#!/usr/bin/env python3
"""Offline interpreter for SCF script bytecode (the engine's Smalltalk-like VM).

Library for regression tests of bytecode patches. It loads a directory of
unpacked `.scf` classes (never game data in the repo: point it at
build/work/script_orig or a patched copy) and executes the real bytecode of
every script class. Only the engine's native side is replaced by Python:

  * native value classes (nil, booleans, Integer, Float, String, Array,
    Symbol, Class, Object's reflection methods), see NATIVES below;
  * stub classes (FontChar, FontCharEx, Sprite, DialogBox, Sound, ...): their
    bytecode is never run. Every call to one is appended to `vm.log` as
    `Call(class, selector, args)` and answered with a configurable default.

See docs/qa-scfvm.md for the model, the assumptions and how to write a
scenario. Opcode semantics follow docs/formats/scf.md.

    vm = VM('build/work/script_orig')
    tw = vm.new_object('TextWindow', posX=-293.0, ...)   # ivars by name
    vm.send(tw, 'putChar', [0x82A0])
    print(vm.log)
"""
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', 'extract'), os.path.join(HERE, '..', 'font')]
import scf  # noqa: E402
import scfdis  # noqa: E402

try:
    import encoding as _en  # noqa: E402
except ImportError:  # pragma: no cover
    _en = None

# Classes whose bytecode is never run: calls are logged and answered by default.
DEFAULT_STUBS = frozenset({
    'FontChar', 'FontCharEx', 'Sprite', 'DialogBox', 'Sound', 'ButtonGuide', 'Thread',
    'System', 'ControlPad', 'WadaiParam', 'WadaiIcon', 'WadaiCursor',
})
SELF = object()  # stub default: answer the receiver

BINOPS = ['+', '-', '*', '/', '%', '&', '|', '^', '=', '>', '<', '>=', '<=', '<>', '-U', '~U']


# --------------------------------------------------------------------------- errors

class VMError(Exception):
    """The script did something the real VM would not survive (or an unsupported feature)."""


class StepLimitExceeded(VMError):
    pass


class ScriptThrow(Exception):
    """A script `throw` travelling up the Python stack until a `try` handler takes it."""

    def __init__(self, value):
        super().__init__(value)
        self.value = value


class ScriptError(VMError):
    """A script exception nobody caught (raised out of VM.send). `.trace` lists the script frames."""

    def __init__(self, vm, value, trace=()):
        self.value = value
        self.trace = list(trace)
        super().__init__('uncaught script exception ' + vm.describe(value)
                         + (' at ' + ' <- '.join(self.trace[:6]) if self.trace else ''))


# --------------------------------------------------------------------------- values
# nil = None, true/false = True/False, small and boxed integers = int (32 bit),
# floats = float (rounded to float32), everything else is one of these objects.

class VString:
    """String: a list of 16-bit character codes (Shift-JIS lead<<8|trail, ASCII as-is)."""

    def __init__(self, codes=()):
        self.codes = list(codes)

    def __eq__(self, o):
        return isinstance(o, VString) and self.codes == o.codes

    def __hash__(self):
        return hash(tuple(self.codes))

    def text(self):
        out = []
        for c in self.codes:
            ch = _en.char_of(c) if _en and c >= 0x8540 else None
            if ch is not None:
                out.append(ch)
            elif c < 0x100:
                out.append(chr(c) if 32 <= c < 127 else f'\\x{c:02x}')
            else:
                try:
                    out.append(bytes([c >> 8, c & 0xFF]).decode('cp932'))
                except UnicodeDecodeError:
                    out.append(f'\\u{{{c:04x}}}')
        return ''.join(out)

    def __repr__(self):
        return f'str{self.text()!r}'


class VArray:
    def __init__(self, items=()):
        self.items = list(items)

    def __eq__(self, o):
        return isinstance(o, VArray) and self.items == o.items

    __hash__ = None

    def __repr__(self):
        return f'array{self.items!r}'


class VSymbol:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '#' + self.name


class VClass:
    """A class used as a value (receiver of `new`, class-side methods, constants)."""

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'class {self.name}'


class VObject:
    """Instance of a script class. `iv` maps instance-variable id -> value."""

    def __init__(self, cdef):
        self.cdef = cdef
        self.iv = {}

    def __repr__(self):
        return f'<{self.cdef.name}>'


class VStub:
    """Instance of a stub class. Remembers what it was created with."""

    def __init__(self, cname, serial, ctor_args):
        self.cname = cname
        self.serial = serial
        self.ctor_args = ctor_args

    def __repr__(self):
        return f'<stub {self.cname}#{self.serial}>'


class Ref:
    """Snapshot of an object inside a logged argument. Equal when the class name is."""

    def __init__(self, name):
        self.name = name

    def __eq__(self, o):
        return isinstance(o, Ref) and self.name == o.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f'<{self.name}>'


class Call(tuple):
    """One logged stub call: compares and unpacks as (class, selector, args).

    `.recv` is the serial of the stub instance that received it (0 for class-side
    calls); for a `new` it is the serial of the object created.
    """

    def __new__(cls, cname, sel, args, recv=0):
        self = super().__new__(cls, (cname, sel, args))
        self.recv = recv
        return self

    def __repr__(self):
        a = ', '.join(repr(x) for x in self[2])
        return f'{self[0]}.{self[1]}({a})' + (f' #{self.recv}' if self.recv else '')


def snap(v):
    """Immutable-ish copy of a value for the call log."""
    if v is None or isinstance(v, (bool, int, float, VSymbol, Ref)):
        return v
    if isinstance(v, VString):
        return VString(v.codes)
    if isinstance(v, VArray):
        return VArray([snap(x) for x in v.items])
    if isinstance(v, VObject) and v.cdef.name == 'Vector':
        arr = v.iv.get(1)
        n = v.iv.get(0)
        if isinstance(arr, VArray) and isinstance(n, int):
            return VArray([snap(x) for x in arr.items[:n]])
    if isinstance(v, VObject):
        return Ref(v.cdef.name)
    if isinstance(v, VStub):
        return Ref(v.cname)
    if isinstance(v, VClass):
        return Ref('class ' + v.name)
    return Ref(type(v).__name__)


def values_equal(a, b, tol=0.0):
    """Structural equality; numbers within `tol` (only when a float is involved)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    na = isinstance(a, (int, float))
    nb = isinstance(b, (int, float))
    if na or nb:
        if not (na and nb):
            return False
        if isinstance(a, int) and isinstance(b, int):
            return a == b
        return abs(a - b) <= tol
    if isinstance(a, VArray) and isinstance(b, VArray):
        return len(a.items) == len(b.items) and all(values_equal(x, y, tol) for x, y in zip(a.items, b.items))
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        return len(a) == len(b) and all(values_equal(x, y, tol) for x, y in zip(a, b))
    return a == b


def compare_logs(a, b, tol=0.0):
    """None if two call logs match (floats within tol), else a description of the first difference."""
    for i, (x, y) in enumerate(zip(a, b)):
        if x[0] != y[0] or x[1] != y[1] or not values_equal(x[2], y[2], tol):
            return f'call #{i}: {x!r}  !=  {y!r}'
    if len(a) != len(b):
        longer = a if len(a) > len(b) else b
        return f'log length {len(a)} vs {len(b)}; first extra: {longer[min(len(a), len(b))]!r}'
    return None


def max_float_delta(a, b):
    """Largest |difference| between corresponding numeric arguments of two matching logs."""
    worst = 0.0

    def walk(x, y):
        nonlocal worst
        if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
            worst = max(worst, abs(x - y))
        elif isinstance(x, (tuple, list)) and isinstance(y, (tuple, list)):
            for p, q in zip(x, y):
                walk(p, q)
        elif isinstance(x, VArray) and isinstance(y, VArray):
            walk(x.items, y.items)
    for x, y in zip(a, b):
        walk(x[2], y[2])
    return worst


# --------------------------------------------------------------------------- text helpers

def sjis_codes(data):
    """Shift-JIS bytes -> 16-bit codes: double-byte as lead<<8|trail, anything else as the byte."""
    out, i = [], 0
    while i < len(data):
        b = data[i]
        if (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC) and i + 1 < len(data):
            out.append(b << 8 | data[i + 1])
            i += 2
        else:
            out.append(b)
            i += 1
    return out


def text_codes(text, english=True):
    """Unicode text -> character codes the way the reinserter encodes it.

    `{...}` is a control-code token and contributes its ASCII bytes as single codes.
    Printable ASCII becomes the D-012 English code (0x8540..0x859F) when `english`,
    otherwise stays a single-byte code. `\\n` is code 10; everything else is cp932.
    """
    out, i = [], 0
    while i < len(text):
        ch = text[i]
        if ch == '{' and '}' in text[i:]:
            j = text.index('}', i)
            out += list(text[i + 1:j].encode('ascii'))
            i = j + 1
            continue
        i += 1
        if ch == '\n':
            out.append(10)
        elif ' ' <= ch <= '~':
            out.append(_en.code_of(ch) if english else ord(ch))
        else:
            out += sjis_codes(ch.encode('cp932'))
    return out


def f32(x):
    try:
        return struct.unpack('<f', struct.pack('<f', x))[0]
    except OverflowError:
        return math.copysign(math.inf, x)


def wrap32(x):
    x &= 0xFFFFFFFF
    return x - (1 << 32) if x & 0x80000000 else x


# --------------------------------------------------------------------------- decoding

def decode(code):
    """Bytecode -> {pc: (op, operands, next_pc)}. Jump operands are absolute targets."""
    out, pc, n = {}, 0, len(code)
    while pc < n:
        op = code[pc]
        ent = scfdis.OPS.get(op)
        if ent is None:
            out[pc] = (op, (), pc + 1)
            pc += 1
            continue
        p, args = pc + 1, []
        for k in ent[1]:
            if k in 'bc':
                args.append(code[p])
                p += 1
            elif k == 's':
                args.append(struct.unpack_from('<b', code, p)[0])
                p += 1
            elif k == 'j':
                args.append(pc + struct.unpack_from('<b', code, p)[0])
                p += 1
            elif k == 'J':
                args.append(pc + struct.unpack_from('<h', code, p)[0])
                p += 2
            else:  # 'C' / 'h': u16
                args.append(struct.unpack_from('<H', code, p)[0])
                p += 2
        out[pc] = (op, tuple(args), p)
        pc = p
    return out


def lint_method(cdef, meth, class_side=False):
    """Static checks of one method. Returns a list of problem strings (empty when clean).

    Checks: every opcode is defined; jump and try targets land on instruction starts; wide sends
    sit at even offsets; constant, instance-variable, class-variable and temp indices exist; the
    operand stack depth is the same on every path into an instruction, never negative, and the
    method cannot fall off its end.
    """
    dec, code = meth.dec, meth.code
    cd = cdef
    nconst = len(cd.data['constants']) if cd.data else 0
    probs = []
    ntemps = meth.argc          # temps: argc plus every push_nils
    for pc, (op, a, nx) in dec.items():
        if op == 0x6C:
            ntemps += a[0]

    def bad(pc, msg):
        probs.append(f'{cd.name}>>{meth.name}/{meth.argc} @{pc:04x}: {msg}')

    todo = [(0, 0)]
    depth_at = {}
    while todo:
        pc, d = todo.pop()
        while True:
            if pc not in dec:
                bad(pc, 'jump target or fall-through is not an instruction start')
                break
            if pc in depth_at:
                if depth_at[pc] != d:
                    bad(pc, f'stack depth {d} on one path, {depth_at[pc]} on another')
                break
            depth_at[pc] = d
            op, a, nx = dec[pc]
            ent = scfdis.OPS.get(op)
            if ent is None:
                bad(pc, f'undefined opcode {op:#04x}')
                break
            if op in (0x32, 0x33) and pc % 2:
                bad(pc, 'wide send at an odd offset (its u16 selector would be misaligned)')
            if op in (0x08, 0x09, 0x0A, 0x0B, 0x30, 0x31, 0x32, 0x33, 0x50, 0x51):
                ci = a[0] if op in (0x08, 0x09, 0x0A, 0x0B, 0x50, 0x51) else a[1]
                if ci >= nconst:
                    bad(pc, f'constant index {ci} out of range')
                elif op in (0x30, 0x31, 0x32, 0x33) and cd.data['constants'][ci][0] not in (6, 7):
                    bad(pc, f'selector constant {ci} is not a symbol')
                elif op in (0x08, 0x09, 0x0A, 0x0B):
                    if cd.data['constants'][ci][0] != 6:
                        bad(pc, f'class-variable class constant {ci} is not a class')
                    else:
                        tgt = cd.data['constants'][ci][1].decode('cp932')
                        if cd.vm.has_class(tgt) and a[1] not in cd.vm.classdef(tgt).fields2:
                            bad(pc, f'{tgt} has no class variable {a[1]}')
            if op in (0x20, 0x21) and not cd.has_ivar_id(a[0]) and not class_side:
                bad(pc, f'instance variable {a[0]} not declared in {cd.name} or its superclasses')
            if op in (0x22, 0x23) and a[0] >= ntemps:
                bad(pc, f'temp {a[0]} but the method has {ntemps} (argc + push_nils)')
            eff = _stack_effect(op, a)
            d2 = d + eff
            if d2 < 0 or (op == 0x03 and d < 1):
                bad(pc, 'operand stack underflow')
                break
            if op in (0x02, 0x03, 0x34, 0x6B):
                break
            if op in (0x40, 0x41):
                pc = a[0]
                d = d2
                continue
            if op in (0x44, 0x45):
                todo.append((a[0], d2))
            if op == 0x69:
                todo.append((a[0], d))      # the handler runs with the stack cut back to the try depth
            pc, d = nx, d2
            if pc >= len(code):
                bad(pc, 'falls off the end of the method')
                break
    return probs


def _stack_effect(op, a):
    if op in (0x08, 0x09, 0x20, 0x22, 0x24, 0x25, 0x26, 0x28, 0x29, 0x2A, 0x50, 0x51, 0x04):
        return 1
    if op in (0x05, 0x0A, 0x0B, 0x21, 0x23, 0x44, 0x45, 0x64, 0x6B) or 0x06 <= op <= 0x07 or 0x0C <= op <= 0x0D \
            or 0x10 <= op <= 0x1D:
        return -1
    if op in (0x30, 0x31, 0x32, 0x33):
        return -a[0]
    if op == 0x65:
        return -2
    return 0


class Method:
    def __init__(self, name, argc, code):
        self.name, self.argc, self.code = name, argc, code
        self._dec = None

    @property
    def dec(self):
        if self._dec is None:
            self._dec = decode(self.code)
        return self._dec


class ClassDef:
    def __init__(self, vm, name, data):
        self.vm = vm
        self.name = name
        self.data = data
        self.super_name = data['names'][1].decode('cp932') if data else ''
        self.fields = {i: n.decode('cp932') for i, n in data['fields']} if data else {}
        self.fields2 = {i: n.decode('cp932') for i, n in data['fields2']} if data else {}
        self.methods, self.methods2 = {}, {}
        for tbl, dst in (('methods', self.methods), ('methods2', self.methods2)):
            for n, a, c in (data[tbl] if data else []):
                dst[(n.decode('cp932'), a)] = Method(n.decode('cp932'), a, c)
        self._consts = None
        self._super = False
        self._ivar_ids = None
        self._ivar_idset = None

    @property
    def super(self):
        if self._super is False:
            self._super = self.vm.classdef(self.super_name) if self.super_name and self.super_name != 'nil' else None
        return self._super

    def chain(self):
        c = self
        while c is not None:
            yield c
            c = c.super

    @property
    def ivar_ids(self):
        """name -> id over the whole superclass chain (subclasses redeclare parent fields)."""
        if self._ivar_ids is None:
            ids = {}
            for c in reversed(list(self.chain())):
                ids.update({n: i for i, n in c.fields.items()})
            self._ivar_ids = ids
        return self._ivar_ids

    def has_ivar_id(self, i):
        if self._ivar_idset is None:
            self._ivar_idset = set(self.ivar_ids.values())
        return i in self._ivar_idset

    @property
    def consts(self):
        if self._consts is None:
            self._consts = [self.vm.convert_const(c) for c in (self.data['constants'] if self.data else [])]
        return self._consts

    def is_kind_of(self, name):
        return any(c.name == name for c in self.chain())


# --------------------------------------------------------------------------- the VM

class VM:
    def __init__(self, script_dir, stubs=DEFAULT_STUBS, step_limit=5_000_000, float32=True,
                 max_depth=150):
        self.script_dir = script_dir
        self.stubs = set(stubs)
        self.step_limit = step_limit
        self.float32 = float32
        self.max_depth = max_depth
        self.steps = 0
        self.depth = 0
        self.log = []
        self.destructed = set()
        self.stub_default = SELF
        self.stub_results = {}      # (class, selector) -> value | callable(vm, recv, args)
        self.warnings = []
        self._defs = {}
        self._classvars = {}
        self._symbols = {}
        self._classes = {}
        self._serial = 0
        self.cur_exc = None
        self._top = False
        self._files = {f[:-4] for f in os.listdir(script_dir) if f.endswith('.scf')}
        sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))

    # ---- loading --------------------------------------------------------
    def has_class(self, name):
        return name in self._files or name in self._defs

    def classdef(self, name):
        cd = self._defs.get(name)
        if cd is None:
            if name in self._files:
                data = scf.parse(open(os.path.join(self.script_dir, name + '.scf'), 'rb').read())
                got = data['names'][0].decode('cp932')
                if got != name:
                    raise VMError(f'{name}.scf holds class {got}')
                cd = ClassDef(self, name, data)
            elif name in self.stubs:
                cd = ClassDef(self, name, None)   # stub without a class file
            else:
                raise VMError(f'no class {name!r} in {self.script_dir}')
            self._defs[name] = cd
        return cd

    def vclass(self, name):
        c = self._classes.get(name)
        if c is None:
            c = self._classes[name] = VClass(name)
        return c

    def symbol(self, name):
        s = self._symbols.get(name)
        if s is None:
            s = self._symbols[name] = VSymbol(name)
        return s

    def convert_const(self, c):
        t, p = c
        if t == 0:
            return None
        if t == 2:
            return False
        if t == 4:
            return True
        if t == 1:
            return struct.unpack('<i', p)[0]
        if t == 3:
            return struct.unpack('<f', p)[0]
        if t == 5:
            return VString(sjis_codes(p))
        if t == 6:
            return self.vclass(p.decode('cp932'))
        if t == 7:
            return self.symbol(p.decode('cp932'))
        if t == 8:
            return VArray([self.convert_const(x) for x in p])
        raise VMError(f'unknown constant type {t}')

    def is_stub(self, cname):
        if cname in self.stubs:
            return True
        if not self.has_class(cname):
            return False
        return any(c.name in self.stubs for c in self.classdef(cname).chain())

    # ---- convenience for scenarios -------------------------------------
    def string(self, x, english=True):
        if isinstance(x, VString):
            return x
        if isinstance(x, str):
            return VString(text_codes(x, english))
        if isinstance(x, (bytes, bytearray)):
            return VString(sjis_codes(x))
        return VString(x)

    def wrap(self, x):
        """Python -> VM value for top-level arguments: str -> String, list -> Array."""
        if isinstance(x, str):
            return self.string(x)
        if isinstance(x, (list, tuple)):
            return VArray([self.wrap(y) for y in x])
        return x

    def new_object(self, cname, **ivars):
        """Allocate an instance WITHOUT running initialize; set instance variables by name."""
        cd = self.classdef(cname)
        if self.is_stub(cname):
            return self._new_stub(cname, ())
        o = VObject(cd)
        for k, v in ivars.items():
            self.set_ivar(o, k, v)
        return o

    def new(self, cname, *args):
        """`Class new: args...` (allocates and runs initialize with those arguments)."""
        return self.send(self.vclass(cname), 'new', args)

    def set_ivar(self, obj, name, value):
        obj.iv[obj.cdef.ivar_ids[name]] = self.wrap(value)

    def get_ivar(self, obj, name):
        return obj.iv.get(obj.cdef.ivar_ids[name])

    def ivars(self, obj):
        return {n: obj.iv.get(i) for n, i in sorted(obj.cdef.ivar_ids.items(), key=lambda kv: kv[1])}

    def set_classvar(self, cname, name, value):
        ids = {n: i for i, n in self.classdef(cname).fields2.items()}
        self._classvars[(cname, ids[name])] = self.wrap(value)

    def get_classvar(self, cname, name):
        ids = {n: i for i, n in self.classdef(cname).fields2.items()}
        return self._classvars.get((cname, ids[name]))

    def live_log(self):
        """The call log without every call that involves a stub instance that was destructed."""
        return [c for c in self.log if not (c.recv and c.recv in self.destructed)]

    def describe(self, v):
        if isinstance(v, VObject):
            d = v.cdef.name
            info = getattr(v, 'info', None)
            if info:
                d += f' ({info})'
            for nm in ('message', 'mess', 'msg'):
                if nm in v.cdef.ivar_ids and v.iv.get(v.cdef.ivar_ids[nm]) is not None:
                    d += f' {v.iv[v.cdef.ivar_ids[nm]]!r}'
            return d
        return repr(v)

    # ---- top-level send --------------------------------------------------
    def send(self, receiver, selector, args=()):
        """Send `selector` (no colons, e.g. 'putChar', 'setPos') with `args` to `receiver`.

        The step counter restarts at every top-level send. An uncaught script exception
        raises ScriptError; VM-level problems raise VMError (StepLimitExceeded for loops).
        """
        if self._top:                    # called from a stub_results callback: share the running state
            return self.dispatch(self.wrap(receiver), selector, [self.wrap(a) for a in args])
        self.steps = 0
        self.depth = 0
        self.cur_exc = None
        self._top = True
        try:
            return self.dispatch(self.wrap(receiver), selector, [self.wrap(a) for a in args])
        except ScriptThrow as t:
            raise ScriptError(self, t.value, getattr(t, 'trace', ())) from None
        finally:
            self._top = False

    # ---- stubs -----------------------------------------------------------
    def _new_stub(self, cname, args):
        self._serial += 1
        o = VStub(cname, self._serial, tuple(snap(a) for a in args))
        self.log.append(Call(cname, 'new', o.ctor_args, o.serial))
        return o

    def _stub_call(self, cname, sel, args, recv):
        serial = recv.serial if isinstance(recv, VStub) else 0
        self.log.append(Call(cname, sel, tuple(snap(a) for a in args), serial))
        if sel == 'destruct' and serial:
            self.destructed.add(serial)
        for key in ((cname, sel, len(args)), (cname, sel), (None, sel)):
            if key in self.stub_results:
                r = self.stub_results[key]
                return r(self, recv, args) if callable(r) else r
        return recv if self.stub_default is SELF else self.stub_default

    # ---- lookup ------------------------------------------------------------
    def class_of(self, v):
        if v is None:
            return self.classdef('Nil')
        if v is True:
            return self.classdef('True')
        if v is False:
            return self.classdef('False')
        if isinstance(v, int):
            return self.classdef('Integer')
        if isinstance(v, float):
            return self.classdef('Float')
        if isinstance(v, VString):
            return self.classdef('String')
        if isinstance(v, VArray):
            return self.classdef('Array')
        if isinstance(v, VSymbol):
            return self.classdef('Symbol')
        if isinstance(v, VClass):
            return self.classdef('Class')
        if isinstance(v, VObject):
            return v.cdef
        if isinstance(v, VStub):
            return self.classdef(v.cname)
        raise VMError(f'not a VM value: {v!r}')

    def lookup(self, cdef, side, sel, argc):
        c = cdef
        while c is not None:
            nat = NATIVES.get((c.name, side, sel, argc))
            if nat is not None:
                return ('n', c, nat)
            m = (c.methods if side == 'i' else c.methods2).get((sel, argc))
            if m is not None:
                return ('s', c, m)
            c = c.super
        if side == 'c':
            return self.lookup(self.classdef('Class'), 'i', sel, argc)
        return None

    def dispatch(self, recv, sel, args, sup=None, sup_side=None):
        """Send a message. `sup` is the class whose superclass starts the search (super sends)."""
        argc = len(args)
        if sup is not None:
            side = sup_side
            start = sup.super
            if start is None:
                found = None
            else:
                found = self.lookup(start, side, sel, argc)
        elif isinstance(recv, VStub):
            return self._stub_call(recv.cname, sel, args, recv)
        elif isinstance(recv, VClass):
            if self.is_stub(recv.name):
                if sel == 'new':
                    return self._new_stub(recv.name, args)
                return self._stub_call(recv.name, sel, args, recv)
            side = 'c'
            found = self.lookup(self.classdef(recv.name), 'c', sel, argc)
        else:
            side = 'i'
            found = self.lookup(self.class_of(recv), 'i', sel, argc)
        if found is None:
            return self.throw_new('DoesNotUnderstand', info=f'{self.class_of(recv).name}>>{sel}/{argc}'
                                  if not isinstance(recv, VClass) else f'class {recv.name}>>{sel}/{argc}')
        kind, owner, ent = found
        if kind == 'n':
            return ent(self, recv, args)
        return self.run_method(recv, owner, side == 'c', ent, args)

    def throw_new(self, cname, *ctor, info=None):
        exc = self.send_internal_new(cname, ctor)
        if info is not None:
            exc.info = info
        raise ScriptThrow(exc)

    def send_internal_new(self, cname, args):
        saved = self.cur_exc
        r = self.dispatch(self.vclass(cname), 'new', list(args))
        self.cur_exc = saved
        return r

    # ---- operators ---------------------------------------------------------
    def _num(self, r):
        return f32(r) if self.float32 else r

    def binop(self, name, a, b):
        isn = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)  # noqa: E731
        if isn(a) and isn(b):
            if isinstance(a, int) and isinstance(b, int):
                if name == '+':
                    return wrap32(a + b)
                if name == '-':
                    return wrap32(a - b)
                if name == '*':
                    return wrap32(a * b)
                if name in ('/', '%'):
                    if b == 0:
                        return self.throw_new('DivisionByZeroException')
                    q = abs(a) // abs(b)
                    if name == '/':
                        return wrap32(-q if (a < 0) != (b < 0) else q)
                    r = abs(a) % abs(b)
                    return -r if a < 0 else r
                if name == '&':
                    return wrap32(a & b)
                if name == '|':
                    return wrap32(a | b)
                if name == '^':
                    return wrap32(a ^ b)
            else:
                if name in ('&', '|', '^'):
                    return self.throw_new('IllegalArgument', info=f'float operand of {name}')
                a, b = float(a), float(b)
                if name == '+':
                    return self._num(a + b)
                if name == '-':
                    return self._num(a - b)
                if name == '*':
                    return self._num(a * b)
                if name == '/':
                    if b == 0.0:
                        return self.throw_new('DivisionByZeroException')
                    return self._num(a / b)
                if name == '%':
                    if b == 0.0:
                        return self.throw_new('DivisionByZeroException')
                    return self._num(math.fmod(a, b))
            if name == '=':
                return a == b
            if name == '<>':
                return a != b
            if name == '>':
                return a > b
            if name == '<':
                return a < b
            if name == '>=':
                return a >= b
            if name == '<=':
                return a <= b
        return self.dispatch(a, name, [b])

    def unop(self, name, a):
        if isinstance(a, (int, float)) and not isinstance(a, bool):
            if name == '-U':
                return wrap32(-a) if isinstance(a, int) else -a
            if isinstance(a, int):
                return wrap32(~a)
        return self.dispatch(a, name, [])

    @staticmethod
    def identical(a, b):
        if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None:
            return a is b
        if isinstance(a, int) and isinstance(b, int):
            return a == b
        if isinstance(a, float) and isinstance(b, float):
            return a == b
        return a is b

    # ---- array access opcodes ---------------------------------------------
    def op_at(self, recv, idx):
        if isinstance(recv, VArray):
            return self._arr_get(recv.items, idx)
        if isinstance(recv, VString):
            return self._arr_get(recv.codes, idx)
        return self.dispatch(recv, '[]', [idx])

    def op_at_put(self, recv, idx, val):
        if isinstance(recv, VArray):
            self._arr_put(recv.items, idx, val)
            return val
        if isinstance(recv, VString):
            self._arr_put(recv.codes, idx, val)
            return val
        self.dispatch(recv, 'atPut', [idx, val])
        return val

    def _arr_get(self, items, idx):
        if not isinstance(idx, int) or isinstance(idx, bool):
            return self.throw_new('IllegalArgument', info='index is not an integer')
        if not 0 <= idx < len(items):
            return self.throw_new('ArrayIndexOutOfBoundsException', info=f'index {idx} of {len(items)}')
        return items[idx]

    def _arr_put(self, items, idx, val):
        if not isinstance(idx, int) or isinstance(idx, bool):
            return self.throw_new('IllegalArgument', info='index is not an integer')
        if not 0 <= idx < len(items):
            return self.throw_new('ArrayIndexOutOfBoundsException', info=f'index {idx} of {len(items)}')
        items[idx] = val

    # ---- the interpreter loop ----------------------------------------------
    def run_method(self, recv, defcls, class_side, meth, args):
        if len(args) != meth.argc:
            raise VMError(f'{defcls.name}>>{meth.name} takes {meth.argc} arguments, got {len(args)}')
        self.depth += 1
        if self.depth > self.max_depth:
            raise VMError(f'call depth {self.max_depth} exceeded in {defcls.name}>>{meth.name}')
        try:
            return self._exec(recv, defcls, class_side, meth, list(args))
        except VMError as e:
            if getattr(e, '_where_set', None) is None:
                e._where_set = True
                e.args = (f'{e.args[0]}  [in {defcls.name}>>{meth.name}/{meth.argc} @{getattr(e, "pc", 0):04x}]',)
            else:
                e.args = (f'{e.args[0]}  <- {defcls.name}>>{meth.name}',)
            raise
        finally:
            self.depth -= 1

    def _exec(self, recv, defcls, class_side, meth, temps):
        code = meth.dec
        consts = defcls.consts
        stack, handlers = [], []
        ncls = recv.cdef if isinstance(recv, VObject) else None
        pc = 0
        limit = self.step_limit
        while True:
            try:
                while True:
                    try:
                        op, a, nxt = code[pc]
                    except KeyError:
                        e = VMError(f'jump into the middle of an instruction or off the end (pc {pc:#x})')
                        e.pc = pc
                        raise e from None
                    self.steps += 1
                    if self.steps > limit:
                        e = StepLimitExceeded(f'step limit {limit} exceeded')
                        e.pc = pc
                        raise e
                    cur = pc
                    pc = nxt
                    if op == 0x22:
                        if a[0] >= len(temps):
                            self._bad(cur, f'push_temp {a[0]} but only {len(temps)} temps')
                        stack.append(temps[a[0]])
                    elif op == 0x20:
                        if ncls is None or not ncls.has_ivar_id(a[0]):
                            self._bad(cur, f'push_ivar {a[0]}: receiver {recv!r} has no such instance variable')
                        stack.append(recv.iv.get(a[0]))
                    elif op == 0x50 or op == 0x51:
                        stack.append(consts[a[0]])
                    elif op == 0x24:
                        stack.append(a[0])
                    elif op == 0x30 or op == 0x32 or op == 0x31 or op == 0x33:
                        argc, ci = a
                        sel = consts[ci].name
                        if argc:
                            sargs = stack[-argc:]
                            del stack[-argc:]
                        else:
                            sargs = []
                        r = stack.pop()
                        if op & 1:
                            stack.append(self.dispatch(r, sel, sargs, sup=defcls, sup_side='c' if class_side else 'i'))
                        else:
                            stack.append(self.dispatch(r, sel, sargs))
                    elif 0x10 <= op <= 0x1D:
                        b = stack.pop()
                        x = stack.pop()
                        stack.append(self.binop(BINOPS[op - 0x10], x, b))
                    elif op == 0x23:
                        if a[0] >= len(temps):
                            self._bad(cur, f'store_temp {a[0]} but only {len(temps)} temps')
                        temps[a[0]] = stack.pop()
                    elif op == 0x21:
                        if ncls is None or not ncls.has_ivar_id(a[0]):
                            self._bad(cur, f'store_ivar {a[0]}: receiver {recv!r} has no such instance variable')
                        recv.iv[a[0]] = stack.pop()
                    elif op == 0x44 or op == 0x45:
                        v = stack.pop()
                        if v is None or v is False:
                            pc = a[0]
                    elif op == 0x40 or op == 0x41:
                        pc = a[0]
                    elif op == 0x05:
                        stack.pop()
                    elif op == 0x04:
                        stack.append(stack[-1])
                    elif op == 0x26:
                        stack.append(recv)
                    elif op == 0x25:
                        stack.append(None)
                    elif op == 0x28:
                        stack.append(True)
                    elif op == 0x29:
                        stack.append(False)
                    elif op == 0x2B:
                        v = stack.pop()
                        stack.append(v is None or v is False)
                    elif op == 0x07:
                        b = stack.pop()
                        stack.append(self.identical(stack.pop(), b))
                    elif op == 0x06:
                        b = stack.pop()
                        stack.append(not self.identical(stack.pop(), b))
                    elif op == 0x0C or op == 0x0D:
                        b = stack.pop()
                        x = stack.pop()
                        tb = not (b is None or b is False)
                        tx = not (x is None or x is False)
                        stack.append((tx and tb) if op == 0x0C else (tx or tb))
                    elif op == 0x64:
                        i = stack.pop()
                        stack.append(self.op_at(stack.pop(), i))
                    elif op == 0x65:
                        v = stack.pop()
                        i = stack.pop()
                        stack.append(self.op_at_put(stack.pop(), i, v))
                    elif op == 0x02:
                        return recv
                    elif op == 0x03:
                        if not stack:
                            self._bad(cur, 'return_top with an empty stack')
                        return stack.pop()
                    elif op == 0x6C:
                        temps.extend([None] * a[0])
                    elif op == 0x08 or op == 0x09:
                        stack.append(self._classvars.get((consts[a[0]].name, a[1])))
                    elif op == 0x0A or op == 0x0B:
                        self._classvars[(consts[a[0]].name, a[1])] = stack.pop()
                    elif op == 0x1E or op == 0x1F:
                        stack.append(self.unop(BINOPS[op - 0x10], stack.pop()))
                    elif op == 0x69:
                        handlers.append((a[0], len(stack)))
                    elif op == 0x6A:
                        if not handlers:
                            self._bad(cur, 'end_try without try')
                        handlers.pop()
                    elif op == 0x6B:
                        raise ScriptThrow(stack.pop())
                    elif op == 0x2A:
                        stack.append(self.cur_exc)
                    elif op == 0x68:
                        self.cur_exc = None
                    elif op == 0x34:
                        return self._primitive(recv, defcls, meth, temps[:meth.argc], class_side)
                    elif op == 0x00 or op == 0x01 or op == 0x6D:
                        pass
                    elif 0x60 <= op <= 0x63:
                        self._bad(cur, f'raise-error opcode {op:#04x}')
                    else:
                        self._bad(cur, f'undefined opcode {op:#04x}')
            except ScriptThrow as t:
                if not hasattr(t, 'trace'):
                    t.trace = []
                t.trace.append(f'{defcls.name}>>{meth.name}/{meth.argc}@{cur:04x}')
                if not handlers:
                    raise
                target, depth = handlers.pop()
                del stack[depth:]
                self.cur_exc = t.value
                pc = target
            except IndexError as ex:
                e = VMError(f'operand stack underflow or Python IndexError ({ex})')
                e.pc = cur
                raise e from ex
            except VMError as e:
                if not hasattr(e, 'pc'):
                    e.pc = cur
                raise

    def _bad(self, pc, msg):
        e = VMError(msg)
        e.pc = pc
        raise e

    def _primitive(self, recv, defcls, meth, args, class_side):
        """`34 n` reached in a class that has no Python native: log it like a stub call."""
        who = defcls.name
        r = self._stub_call(who, meth.name, args, recv)
        self.warnings.append(f'primitive of {who}>>{meth.name}/{meth.argc} answered by the stub default')
        return r


# --------------------------------------------------------------------------- natives
# NATIVES[(class, side, selector, argc)] = fn(vm, receiver, args). side 'i' = instance,
# 'c' = class side. Looked up before script methods at each class of the superclass chain.

NATIVES = {}


def native(cls, side, sel, *argcs):
    def deco(fn):
        for n in argcs:
            NATIVES[(cls, side, sel, n)] = fn
        return fn
    return deco


def _both(sel, argc=0):
    def deco(fn):
        for c in ('Integer', 'Float'):
            NATIVES[(c, 'i', sel, argc)] = fn
        return fn
    return deco


@_both('toFloat')
def _to_float(vm, r, a):
    return vm._num(float(r))


@_both('toInteger')
def _to_integer(vm, r, a):
    return wrap32(int(r))   # truncates toward zero


@_both('asChar')
def _as_char(vm, r, a):
    return VString([int(r)])


# --- Object / Class

@native('Object', 'i', 'getClass', 0)
def _get_class(vm, r, a):
    return vm.vclass(vm.class_of(r).name)


@native('Object', 'i', 'isKindOf', 1)
def _is_kind_of(vm, r, a):
    return isinstance(a[0], VClass) and vm.class_of(r).is_kind_of(a[0].name)


@native('Object', 'i', 'sleep', 1)
def _sleep(vm, r, a):
    return r


@native('Object', 'i', 'perform', 1)
def _perform(vm, r, a):
    return vm.dispatch(r, a[0].name, [])


@native('Object', 'i', 'performWith', 2, 3)
def _perform_with(vm, r, a):
    return vm.dispatch(r, a[0].name, list(a[1:]))


@native('Object', 'i', 'performWithArguments', 2)
def _perform_args(vm, r, a):
    return vm.dispatch(r, a[0].name, list(a[1].items))


@native('Class', 'i', 'name', 0)
def _class_name(vm, r, a):
    return VString(r.name.encode('cp932'))


def _class_new(vm, cls, args):
    cd = vm.classdef(cls.name)
    obj = VObject(cd)
    found = vm.lookup(cd, 'i', 'initialize', len(args))
    if found is None:
        if args:
            return vm.throw_new('DoesNotUnderstand', info=f'{cls.name}>>initialize/{len(args)}')
        return obj
    kind, owner, ent = found
    if kind == 'n':
        ent(vm, obj, args)
    else:
        vm.run_method(obj, owner, False, ent, args)
    return obj


for _n in range(9):
    NATIVES[('Class', 'i', 'new', _n)] = _class_new


@native('Class', 'i', 'newWithArray', 1)
def _new_with_array(vm, cls, a):
    return vm.dispatch(cls, 'new', list(a[0].items))


@native('Class', 'c', 'findClass', 1)
def _find_class(vm, cls, a):
    name = a[0].text() if isinstance(a[0], VString) else getattr(a[0], 'name', '')
    return vm.vclass(name) if vm.has_class(name) else None


# --- String

@native('String', 'c', 'new', 0, 1)
def _string_new(vm, cls, a):
    if a and isinstance(a[0], VString):
        return VString(a[0].codes)
    return VString([0] * a[0] if a else [])


@native('String', 'i', 'length', 0)
def _string_length(vm, r, a):
    return len(r.codes)


@native('String', 'i', '[]', 1)
def _string_at(vm, r, a):
    return vm._arr_get(r.codes, a[0])


@native('String', 'i', 'atPut', 2)
def _string_atput(vm, r, a):
    vm._arr_put(r.codes, a[0], a[1])
    return r


@native('String', 'i', 'put', 1)
def _string_put(vm, r, a):
    if isinstance(a[0], VString):
        r.codes.extend(a[0].codes)
    else:
        r.codes.append(a[0])
    return r


@native('String', 'i', '+', 1)
def _string_plus(vm, r, a):
    if isinstance(a[0], VString):
        return VString(r.codes + a[0].codes)
    if isinstance(a[0], int) and not isinstance(a[0], bool):
        return VString(r.codes + [a[0]])
    return vm.throw_new('IllegalArgument', info='String + non-string')


@native('String', 'i', '=', 1)
def _string_eq(vm, r, a):
    return isinstance(a[0], VString) and r.codes == a[0].codes


@native('String', 'i', '<>', 1)
def _string_ne(vm, r, a):
    return not (isinstance(a[0], VString) and r.codes == a[0].codes)


NATIVES[('String', 'i', 'equals', 1)] = _string_eq


@native('String', 'i', 'clone', 0)
def _string_clone(vm, r, a):
    return VString(r.codes)


@native('String', 'i', 'copyFrom', 1)
def _string_copyfrom(vm, r, a):
    n = min(len(r.codes), len(a[0].codes))
    r.codes[:n] = a[0].codes[:n]
    return r


# --- Array

@native('Array', 'c', 'new', 1)
def _array_new(vm, cls, a):
    if not isinstance(a[0], int) or a[0] < 0:
        return vm.throw_new('IllegalArgument', info='Array size')
    return VArray([None] * a[0])


@native('Array', 'i', 'length', 0)
def _array_length(vm, r, a):
    return len(r.items)


@native('Array', 'i', '[]', 1)
def _array_at(vm, r, a):
    return vm._arr_get(r.items, a[0])


@native('Array', 'i', 'atPut', 2)
def _array_atput(vm, r, a):
    vm._arr_put(r.items, a[0], a[1])
    return r


@native('Array', 'i', 'copyFrom', 1)
def _array_copyfrom(vm, r, a):
    src = a[0].items if isinstance(a[0], VArray) else None
    if src is None:
        return vm.throw_new('IllegalArgument', info='Array copyFrom: non-array')
    n = min(len(r.items), len(src))
    r.items[:n] = src[:n]
    return r


@native('Array', 'i', 'equals', 1)
def _array_equals(vm, r, a):
    return isinstance(a[0], VArray) and len(a[0].items) == len(r.items) and all(
        vm.identical(x, y) for x, y in zip(r.items, a[0].items))


@native('Array', 'i', 'clone', 0)
def _array_clone(vm, r, a):
    return VArray(r.items)


def main():
    """Smoke: `scfvm.py <script_dir> <Class> <selector> [int args...]` sends to a fresh instance."""
    if len(sys.argv) < 4:
        print(__doc__)
        return
    vm = VM(sys.argv[1])
    obj = vm.new(sys.argv[2]) if sys.argv[3] != 'new' else vm.vclass(sys.argv[2])
    print(vm.send(obj, sys.argv[3], [int(x, 0) for x in sys.argv[4:]]))
    for c in vm.log:
        print(c)


if __name__ == '__main__':
    main()
