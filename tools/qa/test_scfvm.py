#!/usr/bin/env python3
"""Self-test of tools/qa/scfvm.py.

Usage: test_scfvm.py <script_dir>      (clean unpacked SCF classes, e.g. build/work/script_orig)

Compiles small snippets with tools/reinsert/scfasm.py into synthetic classes (the real engine
classes supply Object, Array, the exception classes, ...) and checks the opcode semantics
documented in docs/qa-scfvm.md. Also lints every method of every class (stack depth, jump
targets, indices): this validates the opcode table against the whole game.
"""
import os
import shutil
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'reinsert'), os.path.join(HERE, '..', 'extract')]
import scf  # noqa: E402
import scfasm  # noqa: E402
import scfvm  # noqa: E402
from scfvm import VString  # noqa: E402

FAILS = []
CHECKS = [0]


def check(name, got, want):
    CHECKS[0] += 1
    ok = got == want if not isinstance(want, float) else abs(got - want) < 1e-6
    if not ok:
        FAILS.append(name)
        print(f'FAIL {name}: got {got!r}, want {want!r}')
    return ok


SNIPPETS = {}      # name -> (asm text, argc)


def snip(name, text, argc=0):
    SNIPPETS[name] = (text, argc)


def binop(a, op, b):
    return f'{a}\n{b}\nop {op}\nreturn_top\n'


I = lambda n: f'push_int {n}'            # noqa: E731
F = lambda x: f'push_const float:{x}'    # noqa: E731
K = lambda n: f'push_const int:{n}'      # noqa: E731

# --- arithmetic
snip('div_int', binop(I(7), '/', I(2)))
snip('div_neg', binop(I(-7), '/', I(2)))
snip('mod_neg', binop(I(-7), '%', I(2)))
snip('div_float', binop(F(7.0), '/', I(2)))
snip('mix_add', binop(I(1), '+', F(0.5)))
snip('mix_eq', binop(I(2), '=', F(2.0)))
snip('and_bits', binop(I(6), '&', I(3)))
snip('or_bits', binop(I(6), '|', I(3)))
snip('xor_bits', binop(I(6), '^', I(3)))
snip('lt', binop(I(1), '<', F(1.5)))
snip('ge', binop(F(2.0), '>=', I(2)))
snip('ne', binop(I(1), '<>', I(2)))
snip('wrap32', binop(K(2147483647), '+', I(1)))
snip('neg', f'{I(5)}\nop -U\nreturn_top\n')
snip('inv', f'{I(5)}\nop ~U\nreturn_top\n')
snip('f32', binop(F(0.1), '+', F(0.2)))
snip('divzero', binop(I(1), '/', I(0)))
# --- control flow, locals
snip('loop_sum', '''push_nils 2
push_int 0
store_temp 0
push_int 1
store_temp 1
top:
push_temp 1
push_int 10
op <=
jump_if_false done
push_temp 0
push_temp 1
op +
store_temp 0
push_temp 1
push_int 1
op +
store_temp 1
jump top
done:
push_temp 0
return_top
''')
snip('and_or_not', '''push_true
push_false
and
push_true
push_false
or
op =
not
return_top
''')
snip('identical', '''push_nil
push_nil
identical
push_int 3
push_int 4
not_identical
and
return_top
''')
snip('dup', '''push_int 4
dup
op *
return_top
''')
snip('arg_temp', '''push_nils 1
push_temp 0
push_temp 1
op +
store_temp 2
push_temp 2
return_top
''', argc=2)
snip('ivar', '''push_int 41
store_ivar 0
push_ivar 0
push_int 1
op +
return_top
''')
snip('classvar', '''push_int 9
store_classvar class:T 0
push_classvar class:T 0
push_int 1
op +
return_top
''')
# --- sends
snip('val', 'push_int 1\nreturn_top\n')
snip('send_self', 'push_self\nsend 0 #val\npush_int 10\nop +\nreturn_top\n')
snip('send_args', 'push_self\npush_int 3\npush_int 4\nsend 2 #add2\nreturn_top\n')
snip('add2', 'push_temp 0\npush_temp 1\nop -\nreturn_top\n', argc=2)
# --- exceptions
snip('throw_caught', '''try handler
push_const class:IllegalArgument
send 0 #new
throw
end_try
push_int 0
return_top
handler:
push_int 7
return_top
''')
snip('no_throw', '''try handler
end_try
push_int 5
return_top
handler:
push_int 7
return_top
''')
snip('uncaught', 'push_const class:IllegalArgument\nsend 0 #new\nthrow\n')
snip('thrower', 'push_int 99\npush_int 98\npush_const class:IllegalArgument\nsend 0 #new\nthrow\nreturn_self\n')
snip('catch_callee', '''push_nils 1
try handler
push_self
send 0 #thrower
pop
end_try
push_int 0
return_top
handler:
push_exception
push_const class:IllegalArgument
send 1 #isKindOf
jump_if_false other
clear_exception
push_int 1
return_top
other:
push_int 2
return_top
''')
snip('rethrow_outer', '''try h1
try h2
push_self
send 0 #thrower
pop
end_try
h2:
push_exception
throw
h1:
clear_exception
push_int 3
return_top
''')
snip('dnu', 'push_nil\nsend 0 #noSuchThing\nreturn_top\n')
snip('dnu_caught', '''try h
push_int 4
send 0 #noSuchThing
pop
end_try
push_int 0
return_top
h:
push_exception
push_const class:DoesNotUnderstand
send 1 #isKindOf
return_top
''')
# --- arrays, strings, natives
snip('array_rw', '''push_nils 1
push_const class:Array
push_int 3
send 1 #new
store_temp 0
push_temp 0
push_int 1
push_int 42
at_put
pop
push_temp 0
push_int 1
at
push_temp 0
send 0 #length
op +
return_top
''')
snip('array_oob', '''try h
push_const class:Array
push_int 2
send 1 #new
push_int 2
at
pop
end_try
push_int 0
return_top
h:
push_exception
push_const class:ArrayIndexOutOfBoundsException
send 1 #isKindOf
return_top
''')
snip('str_at', 'push_const "abc"\npush_int 1\nat\nreturn_top\n')
snip('str_len_plus', 'push_const "ab"\npush_const "cde"\nop +\nsend 0 #length\nreturn_top\n')
snip('as_char', 'push_const int:0x8140\nsend 0 #asChar\npush_int 0\nat\nreturn_top\n')
snip('to_integer', 'push_const float:-2.75\nsend 0 #toInteger\nreturn_top\n')
snip('to_float', 'push_int 3\nsend 0 #toFloat\nreturn_top\n')
snip('vector', '''push_nils 1
push_const class:Vector
push_int 2
send 1 #new
store_temp 0
push_temp 0
push_int 10
send 1 #put
pop
push_temp 0
push_int 20
send 1 #put
pop
push_temp 0
push_int 30
send 1 #put
pop
push_temp 0
push_int 2
at
push_temp 0
send 0 #length
op +
return_top
''')
snip('is_kind', 'push_int 3\npush_const class:Number\nsend 1 #isKindOf\nreturn_top\n')
# --- stubs
snip('stub_calls', '''push_nils 1
push_const class:FontChar
push_int 7
push_int 0
push_int 1
push_const float:2.0
push_const float:3.0
push_const float:1.0
push_const float:1.0
send 7 #new
store_temp 0
push_temp 0
push_const float:0.5
send 1 #setAlpha
store_temp 0
push_temp 0
send 0 #whatever
pop
push_temp 0
send 0 #destruct
pop
push_const class:Sound
push_int 5
send 1 #playSE
return_top
''')
snip('spin', 'top:\njump top\n')


def build_dir(script_dir):
    tmp = tempfile.mkdtemp(prefix='scfvm_selftest_')
    for f in os.listdir(script_dir):
        if f.endswith('.scf'):
            os.symlink(os.path.join(os.path.abspath(script_dir), f), os.path.join(tmp, f))

    def make(name, sup, with_methods, fields=((0, b'a'), (1, b'b')), fields2=((0, b'cv'),), extra=()):
        consts = []
        methods = []
        for mname, (text, argc) in with_methods.items():
            methods.append((mname.encode(), argc, scfasm.assemble(text, consts)))
        d = {'header': b'\x00\x04', 'names': [name.encode(), sup.encode()], 'fields': list(fields),
             'fields2': list(fields2), 'methods': methods, 'methods2': [], 'constants': consts}
        for fn in extra:
            fn(d)
        open(os.path.join(tmp, name + '.scf'), 'wb').write(scf.serialize(d))
    make('T', 'Object', SNIPPETS)
    # U overrides val and calls super
    make('U', 'T', {'val': ('push_self\nsend_super 0 #val\npush_int 100\nop +\nreturn_top\n', 0)})
    return tmp


def main():
    script_dir = sys.argv[1]
    tmp = build_dir(script_dir)
    try:
        vm = scfvm.VM(tmp, step_limit=10_000)

        def call(name, *args, cls='T'):
            return vm.send(vm.new_object(cls), name, list(args))

        check('int division truncates', call('div_int'), 3)
        check('negative division truncates toward zero', call('div_neg'), -3)
        check('remainder has the dividend sign', call('mod_neg'), -1)
        check('float division', call('div_float'), 3.5)
        check('int + float', call('mix_add'), 1.5)
        check('int = float', call('mix_eq'), True)
        check('&', call('and_bits'), 2)
        check('|', call('or_bits'), 7)
        check('^', call('xor_bits'), 5)
        check('int < float', call('lt'), True)
        check('float >= int', call('ge'), True)
        check('<>', call('ne'), True)
        check('32 bit wrap', call('wrap32'), -2147483648)
        check('-U', call('neg'), -5)
        check('~U', call('inv'), -6)
        check('float32 rounding', call('f32'), struct.unpack('<f', struct.pack('<f', 0.1 + 0.2))[0])
        check('loop', call('loop_sum'), 55)
        check('and/or/not', call('and_or_not'), True)
        check('identical / not_identical', call('identical'), True)
        check('dup', call('dup'), 16)
        check('arguments and locals', call('arg_temp', 3, 4), 7)
        check('ivar', call('ivar'), 42)
        check('classvar', call('classvar'), 10)
        check('class variable by name', vm.get_classvar('T', 'cv'), 9)
        check('self send', call('send_self'), 11)
        check('send with arguments', call('send_args'), -1)
        check('method lookup in subclass + super send', call('send_self', cls='U'), 111)
        check('try/throw/handler', call('throw_caught'), 7)
        check('end_try path', call('no_throw'), 5)
        check('catch across a frame, stack cut back', call('catch_callee'), 1)
        check('rethrow to an outer handler', call('rethrow_outer'), 3)
        check('DoesNotUnderstand is catchable', call('dnu_caught'), True)
        check('Array at/at_put/length', call('array_rw'), 45)
        check('Array index out of range throws', call('array_oob'), True)
        check('String at: gives a code', call('str_at'), ord('b'))
        check('String + String', call('str_len_plus'), 5)
        check('Integer asChar', call('as_char'), 0x8140)
        check('Float toInteger truncates', call('to_integer'), -2)
        check('Integer toFloat', call('to_float'), 3.0)
        check('Vector (real bytecode) grows and reads', call('vector'), 30 + 3)
        check('isKindOf through Integer -> Number', call('is_kind'), True)

        for name, exc in (('uncaught', 'IllegalArgument'), ('divzero', 'DivisionByZeroException'),
                          ('dnu', 'DoesNotUnderstand')):
            try:
                call(name)
                check(f'{name} raises', False, True)
            except scfvm.ScriptError as e:
                check(f'{name} raises {exc}', vm.describe(e.value).split(' ')[0], exc)
        try:
            call('spin')
            check('step limit', False, True)
        except scfvm.StepLimitExceeded:
            check('step limit', True, True)

        vm.log.clear()
        vm.stub_results[('Sound', 'playSE')] = 123
        r = call('stub_calls')
        check('stub class-side result override', r, 123)
        log = [tuple(c) for c in vm.log]
        check('stub log', log, [
            ('FontChar', 'new', (7, 0, 1, 2.0, 3.0, 1.0, 1.0)), ('FontChar', 'setAlpha', (0.5,)),
            ('FontChar', 'whatever', ()), ('FontChar', 'destruct', ()), ('Sound', 'playSE', (5,))])
        check('destructed stub dropped from live_log', [c[1] for c in vm.live_log()], ['playSE'])

        # lint catches a stack imbalance and a bad jump
        bad = {'pushes': ('push_int 1\npush_int 2\nreturn_top\njump x\nx:\nreturn_self\n', 0)}
        ok = {'fine': ('push_int 1\nreturn_top\n', 0)}
        d = scfvm.ClassDef(vm, 'T', vm.classdef('T').data)
        d.methods = {('fine', 0): scfvm.Method('fine', 0, scfasm.assemble(ok['fine'][0], [])),
                     ('imbalance', 0): scfvm.Method('imbalance', 0, scfasm.assemble(
                         'push_true\njump_if_false a\npush_int 1\na:\npush_int 2\nreturn_top\n', []))}
        check('lint clean method', scfvm.lint_method(d, d.methods[('fine', 0)]), [])
        check('lint finds depth mismatch', len(scfvm.lint_method(d, d.methods[('imbalance', 0)])), 1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # every method of every class: stack depth, jump targets, indices (validates the opcode table)
    vm2 = scfvm.VM(script_dir)
    n = 0
    probs = []
    for name in sorted(vm2._files):
        cd = vm2.classdef(name)
        for side, tbl in (('i', cd.methods), ('c', cd.methods2)):
            for m in tbl.values():
                n += 1
                probs += scfvm.lint_method(cd, m, class_side=(side == 'c'))
    check(f'lint of all {n} methods ({len(probs)} problems)', len(probs), 0)
    for p in probs[:10]:
        print('  ', p)

    print(f'{CHECKS[0]} checks')
    print('FAIL' if FAILS else 'PASS')
    sys.exit(1 if FAILS else 0)


if __name__ == '__main__':
    main()
