#!/usr/bin/env python3
"""Regression test: bytecode patches must not change how Japanese text is drawn.

Usage: test_patches_jp.py <script_dir> [--patches DIR] [--only Class.method[/argc]] [-v]

<script_dir> holds the CLEAN unpacked SCF classes (build/work/script_orig). For every
patches/scripts/*.asm the script builds a patched copy in a temp directory (with
tools/reinsert/apply_script_patches.py) and runs scenarios on both class sets with
tools/qa/scfvm.py. Japanese scenarios must give the same result and the same stub
call log (FontChar/Sprite/DialogBox calls) on both sets, floats within a tolerance.
English scenarios run on the patched set only and print a short summary.

A patched method without a scenario is listed as UNTESTED. Exit status 1 on any
mismatch, VM error, patch that does not apply, or English scenario that crashes.

Game text comes from text/*.json when present (gitignored); otherwise made-up
generic strings are used. See docs/qa-scfvm.md for how to add a scenario.
"""
import argparse
import glob
import inspect
import json
import os
import re
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path[:0] = [HERE, os.path.join(ROOT, 'tools', 'reinsert'), os.path.join(ROOT, 'tools', 'font')]
import apply_script_patches as aps  # noqa: E402
import encoding  # noqa: E402
import scfvm  # noqa: E402
from scfvm import VArray, VString  # noqa: E402

F32_TOL = 1e-3          # float32 rounding noise
HALF_PX = 0.5           # D-015: centred TextLineC lines may move by half a pixel
WIDTHS = json.load(open(os.path.join(ROOT, 'tools', 'font', 'en_widths.json')))['widths']


# --------------------------------------------------------------------------- test data

class Data:
    """Game strings from text/*.json (local only) with generic fallbacks."""

    def __init__(self, root):
        self.root = root
        self._recs = None
        self._lim = None

    @property
    def recs(self):
        if self._recs is None:
            self._recs = {}
            for f in sorted(glob.glob(os.path.join(self.root, 'text', '*.json'))):
                for r in json.load(open(f, encoding='utf-8')):
                    self._recs[r['id']] = r['text']
        return self._recs

    @property
    def limits(self):
        if self._lim is None:
            p = os.path.join(self.root, 'tools', 'reinsert', 'limits.json')
            self._lim = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
        return self._lim

    def by_display(self, display):
        out, seen = [], set()
        for k, v in self.limits.items():
            if v.get('display') == display and k in self.recs and self.recs[k] not in seen and self.recs[k]:
                seen.add(self.recs[k])
                out.append(self.recs[k])
        return out

    def dialogue_sample(self, n):
        """n evenly spaced dialogue lines (control codes kept), only long ones so that wrapping happens."""
        lines = [t for k, t in self.recs.items() if ':' in k and len(re.sub(r'\{[^{}]*\}', '', t)) >= 36]
        if not lines:
            return list(GENERIC_JA) * (n // len(GENERIC_JA) + 1)
        step = max(1, len(lines) // n)
        return lines[::step][:n]

    def all_codes(self):
        """Distinct character codes (>= 0x100, plus printable ASCII) used by the game text."""
        codes = set()
        for t in self.recs.values():
            codes.update(scfvm.text_codes(t, english=False))
        return sorted(c for c in codes if c >= 0x100 or 32 <= c < 127)


GENERIC_JA = [      # invented test strings, not game text (used only when text/ is missing)
    'あ', 'いろは', 'ひらがなのテスト', 'カタカナノテスト', '漢字と仮名の混在',
    '１２３４５６７８９０', 'ＡＢＣｄｅｆ！？', '「かぎ」（かっこ）…', '試験用の文字列その一',
    'とても長い文字列をここに置いて幅の計算を確かめる', '二行目\n三行目が長い', '一\n二二二二\n三',
]
GENERIC_EN = [
    'Yes', 'No', 'Save', 'Load game', 'WWW', 'iiiiiiii', 'little WWW', 'Use this name?',
    'Name entry\nUse this name?\nlittle WWW', 'A fairly long English menu entry here',
]
GENERIC_EN_DIALOGUE = [
    '{V0100}{W12}Oh, hello there!{W30} I did not expect to see you here today.',
    'This is a longer line of English text that has to be wrapped over more than one line of the window,'
    ' and it keeps going for a while so that the right edge is reached.',
    'WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW',
    '{Nn}, is that you? ... I mean, iiiiii llllll.',
]
GENERIC_CONFIRM_JA = ['試験', '確認ダイアログの試験です', '一行目\n二行目はもっと長い文章です\n三行目']
GENERIC_CONFIRM_EN = [
    'Save?', 'Use this name?\nlittle WWW', 'No memory card inserted in slot 1.\nPlease check and retry.',
    'This message has a single line that is quite a bit longer than the usual ones in the game',
]


def ja_codes(text):
    return scfvm.text_codes(text, english=False)


def en_codes(text):
    return scfvm.text_codes(text, english=True)


# --------------------------------------------------------------------------- scenario model

class Case:
    """One scenario: run(vm) drives a fresh VM and returns a VM-independent result."""

    def __init__(self, key, label, run, lang='ja', tol=F32_TOL, mode='log', project=None,
                 oracle=None, summary=None, why='', stubs=(), steps=3_000_000, soft=False):
        self.key, self.label, self.run, self.lang = key, label, run, lang
        self.stubs, self.steps, self.soft = frozenset(stubs), steps, soft
        self.tol, self.mode, self.project = tol, mode, project
        self.oracle, self.summary, self.why = oracle, summary, why


SCENARIOS = {}


def scenarios(*keys):
    def deco(fn):
        for k in keys:
            SCENARIOS[k] = fn
        return fn
    return deco


def final_states(log):
    """Replay a call log to the end state of every stub instance (for redundant-call patches)."""
    st = {}
    for c in log:
        cls, sel, args = c
        if not c.recv:
            continue
        s = st.setdefault(c.recv, {'class': cls})
        if sel in ('new', 'initialize') and len(args) == 7:
            s.pop('destruct', None)         # initialize revives a destroyed glyph
            s['init'] = args
            s['code'] = args[0]
            s['pos'] = (args[3], args[4])
        elif sel == 'setCode':
            s['code'] = args[0]
        elif sel == 'setPos':
            s['pos'] = tuple(args)
        elif sel == 'move' and len(args) >= 2:
            s['pos'] = (args[0], args[1])       # target position
            s[sel] = args
        else:
            s[sel] = args
    # a destroyed glyph is gone: where it was last placed does not matter
    return [{'class': v['class'], 'destruct': ()} if 'destruct' in v else v for v in (st[k] for k in sorted(st))]


class Outcome:
    def __init__(self, result, log, err, vm):
        self.result, self.log, self.err, self.vm = result, log, err, vm


def execute(script_dir, case):
    vm = scfvm.VM(script_dir, stubs=scfvm.DEFAULT_STUBS | case.stubs, step_limit=case.steps)
    res = err = None
    try:
        res = case.run(vm)
    except scfvm.ScriptError as e:
        err = ('script', vm.describe(e.value), e.trace[:4])
    except scfvm.VMError as e:
        err = ('vm', str(e))
    log = case.project(vm) if case.project else vm.log
    return Outcome(res, log, err, vm)


def compare(case, a, b):
    """Return (problem or None, max float delta)."""
    if a.err or b.err:
        if a.err:
            return f'scenario fails on the ORIGINAL (fix the scenario): {a.err}; patched={b.err}', 0.0
        return f'error: original=None patched={b.err}', 0.0
    if not scfvm.values_equal(a.result, b.result, case.tol):
        return f'result differs {_first_diff(a.result, b.result, case.tol)}', 0.0
    if case.mode == 'state':
        sa, sb = final_states(a.log), final_states(b.log)
        if len(sa) != len(sb):
            return f'{len(sa)} vs {len(sb)} stub objects', 0.0
        for i, (x, y) in enumerate(zip(sa, sb)):
            if x.keys() != y.keys() or not all(scfvm.values_equal(x[k], y[k], case.tol) for k in x):
                return f'final state of object {i} differs: {x} != {y}', 0.0
        return None, max((_state_delta(x, y) for x, y in zip(sa, sb)), default=0.0)
    bad = scfvm.compare_logs(a.log, b.log, case.tol)
    return bad, (scfvm.max_float_delta(a.log, b.log) if not bad else 0.0)


def _first_diff(a, b, tol):
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        for i, (x, y) in enumerate(zip(a, b)):
            if not scfvm.values_equal(x, y, tol):
                return f'at [{i}]: original={_short(x)} patched={_short(y)}'
        return f'in length: original={len(a)} patched={len(b)}'
    return f'original={_short(a)} patched={_short(b)}'


def _state_delta(x, y):
    d = 0.0
    for k in x:
        if isinstance(x[k], tuple) and isinstance(y[k], tuple) and len(x[k]) == len(y[k]):
            for p, q in zip(x[k], y[k]):
                if isinstance(p, (int, float)) and isinstance(q, (int, float)) and not isinstance(p, bool):
                    d = max(d, abs(p - q))
    return d


def _short(v, n=160):
    s = repr(v)
    return s if len(s) <= n else s[:n] + '...'


# --------------------------------------------------------------------------- helpers for scenarios

def make_line(vm, cls, pitch, scale_idx, text, x=-120.0, y=60.0, layer=10, clut=0):
    tl = vm.new(cls, layer, x, y, pitch, clut, scale_idx)
    vm.send(tl, 'setText', [VString(text)])
    return tl


def glyph_x(vm):
    """Final x of every live FontChar (after setPos/move/initialize), creation order (for summaries)."""
    live = [st for st in final_states(vm.log) if st['class'] in ('FontChar', 'FontCharEx') and 'destruct' not in st]
    return [st['pos'][0] for st in live if 'pos' in st]


def en_adv(code, pitch):
    ch = encoding.char_of(code) if 0x8540 <= code <= 0x859F else None
    return (float(WIDTHS[ch]) * pitch / 24) if ch else float(pitch)


SCALES = (0.5, 0.75, 1.0, 1.25, 1.5)
LINE_PARAMS = [(24, 2), (18, 1), (26, 2), (25, 3)]   # (pitch, font scale index); 25 makes (n-1)*pitch odd


# --------------------------------------------------------------------------- TextLine / TextLineC

def _line_cases(key, cls, texts_ja, texts_en, centred):
    tol = HALF_PX if centred else F32_TOL
    meth = key.split('.')[1].split('/')[0]
    mode = 'state' if meth == 'setText' else 'log'
    why = []
    if centred:
        why.append('D-015: centring is a float division now; odd (n-1)*pitch moves a line by half a pixel')
    if meth == 'setText':
        why.append('the patched setText also repositions reused glyphs (D-015): compared as final glyph state')
    why = '; '.join(why)

    def mk(texts, lang):
        conv = ja_codes if lang == 'ja' else en_codes
        out = []
        if lang == 'ja' and key == 'TextLine.setText/1':
            out.append(_staffroll_case(key))
        if meth == 'setText':
            variants = ('reuse',)
        elif cls == 'TextLine':
            variants = ('fresh',)       # a TextLine that was re-set shorter is covered by setText/reuse
        else:
            variants = ('fresh', 'reuse')
        for variant in variants:
            for pitch, sc in LINE_PARAMS:
                for ti, t in enumerate(texts):
                    codes = conv(t)

                    def run(vm, codes=codes, pitch=pitch, sc=sc, ti=ti, variant=variant):
                        tl = vm.new(cls, 10, -120.0, 60.0, pitch, 0, sc)
                        if meth == 'setText':
                            vm.send(tl, 'setText', [VString(codes)])
                            # reuse path: a different text on the same object, then the same one again
                            for other in (texts[(ti + 1) % len(texts)], texts[(ti + 2) % len(texts)]):
                                vm.send(tl, 'setText', [VString(conv(other))])
                            vm.send(tl, 'setText', [VString(codes)])
                            return [vm.get_ivar(tl, 'posX')]
                        if variant == 'reuse':
                            # TextLineC.setText twice: the first glyphs stay (destroyed) in fList, so the
                            # original itself positions the second text's glyphs wrongly
                            vm.send(tl, 'setText', [VString(codes + codes[:1] * 3)])
                        vm.send(tl, 'setText', [VString(codes)])
                        vm.log.clear()      # setup is not under test (the patched setText logs extra setPos calls)
                        if meth == 'setPos':
                            vm.send(tl, 'setPos', [37.0, -11.0])
                        elif meth == 'move':
                            vm.send(tl, 'move', [37.0, -11.0, 5, 0])
                        elif meth == 'restart':
                            vm.send(tl, 'dormant')
                            vm.send(tl, 'restart')
                        else:
                            raise AssertionError(meth)
                        return [vm.get_ivar(tl, 'posX')]
                    out.append(Case(key, f'{lang} {cls} {variant} p{pitch} s{sc} #{ti}', run, lang=lang, tol=tol,
                                    mode=mode, why=why, soft=(variant == 'reuse' and meth != 'setText'),
                                    summary=lambda vm, r: _fmt_x(glyph_x(vm))))
        return out
    return mk(texts_ja, 'ja'), mk(texts_en, 'en')


def _staffroll_case(key):
    """End to end: the credits (StaffRoll.run) re-sets 18 TextLine objects with lines of any length."""
    def run(vm):
        vm.stub_results[('Parson', 'getDeai')] = False
        vm.stub_results[('GameParam', 'getClear')] = 0
        vm.stub_results[('GameParam', 'getMyouji')] = vm.string('Ab', english=False)
        vm.stub_results[('GameParam', 'getNamae')] = vm.string('Cd', english=False)
        vm.send(vm.new('StaffRoll'), 'run')
        return [1]
    return Case(key, 'ja StaffRoll.run end to end (18 reused TextLines)', run, mode='state',
                stubs={'Parson', 'GameParam'}, steps=20_000_000,
                why='StaffRoll.run is a consumer of TextLine.setText on reused lines of varying length')


def _fmt_x(xs, n=14):
    return 'glyph x: ' + ' '.join(f'{x:g}' for x in xs[-n:]) + (' ...' if len(xs) > n else '')


def _cases_for_line(key, cls, centred):
    def build(data):
        ja = [t.replace('\n', '') for t in (data.by_display('TextLine') or GENERIC_JA)]
        return _line_cases(key, cls, [t for t in ja if t][:30], GENERIC_EN, centred)
    return build


for _cls in ('TextLine', 'TextLineC'):
    for _m in ('setText/1', 'setPos/0', 'restart/0', 'move/4'):
        SCENARIOS[f'{_cls}.{_m}'] = _cases_for_line(f'{_cls}.{_m}', _cls, _cls == 'TextLineC')


@scenarios('TextLine.xOf/1')
def _xof_cases(data):
    ja = [t.replace('\n', '') for t in (data.by_display('TextLine') or GENERIC_JA)][:30]
    key = 'TextLine.xOf/1'

    def mk(texts, lang):
        out = []
        for pitch, sc in LINE_PARAMS:
            for ti, t in enumerate(texts):
                codes = ja_codes(t) if lang == 'ja' else en_codes(t)

                def run(vm, codes=codes, pitch=pitch, sc=sc):
                    cls = 'TextLineC'            # inherits xOf: from TextLine
                    tl = make_line(vm, cls, pitch, sc, codes)
                    return [vm.send(tl, 'xOf', [i]) for i in range(len(codes) + 1)]

                def oracle(res, codes=codes, pitch=pitch):
                    want, acc = [], 0.0
                    for i in range(len(codes) + 1):
                        want.append(acc)
                        if i < len(codes):
                            acc += en_adv(codes[i], pitch)
                    return None if scfvm.values_equal(res, want, F32_TOL * 4) else \
                        f'xOf {res} != model {want}'
                out.append(Case(key, f'{lang} xOf p{pitch} #{ti}', run, lang=lang, oracle=oracle,
                                summary=lambda vm, r: 'xOf: ' + ' '.join(f'{x:g}' for x in r[:12])))
        return out
    return mk(ja, 'ja'), mk(GENERIC_EN, 'en')


# --------------------------------------------------------------------------- ConfirmDialog

@scenarios('ConfirmDialog.initialize/7')
def _confirm_cases(data):
    ja = data.by_display('ConfirmDialog') or GENERIC_CONFIRM_JA
    key = 'ConfirmDialog.initialize/7'

    def run_for(codes, width, mode):
        def run(vm):
            vm.new('ConfirmDialog', 15, 0.0, 0.0, width, VString(codes), mode)
            return [c[2] for c in vm.log if c[0] == 'DialogBox' and c[1] == 'new']
        return run

    def box_summary(vm, r):
        boxes = [c[2] for c in vm.log if c[0] == 'DialogBox' and c[1] == 'new']
        xs = sorted({round(c[2][3], 1) for c in vm.log if c[0] == 'FontChar' and c[1] == 'new'})
        return f'DialogBox new{boxes[0] if boxes else None}; glyph x {xs[0] if xs else "-"}..{xs[-1] if xs else "-"}'

    ja_cases = []
    for i, t in enumerate(ja):
        for width, mode in ((None, 0), (None, 2)):
            ja_cases.append(Case(key, f'ja msg#{i} w={width} mode={mode}', run_for(ja_codes(t), width, mode),
                                 project=None))
    for i, t in enumerate(ja[:12]):
        for width in (50, 200, 400, 700):
            ja_cases.append(Case(key, f'ja msg#{i} w={width} mode=1', run_for(ja_codes(t), width, 1)))
    en_cases = []
    for i, t in enumerate(GENERIC_CONFIRM_EN):
        en_cases.append(Case(key, f'en msg#{i}', run_for(en_codes(t), None, 2), lang='en', summary=box_summary))
    return ja_cases, en_cases


# --------------------------------------------------------------------------- DeckView

@scenarios('DeckView.setName/0')
def _deck_cases(data):
    key = 'DeckView.setName/0'
    ja = ['あ', 'あいう', 'あいうえおか', 'あいうえおかき', 'ひらがなカタカナ漢字', '試験名０１', '１２３４５６７８９',
          '漢字']

    def run_for(codes):
        def run(vm):
            vm.stub_results[('WadaiParam', 'getDeckName')] = lambda vm_, r, a: VString(codes)
            dv = vm.new_object('DeckView', lay=5)
            vm.send(dv, 'setName')
            name = vm.get_ivar(dv, 'name')
            return [vm.send(name, 'length')]
        return run

    def summary(vm, r):
        pos = [c[2][3] for c in vm.live_log() if c[0] == 'FontChar' and c[1] == 'new']
        return f'{r[0]} glyphs, x: ' + ' '.join(f'{x:g}' for x in pos)
    ja_cases = [Case(key, f'ja name#{i}', run_for(ja_codes(t)), project=lambda vm: vm.live_log(),
                     why='measuring TextLineC glyphs are destroyed; only surviving stub objects are compared')
                for i, t in enumerate(ja)]
    en_cases = [Case(key, f'en name {t!r}', run_for(en_codes(t)), lang='en', summary=summary,
                     project=lambda vm: vm.live_log())
                for t in ('Deck 01', 'Wide WWWWWWWW', 'iiiiiiiiiiiiiiiii', 'A', 'Hello')]
    return ja_cases, en_cases


# --------------------------------------------------------------------------- TextWindow / LogLine putChar

def _put_codes(data):
    codes = data.all_codes()
    if not codes:
        codes = list(range(0x829F, 0x82F2)) + list(range(0x8340, 0x8397)) + list(range(0x889F, 0x88FD))
    extra = [0x815E, 0x8162, 0x8176, 0x816A, 0x8140, 0x824F, 0x8260, 0x8281, 0x853F, 0x85A0, 0x8640, 0x9FFC,
             0xE040, 65, 66, 97, 0x20]
    return sorted(set(codes) | set(extra))


EN_CODES = [encoding.code_of(ch) for ch in 'Wi.l, mAg?']


@scenarios('TextWindow.putChar/1')
def _tw_cases(data):
    key = 'TextWindow.putChar/1'
    codes_all = _put_codes(data)
    right = -293.0 + 586.0 - 17.0          # right wrap edge of the message window

    def run_for(codes, scl_idx, starts):
        def run(vm):
            tw = vm.new('TextWindow')
            sc = SCALES[scl_idx]
            vm.set_ivar(tw, 'fontSclW', sc)
            vm.set_ivar(tw, 'fontSclH', sc)
            res = []
            for start in starts:
                for code in codes:
                    vm.set_ivar(tw, 'curX', start)
                    vm.set_ivar(tw, 'curY', 84.0)
                    vm.send(tw, 'putChar', [code])
                    res.append((vm.get_ivar(tw, 'curX'), vm.get_ivar(tw, 'curY')))
            return res
        return run

    def summary(vm, r):
        return 'advance per char (W i . l , space m A g ?): ' + ' '.join(f'{x[0] + 276.0:g}' for x in r)
    ja = []
    # the whole code set at the start of a line, then the wrap edge region with a handful of codes
    ja.append(Case(key, 'ja all codes @ line start, scale 1.0', run_for(codes_all, 2, [-276.0])))
    sample = [c for c in codes_all if c >= 0x8140][:40:3] + [0x815E, 0x8162, 0x853F, 0x85A0]
    for sc in (0, 1, 3, 4):
        edge = [right - 60, right - 49.0, right - 48.0, right - 47.5, right - 30.0, right - 24.5,
                right - 24.0, right - 23.5, right - 23.0, right - 22.5, right - 12.0, right - 1.0, right, right + 1.0]
        ja.append(Case(key, f'ja edge sweep, font size {sc}', run_for(sample, sc, edge)))
    def e2e(texts, english):
        def run(vm):
            tw = vm.new('TextWindow')
            queue = vm.get_ivar(tw, 'putQueue')
            res = []
            for t in texts:
                vm.set_ivar(tw, 'curX', -276.0)
                vm.set_ivar(tw, 'curY', 84.0)
                for tok in re.split(r'(\{[^{}]*\})', t):
                    if tok.startswith('{'):
                        continue                       # control codes belong to Parson, not the window
                    for c in (en_codes(tok) if english else ja_codes(tok)):
                        vm.send(tw, 'put', [5 if c == 0x815E else c])      # command 5 = line break
                while vm.send(queue, 'length'):
                    vm.send(tw, 'output')
                res.append((vm.get_ivar(tw, 'curX'), vm.get_ivar(tw, 'curY')))
            return res
        return run
    lines = data.dialogue_sample(120)
    for i in range(0, len(lines), 20):
        ja.append(Case(key, f'ja e2e put:/output with dialogue lines {i}..{i + 19}', e2e(lines[i:i + 20], False)))
    import en_text
    wrapped = [en_text.wrap(t) for t in GENERIC_EN_DIALOGUE]
    en = [Case(key, 'en e2e put:/output with wrapped English lines', e2e(wrapped, True), lang='en',
               summary=lambda vm, r: 'end curX/curY: ' + ' '.join(f'({x:g},{y:g})' for x, y in r)),
          Case(key, 'en widths @ line start', run_for(EN_CODES, 2, [-276.0]), lang='en', summary=summary),
          Case(key, 'en wrap at the right edge', run_for(EN_CODES, 2, [right - 12.0, right - 5.0, right]),
               lang='en', summary=lambda vm, r: 'curX/curY after: ' + ' '.join(f'({x:g},{y:g})' for x, y in r[:9]))]
    return ja, en


@scenarios('LogLine.putChar/1')
def _ll_cases(data):
    key = 'LogLine.putChar/1'
    codes_all = _put_codes(data)
    right = 276.0

    def run_for(codes, scl_idx, starts):
        def run(vm):
            ll = vm.new_object('LogLine')
            vm.set_ivar(ll, 'fList', vm.new('Vector', 80))
            vm.set_ivar(ll, 'nofLine', 1)
            for name, v in (('posX', -276.0), ('posY', 100.0), ('curY', 120.0), ('pitchX', -1.0), ('indent', 0),
                            ('fClut', 0), ('fSclW', SCALES[scl_idx]), ('fSclH', SCALES[scl_idx]),
                            ('rCurX', -276.0)):
                vm.set_classvar('LogLine', name, v)
            res = []
            for start in starts:
                for code in codes:
                    vm.set_classvar('LogLine', 'curX', start)
                    vm.set_classvar('LogLine', 'curY', 120.0)
                    vm.send(ll, 'putChar', [code])
                    res.append((vm.get_classvar('LogLine', 'curX'), vm.get_classvar('LogLine', 'curY')))
            return res
        return run
    ja = [Case(key, 'ja all codes @ line start, scale 0.75', run_for(codes_all, 1, [-276.0]))]
    sample = [c for c in codes_all if c >= 0x8140][:40:3] + [0x815E, 0x8162, 0x853F, 0x85A0]
    for sc in (1, 2, 4):
        edge = [right - 40, right - 25.0, right - 24.0, right - 18.5, right - 18.0, right - 17.9, right - 12.0,
                right - 1.0, right, right + 1.0]
        ja.append(Case(key, f'ja edge sweep, scale idx {sc}', run_for(sample, sc, edge)))
    def e2e(texts, english):
        def run(vm):
            vm.stubs.add('GameParam')       # {Nm}/{Nn} read the player's name
            vm.stub_results[('GameParam', 'getMyouji')] = vm.string('Ab', english=False)
            vm.stub_results[('GameParam', 'getNamae')] = vm.string('Cd', english=False)
            res = []
            for t in texts:
                codes = en_codes(t) if english else ja_codes(t)
                ll = vm.new('LogLine', -276.0, 100.0, 0, VArray([VString(codes), 1, 0, None]))
                res.append((vm.get_classvar('LogLine', 'curX'), vm.get_classvar('LogLine', 'curY'),
                            vm.get_ivar(ll, 'nofLine')))
            return res
        return run
    lines = data.dialogue_sample(120)
    for i in range(0, len(lines), 20):
        ja.append(Case(key, f'ja e2e LogLine.initialize with dialogue lines {i}..{i + 19}',
                       e2e(lines[i:i + 20], False), stubs={'GameParam'}))
    import en_text
    wrapped = [en_text.wrap(t) for t in GENERIC_EN_DIALOGUE]
    en = [Case(key, 'en e2e LogLine.initialize with wrapped English lines', e2e(wrapped, True), lang='en',
               stubs={'GameParam'}, summary=lambda vm, r: 'end curX/curY/lines: ' + ' '.join(
                   f'({x:g},{y:g},{n})' for x, y, n in r)),
          Case(key, 'en widths @ line start', run_for(EN_CODES, 1, [-276.0]), lang='en',
               summary=lambda vm, r: 'curX after each: ' + ' '.join(f'{x:g}' for x, _ in r)),
          Case(key, 'en wrap at the right edge', run_for(EN_CODES, 1, [right - 9.0, right - 3.0]), lang='en',
               summary=lambda vm, r: 'curX/curY after: ' + ' '.join(f'({x:g},{y:g})' for x, y in r[:9]))]
    return ja, en


# --------------------------------------------------------------------------- ShioriListItem

@scenarios('ShioriListItem.initialize/2')
def _shiori_cases(data):
    """Save-list row: a Japanese name of up to 3 + 3 characters must be placed exactly as before."""
    key = 'ShioriListItem.initialize/2'
    ja_surnames = ['あ', 'あい', 'あいう', '日', '日本', '日本人', 'ＡＢ']
    ja_given = ['う', 'うえ', 'うえお', '太', '太郎', '太郎丸']

    def run_for(sur, giv, english):
        def run(vm):
            conv = en_codes if english else ja_codes

            def get(vm_, r, a):
                o = vm_._new_stub('ShioriData', ())
                return o
            vm.stubs.add('ShioriData')
            vm.stub_results[('ShioriData', 'get')] = get
            vm.stub_results[('ShioriData', 'getMyouji')] = VString(conv(sur))
            vm.stub_results[('ShioriData', 'getNamae')] = VString(conv(giv))
            vm.stub_results[('ShioriData', 'getUpdate')] = VArray([None] * 8)
            item = vm.new('ShioriListItem', 10, 3)
            vm.send(item, 'restart')
            vm.send(item, 'setPos', [11.0, -7.0])
            return [vm.get_ivar(item, 'name0X'), vm.get_ivar(item, 'name1X')]
        return run

    def summary(vm, r):
        xs = glyph_x(vm)
        return f'name0X={r[0]:g} name1X={r[1]:g}; glyph x: ' + ' '.join(f'{x:g}' for x in xs)
    ja = [Case(key, f'ja {a}+{b}', run_for(a, b, False), stubs={'ShioriData'}, mode='state',
               why='the patched TextLine.setText also repositions glyphs (D-015): compared as final glyph state')
          for a in ja_surnames for b in ja_given if len(a) <= 3 and len(b) <= 3]
    en = [Case(key, f'en {a!r}+{b!r}', run_for(a, b, True), lang='en', stubs={'ShioriData'}, summary=summary)
          for a, b in (('Ann', 'Lee'), ('Wwwwwwww', 'Wwwwwwww'), ('Smith', 'Jo'), ('Iiiiiiii', 'Iiiiiiii'))]
    return ja, en


# --------------------------------------------------------------------------- Parson.setDispName

@scenarios('Parson.setDispName/1')
def _parson_cases(data):
    """Name plate. Japanese surnames of 0 or 3 characters (and non-strings) must come out as before.

    1 and 2 character surnames are padded by the original and shown whole by the patch (D-016):
    those are printed in the English list, not compared."""
    key = 'Parson.setDispName/1'

    def run_for(arg):
        def run(vm):
            p = vm.new_object('Parson')
            vm.send(p, 'setDispName', [arg])
            return vm.get_ivar(p, 'dispName')
        return run
    mk = lambda t: VString(ja_codes(t))  # noqa: E731
    ja = [Case(key, f'ja {t!r}', run_for(mk(t))) for t in ('', '日本人', 'あいう', 'ＡＢＣ', '山田花')]
    ja += [Case(key, 'ja nil', run_for(None)), Case(key, 'ja non-string', run_for(5))]
    summary = lambda vm, r: f'dispName = {r!r}'  # noqa: E731
    en = [Case(key, f'en/by-design {t!r}', run_for(VString(ja_codes(t) if any(ord(c) > 255 for c in t) else en_codes(t))),
               lang='en', summary=summary) for t in ('日', '日本', 'Ann', 'Wwwwwwww', '')]
    return ja, en


# --------------------------------------------------------------------------- running

HEADER = re.compile(r'^; (target|add): (\S+) (\S+) argc=(\d+) table=(methods2?)$', re.M)


def patch_key(path):
    m = HEADER.search(open(path, encoding='utf-8').read())
    if not m:
        return None, None, None
    return f'{m.group(2)}.{m.group(3)}/{m.group(4)}', m.group(1), (m.group(2), m.group(3), int(m.group(4)), m.group(5))


def lint_patch(patched_dir, target):
    """Static checks of the patched method (see scfvm.lint_method)."""
    cls, meth, argc, table = target
    vm = scfvm.VM(patched_dir)
    cd = vm.classdef(cls)
    m = (cd.methods if table == 'methods' else cd.methods2).get((meth, argc))
    if m is None:
        return [f'{cls}>>{meth}/{argc} not found in the patched set']
    return scfvm.lint_method(cd, m, class_side=(table == 'methods2'))


def build_patched(script_dir, patch_files):
    tmp = tempfile.mkdtemp(prefix='scfvm_patched_')
    shutil.copytree(script_dir, tmp, dirs_exist_ok=True)
    # apply() grew a `symbols` argument for name entry (D-016); stay compatible with both shapes
    extra = [aps.symbol_array()] if len(inspect.signature(aps.apply).parameters) > 3 else []
    widths = aps.width_array()
    status = {}
    for p in patch_files:
        try:
            msg = aps.apply(tmp, p, widths, *extra)
            status[p] = ('input not clean: ' + msg) if ('already' in msg and 'added' not in msg) else None
        except Exception as e:  # noqa: BLE001 - report any apply failure per patch
            status[p] = f'apply failed: {e}'
    return tmp, status


_NAME_WHY = 'name entry changes Japanese behaviour on purpose (3 -> 8 slots, D-016): needs spec scenarios, not JA identity'
UNTESTED_WHY = {
    'NameEntry': _NAME_WHY, 'NameEntryEdit': _NAME_WHY, 'NameEntryList': _NAME_WHY,
    'ShioriData': 'serialize/cut keep the 256-byte slot header (D-016): no Japanese-identity form, needs a spec scenario',
    'GameParam': 'name-entry work (D-016): no scenario yet', 'K2_Script': 'name-entry work (D-016): no scenario yet',
}


def run_key(key, kind, orig_dir, new_dir, data, verbose):
    """Run all scenarios of one patched method. Returns a result dict."""
    fn = SCENARIOS[key]
    ja, en = fn(data)
    res = {'ja': len(ja), 'en': len(en), 'fail': [], 'warn': [], 'delta': 0.0, 'en_err': [], 'summaries': [],
           'why': set()}
    for c in ja:
        t_new = execute(new_dir, c)
        if c.oracle and kind == 'add':
            if t_new.err:
                res['fail'].append((c.label, f'error {t_new.err}'))
            else:
                bad = c.oracle(t_new.result)
                if bad:
                    res['fail'].append((c.label, bad))
            continue
        t_old = execute(orig_dir, c)
        bad, delta = compare(c, t_old, t_new)
        res['delta'] = max(res['delta'], delta)
        if c.why:
            res['why'].add(c.why.strip())
        if bad:
            res['warn' if c.soft else 'fail'].append((c.label, bad))
    for c in en:
        t_new = execute(new_dir, c)
        if t_new.err:
            if 'reuse' in c.label and any(sc.soft for sc in ja):
                res['warn'].append((c.label, f'EN: {t_new.err}'))
            else:
                res['en_err'].append((c.label, t_new.err))
            continue
        if c.oracle:
            bad = c.oracle(t_new.result)
            if bad:
                res['fail'].append((c.label, 'model: ' + bad))
        if c.summary:
            res['summaries'].append((c.label, c.summary(t_new.vm, t_new.result)))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('script_dir')
    ap.add_argument('--patches', default=os.path.join(ROOT, 'patches', 'scripts'))
    ap.add_argument('--only')
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args()

    patch_files = sorted(glob.glob(os.path.join(args.patches, '*.asm')))
    data = Data(ROOT)
    t0 = time.time()
    tmp, status = build_patched(args.script_dir, patch_files)
    rows, failed = [], False
    try:
        for p in patch_files:
            key, kind, target = patch_key(p)
            name = os.path.basename(p)
            if key is None:
                rows.append((name, '?', 'UNTESTED', 'no target header'))
                continue
            if args.only and not key.startswith(args.only):
                continue
            lint = [] if status[p] else lint_patch(tmp, target)
            for pr in lint[:5]:
                print(f'  LINT {pr}')
            if key not in SCENARIOS:
                note = status[p] or UNTESTED_WHY.get(target[0], 'no scenario')
                if lint:
                    rows.append((key, '-', 'FAIL', f'static lint: {len(lint)} problems'))
                    failed = True
                else:
                    rows.append((key, '-', 'UNTESTED', note + ('' if status[p] else '; static lint clean')))
                continue
            if status[p]:
                rows.append((key, '-', 'FAIL', status[p]))
                failed = True
                continue
            r = run_key(key, kind, args.script_dir, tmp, data, args.verbose)
            if lint:
                r['fail'].append(('static lint', '; '.join(lint[:3])))
            verdict = 'PASS' if not r['fail'] and not r['en_err'] else 'FAIL'
            failed |= verdict == 'FAIL'
            note = f'max |delta| {r["delta"]:g}' if kind != 'add' else 'vs independent model (no original)'
            if verdict == 'PASS' and r['warn']:
                note += f'; {len(r["warn"])} soft warnings (see above)'
            rows.append((key, f'{r["ja"]} ja + {r["en"]} en', verdict, note))
            for label, msg in r['warn'][:2]:
                print(f'  WARN {key} [{label}]: {_short(msg, 300)}')
            for label, msg in r['fail'][:3]:
                print(f'  MISMATCH {key} [{label}]: {_short(msg, 400)}')
            if len(r['fail']) > 3:
                print(f'  ... {len(r["fail"]) - 3} more mismatches in {key}')
            for label, err in r['en_err'][:3]:
                print(f'  EN ERROR {key} [{label}]: {_short(err, 300)}')
            shown = r['summaries'] if args.verbose else r['summaries'][:3]
            for label, s in shown:
                print(f'  en {key} [{label}] {s}')
            if args.verbose:
                for w in sorted(r['why']):
                    print(f'  note {key}: {w}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    w = max(len(r[0]) for r in rows) if rows else 10
    print(f'{"method":<{w}}  {"scenarios":<14}  result    note')
    for key, sc, verdict, note in rows:
        print(f'{key:<{w}}  {sc:<14}  {verdict:<8}  {note}')
    untested = [r[0] for r in rows if r[2] == 'UNTESTED']
    print(f'\n{sum(r[2] == "PASS" for r in rows)} passed, {sum(r[2] == "FAIL" for r in rows)} failed, '
          f'{len(untested)} untested ({time.time() - t0:.0f}s)')
    if untested:
        print('UNTESTED: ' + ', '.join(untested))
    print('FAIL' if failed else 'OK')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
