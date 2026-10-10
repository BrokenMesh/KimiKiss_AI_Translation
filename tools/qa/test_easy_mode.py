#!/usr/bin/env python3
"""Easy mode (D-038): the cheat patches change nothing while their switch is off, and do what they
should when it is on.

Usage: test_easy_mode.py <script_dir>

<script_dir> holds the CLEAN unpacked SCF classes (build/work/script_orig). All patches/scripts/*.asm
are applied to a temp copy. Every case runs the method on the original classes and on the patched
classes with all switches off (results and touched state must be identical), then on the patched
classes with the switch on (checked against what the cheat should do). The switches are bits of
GameParam class variable 18 (autoSkip): 1 No Losses, 2 Fewer Rejections, 4 Easier Meetings, 8 More Tries.
"""
import glob
import itertools
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'reinsert')]
import scfvm  # noqa: E402
from scfvm import VArray  # noqa: E402
import test_patches_jp as tpj  # noqa: E402

FLAG = ('GameParam', 18)
fails = []
count = 0


def vm_for(d, flags):
    vm = scfvm.VM(d)
    vm._classvars[FLAG] = flags
    return vm


def count_case():
    global count
    count += 1


def check(label, run, orig_dir, new_dir, bit, expect):
    """run(vm) -> comparable result. expect(orig_result, on_result) -> problem or None."""
    count_case()
    try:
        a = run(vm_for(orig_dir, False))
        b = run(vm_for(new_dir, False))
        b0 = run(vm_for(new_dir, 0))
        c = run(vm_for(new_dir, bit))
    except (scfvm.ScriptError, scfvm.VMError) as e:
        fails.append(f'{label}: {e}')
        return
    if not (a == b == b0):
        fails.append(f'{label}: switch off differs from the original: {a} / {b} / {b0}')
        return
    bad = expect(a, c)
    if bad:
        fails.append(f'{label}: switch on: {bad} (original {a}, patched {c})')


def same(a, c):
    return None if a == c else 'should equal the original'


def favor(vm, **iv):
    base = dict(deai=True, level=1, stage=1, interest=3, fInter=False, tension=50, panic=1, countO=0, countH=0,
                feelings=VArray([None] * 8), bad=VArray([None, None]))
    base.update(iv)
    return vm.new_object('Favor', **base)


def fstate(vm, f):
    iv = vm.ivars(f)
    return tuple((k, tuple(v.items) if isinstance(v, VArray) else v) for k, v in sorted(iv.items()))


def fget(state, name):
    return dict(state)[name]


def run_cases(orig, new):
    def untouched(i):
        vm = vm_for(new, 0)
        return fstate(vm, favor(vm, interest=i))

    # ---- 1 No Losses
    for t, d in itertools.product((1, 50, 128), (-200, -8, 0, 8, 200)):
        def run(vm, t=t, d=d):
            f = favor(vm, tension=t)
            return vm.send(f, 'addTension', [d]), fstate(vm, f)
        check(f'Favor.addTension t={t} d={d}', run, orig, new, 1,
              (lambda a, c, t=t, d=d: same(a, c) if d >= 0 else (None if c[0] == t and fget(c[1], 'tension') == t else 'tension changed')))

    for d in (-48, -8, 0, 16):
        def run(vm, d=d):
            f = favor(vm, tension=60)
            vm._classvars[('TensionGauge', 7)] = f
            vm._classvars[('TensionGauge', 8)] = 60
            g = vm.new_object('TensionGauge')
            vm.send(g, 'addTension', [d])
            return fstate(vm, f), vm._classvars.get(('TensionGauge', 9)), vm._classvars.get(('TensionGauge', 13))
        check(f'TensionGauge.addTension d={d}', run, orig, new, 1,
              (lambda a, c, d=d: same(a, c) if d >= 0 else (None if fget(c[0], 'tension') == 60 and c[1] is None and c[2] is None else 'loss applied')))

    for notes in ([], [0], [1], [0, 1, 1], [1, 0, 0, 0, 1]):
        def run(vm, notes=notes):
            f = favor(vm, countO=notes.count(0), countH=notes.count(1), feelings=VArray(notes + [None] * (8 - len(notes))))
            return vm.send(f, 'downFeel', []), fstate(vm, f)
        check(f'Favor.downFeel {notes}', run, orig, new, 1,
              lambda a, c, notes=notes: None if c[0] == -1 and fget(c[1], 'feelings')[:len(notes)] == tuple(notes) else 'a note was removed')

    for i, v in itertools.product((0, 3, 9), (-9, -1, 0, 1, 3)):
        def run(vm, i=i, v=v):
            f = favor(vm, interest=i)
            return vm.send(f, 'addInterest', [v]), fstate(vm, f)
        check(f'Favor.addInterest i={i} v={v}', run, orig, new, 1,
              lambda a, c, i=i, v=v: same(a, c) if v >= 0 else (None if c[0] == i and c[1] == untouched(i) else 'interest or tension lowered'))

    for i, fi in itertools.product((0, 1, 5), (False, True)):
        def run(vm, i=i, fi=fi):
            f = favor(vm, interest=i, fInter=fi, tension=64, panic=3)
            return vm.send(f, 'downInterest', []), fstate(vm, f)
        check(f'Favor.downInterest i={i} fInter={fi}', run, orig, new, 1,
              lambda a, c, i=i: None if c[0] == i and fget(c[1], 'tension') == fget(a[1], 'tension')
              and fget(c[1], 'panic') == fget(a[1], 'panic') and fget(c[1], 'fInter') is False else 'interest lowered or decay changed')

    for bad in ([None, None], [9, None], [9, 10]):
        def run(vm, bad=bad):
            f = favor(vm, bad=VArray(bad))
            vm.send(f, 'addBad', [11])
            return fstate(vm, f)
        check(f'Favor.addBad {bad}', run, orig, new, 1,
              lambda a, c, bad=bad: None if fget(c, 'bad') == tuple(bad) else 'mark added')

    # ---- 2 Fewer Rejections
    def history(vm, t, hits):
        vm._classvars[('MatchHistory', 9)] = t
        vm._classvars[('MatchHistory', 11)] = VArray(hits + [None] * (8 - len(hits)))
        return vm.new_object('MatchHistory')
    for t, hits in [(2, [None, None]), (3, [1, None, None]), (4, [None, None, None, None]), (4, [1, None, None, None]),
                    (5, [1, None, None, None, None]), (3, [None, 2, None])]:
        for sel in ('checkLose3', 'checkLose4'):
            check(f'MatchHistory.{sel} t={t} {hits}', lambda vm, t=t, hits=hits, sel=sel: vm.send(history(vm, t, hits), sel, []),
                  orig, new, 2, lambda a, c: None if c is False else 'still true')

    for t in (1, 68, 100, 128):
        def run(vm, t=t):
            vm._classvars[('TensionGauge', 8)] = t
            return vm.send(vm.new_object('TensionGauge'), 'getTension', [])
        check(f'TensionGauge.getTension {t}', run, orig, new, 2, lambda a, c, t=t: None if c == t + 32 else 'not +32')

    for i, r20, r10 in itertools.product(range(10), (0, 4, 10, 19), (0, 3, 6, 9)):
        def run(vm, i=i, r20=r20, r10=r10):
            vm.rnd = lambda n: r20 if n == 20 else r10
            p = vm.new_object('Parson', favor=favor(vm, interest=i))
            return vm.send(p, 'checkInterest', [])
        want = 2 if i + 3 > r20 else (0 if i + 3 > r10 else 1)
        check(f'Parson.checkInterest i={i} r={r20},{r10}', run, orig, new, 2, lambda a, c, want=want: None if c == want else f'want {want}')

    # ---- 4 Easier Meetings
    for spot, rolls, enabled in [(0, [0, 0, 3], {3}), (0, [5, 3], {3}), (1, [4], {4}), (1, [0] * 12, set()),
                                 (0, [2, 2, 2, 2, 2, 2, 2, 2, 2, 7], {7})]:
        def run(vm, spot=spot, rolls=rolls, enabled=enabled):
            seq = iter(rolls + [0] * 20)
            calls = []
            scfvm.NATIVES[('GameParam', 'c', 'checkEncount', 1)] = lambda vm, r, a: calls.append(a[0]) or next(seq)
            scfvm.NATIVES[('Parson', 'c', 'isEnable', 1)] = lambda vm, r, a: a[0] in enabled
            try:
                return vm.send(vm.vclass('GameParam'), 'checkFirst' if spot == 0 else 'checkSecond', []), len(calls)
            finally:
                del scfvm.NATIVES[('GameParam', 'c', 'checkEncount', 1)]
                del scfvm.NATIVES[('Parson', 'c', 'isEnable', 1)]
        first_ok = next((k for k, r in enumerate(rolls[:9]) if r > 0 and r in enabled), None)
        want = (rolls[first_ok], first_ok + 1) if first_ok is not None else ((rolls + [0] * 9)[8], 9)
        check(f'GameParam.check{"First" if spot == 0 else "Second"} {rolls}', run, orig, new, 4,
              lambda a, c, want=want: None if c == want else f'want {want}')

    # ---- 8 More Tries
    for stock, mx in ((0, 1), (1, 1), (0, 2), (2, 2)):
        def run(vm, stock=stock, mx=mx):
            g = vm.new_object('GameParam', atkStock=stock, atkMax=mx)
            return vm.send(g, 'getAttack', []), vm.send(g, 'useAttack', []), vm.get_ivar(g, 'atkStock')
        check(f'GameParam.get/useAttack stock={stock} max={mx}', run, orig, new, 8,
              lambda a, c, stock=stock, mx=mx: None if c == (mx, True, stock) else f'want {(mx, True, stock)}')

    for deck, ptr in (([0, 0, 0], 3), ([5, 0, 7], 1), ([5, 6, 7], 0), ([0, 0], 0)):
        def run(vm, deck=deck, ptr=ptr):
            vm._classvars[('TopicPlayer', 6)] = VArray(deck)
            vm._classvars[('TopicPlayer', 7)] = ptr
            dealt = []

            def set_deck(vm, r, a):
                dealt.append(1)
                vm._classvars[('TopicPlayer', 6)] = VArray([1] * 16)
                vm._classvars[('TopicPlayer', 7)] = 0
            scfvm.NATIVES[('TopicPlayer', 'c', 'setDeck', 0)] = set_deck
            try:
                return vm.send(vm.vclass('TopicPlayer'), 'getRemainder', []), len(dealt)
            finally:
                del scfvm.NATIVES[('TopicPlayer', 'c', 'setDeck', 0)]
        left = sum(1 for x in deck[ptr:] if x > 0)
        want = (left, 0) if left or ptr == 0 else (16, 1)
        check(f'TopicPlayer.getRemainder {deck}@{ptr}', run, orig, new, 8, lambda a, c, want=want: None if c == want else f'want {want}')

    # ---- the Easy Mode panel (Configuration easyMode:) driven with scripted pad input, one entry per frame
    for start, mode, frames, want_flags, want_save in [
            (False, 0, [(0, 16384), (32, 0), (0, 16384), (0, 8192), (0, 4096), (0, 4096), (64, 0)], 6, True),
            (6, 0, [(0, 16384), (32, 0), (0, 32768), (64, 0)], 6, False),     # toggled back: no save prompt
            (6, 1, [(0, 4096), (32, 0), (64, 0)], 14, False),                          # in-game mode: never prompts
            (15, 0, [(32, 0), (0, 16384), (32, 0), (64, 0)], 12, True)]:
        def run(vm, start=start, mode=mode, frames=frames):
            vm._classvars[FLAG] = start
            st = {'f': -1}

            def sleep(vm, r, a):
                st['f'] += 1
                return r
            seq = [(0, 0)] + frames              # the first sleep is the fade-in, before the input loop
            pad = lambda: seq[min(max(st['f'], 0), len(seq) - 1)]  # noqa: E731
            hooks = {('K2_Script', 'i', 'sleep', 1): sleep,
                     ('ControlPad', 'c', 'trig', 0): lambda vm, r, a: pad()[0],
                     ('ControlPad', 'c', 'rapid', 0): lambda vm, r, a: pad()[1]}
            scfvm.NATIVES.update(hooks)
            try:
                vm.send(vm.new_object('Configuration'), 'easyMode', [mode])
            finally:
                for k in hooks:
                    del scfvm.NATIVES[k]
            saves = sum(1 for x in vm.log if x[0] == 'ConfigSave' and x[1] == 'scriptMain')
            alive = ({x.recv for x in vm.log if x[1] == 'new' and x[0] != 'ConfigSave'}
                     - {x.recv for x in vm.log if x[1] == 'destruct'} - {0})
            return vm._classvars[FLAG], saves, len(alive)
        count_case()
        try:
            vm = scfvm.VM(new, stubs=(scfvm.DEFAULT_STUBS - {'ControlPad'}) | {'ConfigSave'})
            got = run(vm)
        except (scfvm.ScriptError, scfvm.VMError) as e:
            fails.append(f'easyMode {start}/{mode}: {e}')
            continue
        if got != (want_flags, int(want_save), 0):
            fails.append(f'easyMode {start}/{mode} {frames}: got flags/saves/objects left {got}, '
                         f'want {(want_flags, int(want_save), 0)}')

    # ---- title menu: command 6 shows sprite {114, 4}, 0..5 the original table
    vm = scfvm.VM(new)
    mm = vm.new_object('MainMenu')
    for c, want in enumerate([[114, 0], [114, 1], [114, 5], [114, 2], [114, 3], [119, 0], [114, 4]]):
        count_case()
        got = vm.send(mm, 'menuTex', [c])
        if list(got.items) != want:
            fails.append(f'MainMenu.menuTex {c}: {got} != {want}')

    # ---- the switch bits
    for v, want in ((None, 0), (False, 0), (True, 0), (0, 0), (5, 5), (15, 15)):
        vm = vm_for(new, v)
        got = vm.send(vm.vclass('GameParam'), 'easyFlags', [])
        bits = [vm.send(vm.vclass('GameParam'), 'easy', [b]) for b in (1, 2, 4, 8)]
        count_case()
        if got != want or bits != [bool(want & b) for b in (1, 2, 4, 8)]:
            fails.append(f'GameParam.easyFlags {v!r}: {got} {bits}')


def main():
    orig = sys.argv[1]
    new, status = tpj.build_patched(orig, sorted(glob.glob(os.path.join(tpj.ROOT, 'patches', 'scripts', '*.asm'))))
    bad = {p: s for p, s in status.items() if s}
    if bad:
        for p, s in bad.items():
            print(f'{os.path.basename(p)}: {s}')
        print('FAIL')
        sys.exit(1)
    try:
        run_cases(orig, new)
    finally:
        shutil.rmtree(new, ignore_errors=True)
    for f in fails[:20]:
        print('  ' + f)
    print(f'{count} cases, {len(fails)} failed')
    print('FAIL' if fails else 'PASS')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
