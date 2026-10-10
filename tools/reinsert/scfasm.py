#!/usr/bin/env python3
"""Assemble SCF method bytecode from a text listing.

Syntax, one instruction per line (`;` starts a comment, `name:` is a label):

  push_ivar 32            push_temp 0        push_int -3
  push_const "text"       push_const #sym    push_const class:FontChar
  push_const en:"Easy Mode"   (English: D-012 codes 0x8540.., as in translated text)
  push_const int:256      push_const float:2.0   push_const idx:12
  push_classvar class:Parson 7
  send 1 #put             send_super 0 #initialize
  jump loop               jump_if_false done
  op +                    (binary operators, see BINOPS)
  primitive 6

Constants are looked up in the class's constant pool and appended when
missing. The short or long form of each opcode is picked automatically:
u8 constant indices when < 256, s16 jumps always (simple and safe). A `00`
pad is inserted before `send` with a u16 selector index when its operand
would land on an odd offset; the VM reads that operand with a halfword
load, and the original compiler pads the same way.

The `.s`/`.l`/`.w` suffixes (`jump.s`, `send.w`, `push_const.w`, ...)
force a form; the disassembler round trip uses them.
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'extract'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scfdis  # noqa: E402
import en_text  # noqa: E402

BY_NAME = {}
for code, (name, spec) in scfdis.OPS.items():
    BY_NAME.setdefault(name, []).append((code, spec))

FIXED = {  # mnemonic -> opcode for operand-free or fixed-operand instructions
    name: forms[0] for name, forms in BY_NAME.items() if len(forms) == 1
}


class Pool:
    """Constant pool of one class; appends new constants on demand."""

    def __init__(self, constants):
        self.constants = constants

    def index(self, const):
        for i, c in enumerate(self.constants):
            if c == const:
                return i
        self.constants.append(const)
        return len(self.constants) - 1

    def parse(self, tok):
        if tok.startswith('idx:'):
            return int(tok[4:], 0)
        if tok.startswith('"'):
            return self.index((5, tok[1:-1].encode('cp932')))
        if tok.startswith('en:"'):
            return self.index((5, en_text.encode_translation(tok[4:-1])))
        if tok.startswith('#'):
            return self.index((7, tok[1:].encode('ascii')))
        if tok.startswith('class:'):
            return self.index((6, tok[6:].encode('ascii')))
        if tok.startswith('int:'):
            return self.index((1, struct.pack('<i', int(tok[4:], 0))))
        if tok.startswith('float:'):
            return self.index((3, struct.pack('<f', float(tok[6:]))))
        raise ValueError(f'bad constant operand {tok!r}')


def tokenize(line):
    line = re.sub(r'\s*;(?=(?:[^"]*"[^"]*")*[^"]*$).*', '', line)  # comment outside quotes
    return [t for t in re.findall(r'(?:en:)?"[^"]*"|[^\s,]+', line)]


def assemble(text, constants):
    """Return bytecode for one method. `constants` is extended in place."""
    pool = Pool(constants)
    items, labels = [], {}
    for raw in text.splitlines():
        toks = tokenize(raw)
        while toks and toks[0].endswith(':') and not toks[0].startswith(('class:', 'int:', 'float:', 'idx:')):
            labels[toks.pop(0)[:-1]] = len(items)
        if toks:
            items.append(toks)

    # Encode each item; jumps are resolved in a fixed-size second pass.
    def encode(toks, pc, addrs):
        mnem, args = toks[0], toks[1:]
        force = None
        if '.' in mnem:
            mnem, force = mnem.split('.')
        if mnem == 'op':
            return bytes([0x10 + scfdis.BINOPS.index(args[0])])
        if mnem in ('jump', 'jump_if_false'):
            short = force == 's'
            code = {'jump': 0x40, 'jump_if_false': 0x44}[mnem] + (0 if short else 1)
            tgt = addrs[labels[args[0]]] if addrs else pc
            off = tgt - pc
            return bytes([code]) + (struct.pack('<b', off) if short else struct.pack('<h', off))
        if mnem in ('send', 'send_super'):
            argc, sel = int(args[0], 0), pool.parse(args[1])
            wide = force == 'w' or (force is None and sel > 0xFF)
            base = 0x30 if mnem == 'send' else 0x31
            if wide:
                pad = b'\x00' if (pc + 2) % 2 else b''
                return pad + bytes([base + 2, argc]) + struct.pack('<H', sel)
            return bytes([base, argc, sel])
        if mnem == 'push_const':
            i = pool.parse(args[0])
            if force == 'w' or (force is None and i > 0xFF):
                return b'\x51' + struct.pack('<H', i)
            return bytes([0x50, i])
        if mnem in ('push_classvar', 'store_classvar'):
            i, slot = pool.parse(args[0]), int(args[1], 0)
            base = 0x08 if mnem == 'push_classvar' else 0x0A
            if force == 'w' or (force is None and i > 0xFF):
                return bytes([base + 1]) + struct.pack('<H', i) + bytes([slot])
            return bytes([base, i, slot])
        if mnem == 'try':
            tgt = addrs[labels[args[0]]] if addrs else pc
            return b'\x69' + struct.pack('<h', tgt - pc)
        if mnem == 'pad':
            return b'\x00'
        code, spec = FIXED[mnem]
        out = bytes([code])
        for k, a in zip(spec, args):
            v = int(a, 0)
            out += struct.pack({'b': '<B', 's': '<b', 'h': '<H'}[k], v)
        return out

    addrs = None
    for _ in range(3):  # sizes are independent of label values, so this converges at once
        pc, new = 0, []
        for toks in items:
            new.append(pc)
            pc += len(encode(toks, pc, addrs))
        addrs = new
    out = bytearray()
    for toks, at in zip(items, addrs):
        out += encode(toks, at, addrs)
    return bytes(out)


def listing(code, constants):
    """Disassemble to assembler syntax with forced forms (for round trips)."""
    lines, targets, pc, decoded = [], set(), 0, []
    while pc < len(code):
        op = code[pc]
        name, spec = scfdis.OPS[op]
        p, args = pc + 1, []
        for k in spec:
            n = 2 if k in 'JCh' else 1
            raw = code[p:p + n]
            p += n
            if k == 'j':
                args.append(pc + struct.unpack('<b', raw)[0])
            elif k == 'J':
                args.append(pc + struct.unpack('<h', raw)[0])
            elif k == 's':
                args.append(struct.unpack('<b', raw)[0])
            else:
                args.append(int.from_bytes(raw, 'little'))
        if k_jump := [a for k, a in zip(spec, args) if k in 'jJ']:
            targets.update(k_jump)
        decoded.append((pc, op, name, spec, args))
        pc = p
    for at, op, name, spec, args in decoded:
        lab = f'L{at:04x}: ' if at in targets else ''
        if op == 0x00:
            continue  # pads are regenerated by the assembler
        if name.startswith('op '):
            lines.append(f'{lab}{name}')
        elif op in (0x40, 0x41, 0x44, 0x45):
            lines.append(f'{lab}{name}.{"s" if op in (0x40, 0x44) else "l"} L{args[0]:04x}')
        elif op == 0x69:
            lines.append(f'{lab}try L{args[0]:04x}')
        elif op in (0x30, 0x31, 0x32, 0x33):
            lines.append(f'{lab}{name}.{"w" if op & 2 else "b"} {args[0]} idx:{args[1]}')
        elif op in (0x50, 0x51):
            lines.append(f'{lab}push_const.{"w" if op == 0x51 else "b"} idx:{args[0]}')
        elif op in (0x08, 0x09, 0x0A, 0x0B):
            lines.append(f'{lab}{name}.{"w" if op & 1 else "b"} idx:{args[0]} {args[1]}')
        else:
            lines.append(f'{lab}{name} {" ".join(map(str, args))}'.rstrip())
    return '\n'.join(lines)
