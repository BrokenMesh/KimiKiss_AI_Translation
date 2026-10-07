#!/usr/bin/env python3
"""Deterministic compliance pass for translations (plan Phase 5, step 3). No model calls.

Usage: check_translation.py <text_dir> [--files NAME ...] [--json out.json] [-v] [--trans DIR]
           [--glossary PATH] [--limits PATH] [--allow-chars STR] [--whitelist FILE]
           [--no-wrap] [--require-all] [--strict]

Japanese comes from <text_dir> (text/*.json, local), the English from the translation store
(--trans DIR, default translation/en, tools/translate/store.py; 'none' = only "translation" fields
found in <text_dir>). Checks every record that has a translation (records without one are only counted):
  a  control codes      same codes as the Japanese (D-006 lets a translator move whole tokens, so a
                        different order is a warning), except that the relative order of codes of one
                        family (V voice, E eyes, F face, M mouth, T timing, ...) must be kept; a leading
                        {Ti..} must stay first; braces must balance
  b  Japanese left over kana, kanji, full-width characters outside braces (allowed: the line break U+FF0F,
                        U+FF5C, U+3000 and --allow-chars / --whitelist)
  c  fit                dialogue: text wrapped as the build does (en_text.wrap with the speaker label and
                        indent rule) must take <= 3 lines; choices: one line each, same count; ConfirmDialog:
                        each \\n line <= 576 px; other system text: limits.json max_px; runtime
                        concatenations (topic message, memory card status + message)
  d  glossary           the English of a glossary term must appear when its Japanese does (warning)
  e  encodable          characters with no English glyph and no Japanese meaning (accents, curly quotes ...)
  f  suspicious         empty, untranslated copy, double spaces, unbalanced quotes / brackets
  g  source hash        SRC_STALE (warning): the hash in the store header differs from the current
                        Japanese, so the line was written against another Japanese text

Per record: PASS, WARN (passes, has warnings) or FAIL. Exit status 1 when any record FAILs
(--strict: also on WARN; --require-all: records without translation FAIL).
Widths are in pixels of the English width table (tools/font/en_widths.json), at the scale of the
consumer (ConfirmDialog 0.75).
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'translate'))
import rules  # noqa: E402
import store  # noqa: E402

BREAK = rules.BREAK
# Codes whose order relative to each other is free: waits are plain delays and the name tokens may
# swap places ({Nn} {Nm} in Western order).
FREE_ORDER_FAMILIES = ('W', 'N')


class Result:
    def __init__(self, rec, lim):
        self.rec = rec
        self.lim = lim
        self.items = []  # (level, code, message)
        self.info = {}

    def fail(self, code, msg):
        self.items.append(('FAIL', code, msg))

    def warn(self, code, msg):
        self.items.append(('WARN', code, msg))

    @property
    def status(self):
        levels = {i[0] for i in self.items}
        return 'FAIL' if 'FAIL' in levels else 'WARN' if 'WARN' in levels else 'PASS'


class Context:
    def __init__(self, text_dir, limits, terms, allow_chars, allowed_ids, wrap=True, trans_dir=None):
        self.limits = limits
        self.terms = terms
        self.allow = set(rules.DEFAULT_ALLOWED) | set(allow_chars or '')
        self.allowed_ids = allowed_ids
        self.wrap = wrap
        # trans_dir: the translation store merged in (None: translations found in text_dir only)
        self.index = store.merged_index(text_dir, trans_dir) if trans_dir else rules.index_dir(text_dir)
        self.labels = rules.speaker_labels(self.index)

    def prepared(self, rec):
        """The translation as it will be reinserted (wrapped), and its limit."""
        lim = rules.limit_for(rec, self.limits, self.labels)
        text = rec['translation']
        return (rules.prepare_text(text, lim) if self.wrap else text), lim


def family(code):
    return code[:1]


def is_ruby(code):
    return code == 'R' or (code[:1] == 'R' and code[1:].isdigit())


def check_codes(res, ja_codes, tr_codes, orig_text, tr_text):
    # Ruby ({R}base{Rn}reading) is a reading aid for kanji names; English drops it as a whole: when the
    # Japanese has real ruby ({Rn}) and the translation keeps no {R..} code, the ruby codes are not required.
    if any(is_ruby(c) and c != 'R' for c in ja_codes) and not any(is_ruby(c) for c in tr_codes):
        ja_codes = [c for c in ja_codes if not is_ruby(c)]
    miss = collections.Counter(ja_codes) - collections.Counter(tr_codes)
    extra = collections.Counter(tr_codes) - collections.Counter(ja_codes)
    if miss:
        res.fail('CC_MISSING', 'control codes missing: ' + ' '.join('{%s}' % c for c in sorted(miss.elements())))
    if extra:
        res.fail('CC_EXTRA', 'control codes added or changed: ' + ' '.join('{%s}' % c for c in sorted(extra.elements())))
    if miss or extra:
        return
    if ja_codes != tr_codes:
        # same multiset, different order: tokens may move (D-006) unless a family is reordered
        bad = []
        for fam in sorted({family(c) for c in ja_codes} - set(FREE_ORDER_FAMILIES)):
            x = [c for c in ja_codes if family(c) == fam]
            y = [c for c in tr_codes if family(c) == fam]
            if x != y:
                bad.append(f'{fam}: {" ".join(x)} -> {" ".join(y)}')
        if bad:
            res.fail('CC_ORDER', 'codes of one family changed order (' + '; '.join(bad) + ')')
        else:
            res.warn('CC_MOVED', 'control codes moved: ' + ' '.join('{%s}' % c for c in tr_codes))
    # a leading timing prefix selects the text speed of the whole line
    m = re.match(r'\{(Ti\d+)\}', orig_text)
    if m and not tr_text.startswith('{%s}' % m.group(1)):
        res.fail('CC_PREFIX', 'line must start with {%s} like the Japanese' % m.group(1))


def check_braces(res, tr_text):
    depth = 0
    for ch in tr_text:
        if ch == '{':
            depth += 1
            if depth > 1:
                break
        elif ch == '}':
            depth -= 1
            if depth < 0:
                break
    if depth != 0:
        res.fail('CC_BRACE', 'unbalanced or nested braces')
        return False
    return True


def check_chars(res, ctx, rec, tr_text, lim):
    outside = rules.BRACED.sub('', tr_text)
    jp, typo, other, ctrl = [], [], [], []
    allow_choice = lim['kind'] == 'choice'
    for i, ch in enumerate(outside):
        o = ord(ch)
        if ' ' <= ch <= '~':
            continue
        if ch == '\n' and lim['kind'] == 'confirm':
            continue
        if ch in ctx.allow or (allow_choice and ch == '・'):
            continue
        if ch == '\n' or o < 0x20 or o == 0x7F:
            ctrl.append(ch)
        elif ch in rules.TYPOGRAPHY:
            typo.append(ch)
        elif rules.is_japanese(ch):
            jp.append(ch)
        else:
            other.append(ch)
    if jp:
        res.fail('JP_LEFT', 'Japanese or full-width characters left outside braces: ' + ''.join(dict.fromkeys(jp)))
    if typo:
        res.fail('NOT_ENCODABLE', 'no glyph for ' + ' '.join(f'U+{ord(c):04X}' for c in dict.fromkeys(typo)) +
                 ' (typographic; use ASCII: ' + ' '.join(repr(rules.TYPOGRAPHY[c]) for c in dict.fromkeys(typo)) +
                 ' or import --normalize)')
    if other:
        res.fail('NOT_ENCODABLE', 'no glyph for ' + ' '.join(f'U+{ord(c):04X}' for c in dict.fromkeys(other)) +
                 ' (only printable ASCII 0x20-0x7E is available)')
    if ctrl:
        names = ', '.join(sorted({'newline' if c == '\n' else f'U+{ord(c):04X}' for c in ctrl}))
        why = ('the message window drops newlines (use the line break only when a paragraph break is wanted)'
               if lim['kind'] != 'confirm' and '\n' in ctrl else 'control character')
        if lim['kind'] in ('single', 'fragment', 'choice') and '\n' in ctrl:
            why = 'TextLine draws a newline as a glyph; one string is one line'
        res.fail('CONTROL_CHAR', f'{names} not allowed: {why}')
    # ideographic space is a layout blank, fine at the start, odd inside English text
    if '　' in outside.lstrip('　') and '　' not in ctx.allow - set(rules.DEFAULT_ALLOWED):
        res.warn('IDEOGRAPHIC_SPACE', 'U+3000 inside the text (a full-width blank, wider than a space)')


def check_fit(res, ctx, rec, lim, prepared):
    kind = lim['kind']
    if kind == 'skip':
        return
    # system text is not wrapped by the engine: measure what we have
    m = rules.fit(prepared, lim)
    res.info.update(lines_px=[round(p, 1) for p in m['lines']], rows=m['rows'])
    if kind == 'dialogue':
        if m['rows'] > lim['lines']:
            res.fail('FIT_LINES', f'{m["rows"]} lines after wrapping, max {lim["lines"]}'
                     + (f' (a word is wider than the line: {[round(m["lines"][i]) for i in m["overflow"]]} px)'
                        if m['overflow'] else '')
                     + f'; line px {[round(p) for p in m["lines"]]}')
        elif m['overflow']:
            res.warn('FIT_WORD', 'a single word is wider than the line; the engine will break it mid-word '
                     f'(line px {[round(m["lines"][i]) for i in m["overflow"]]} > {lim["cont_px"]})')
        res.info['wrapped'] = prepared
        return
    if kind == 'choice':
        want = lim['choices']
        n = len(prepared.split(BREAK))
        if n != want:
            res.fail('CHOICE_COUNT', f'{n} choice(s), the Japanese has {want}; the break separates choices')
        for i, p in enumerate(m['lines']):
            if p > lim['max_px']:
                res.fail('FIT_PX', f'choice {i + 1} is {p:.0f} px, max {lim["max_px"]}')
        return
    # confirm / single / fragment
    if kind == 'confirm':
        n = len(m['lines'])
        if n > lim['lines']:
            res.fail('FIT_LINES', f'{n} lines, max {lim["lines"]}')
    elif len(m['lines']) > 1:
        res.fail('FIT_LINES', 'line break in a one-line string (it would be drawn as a glyph or break the layout)')
    for i, p in enumerate(m['lines']):
        if p > lim['max_px']:
            soft = rec['id'] in TOPIC_IDS
            (res.warn if soft else res.fail)(
                'FIT_PX', f'line {i + 1} is {p:.0f} px, max {lim["max_px"]}' + (' (budget; the sum below is the hard limit)' if soft else ''))
    if kind == 'single' and BREAK in prepared and BREAK not in rec['text']:
        res.warn('FIT_BREAK', 'line break in a single-line string')


TOPIC_IDS = {'K2_Script:240', 'K2_Script:241'}
TOPIC_PREFIX = 'WadaiTable:'
MEMCARD_STATUS = ['MemoryCard:11.1', 'MemoryCard:11.2', 'MemoryCard:11.3', 'MemoryCard:11.5']
MEMCARD_CHECK = 'MemoryCardCheck:9.19'


def px_of_translation(ctx, rid, display='TextWindow'):
    r = ctx.index.get(rid)
    if r and r.get('translation'):
        return rules.text_px(r['translation'], display)
    return None


def n_lines(ctx, rid, own_id, own_text):
    """Line count of a ConfirmDialog message: the translation if there is one, else the Japanese."""
    if rid == own_id:
        return len(rules.split_lines(own_text, 'confirm'))
    r = ctx.index.get(rid)
    return len(rules.split_lines(r.get('translation') or r['text'], 'confirm')) if r else 0


def check_composites(res, ctx, rec):
    rid, tr = rec['id'], rec['translation']
    if rid in TOPIC_IDS or rid.startswith(TOPIC_PREFIX):
        p240 = px_of_translation(ctx, 'K2_Script:240')
        p241 = px_of_translation(ctx, 'K2_Script:241')
        own = rules.text_px(tr, 'TextWindow')
        if rid.startswith(TOPIC_PREFIX):
            # unknown neighbours count at their limits.json budget
            a, t, b = (200 if p240 is None else p240), own, (100 if p241 is None else p241)
        else:
            topics = [px_of_translation(ctx, k) for k in ctx.index if k.startswith(TOPIC_PREFIX)]
            t = max([x for x in topics if x is not None], default=0)
            a = own if rid == 'K2_Script:240' else (p240 or 0)
            b = own if rid == 'K2_Script:241' else (p241 or 0)
        total = a + t + b
        res.info['topic_sum_px'] = round(total, 1)
        if total > en_text_line_px():
            res.fail('FIT_COMPOSITE', f'topic message = {a:.0f} + topic {t:.0f} + {b:.0f} = {total:.0f} px, max '
                     f'{en_text_line_px()} (one runtime string on one line, no break possible)')
    if rid == MEMCARD_CHECK or rid in MEMCARD_STATUS:
        status = max(n_lines(ctx, i, rid, tr) for i in MEMCARD_STATUS)
        msg = n_lines(ctx, MEMCARD_CHECK, rid, tr)
        total = status + 2 + msg
        res.info['memcard_lines'] = total
        if total > 14:
            res.fail('FIT_COMPOSITE', f'status ({status} lines) + 2 blank + message ({msg} lines) = {total}, max 14 '
                     '(MemoryCardCheck shows status, a blank line and this text together)')


def en_text_line_px():
    return rules.en_text.LINE_PX


def check_glossary(res, ctx, rec):
    low = rec['translation'].lower()
    for t in rules.glossary_hits(rec['text'], ctx.terms):
        if not any(v.lower() in low for v in t['variants']):
            res.warn('GLOSSARY', f'"{t["ja"]}" should appear as "{t["en"]}"' + (f' ({t["note"]})' if t['note'] else ''))


def check_suspicious(res, rec, tr, lim):
    plain = rules.BRACED.sub('', tr)
    if plain.strip(' 　') == '' and rules.BRACED.sub('', rec['text']).strip(' 　') != '':
        res.warn('NO_TEXT', 'translation has no text outside control codes')
    if tr == rec['text'] or plain == rules.BRACED.sub('', rec['text']):
        res.fail('UNTRANSLATED', 'translation is identical to the Japanese')
    if '  ' in plain:
        res.warn('DOUBLE_SPACE', 'double space')
    if tr != tr.strip(' ') and lim['kind'] not in ('fragment', 'single'):
        res.warn('EDGE_SPACE', 'leading or trailing space')
    if plain.count('"') % 2:
        res.warn('QUOTES', 'odd number of double quotes')
    for o, c in (('(', ')'), ('[', ']')):
        if plain.count(o) != plain.count(c) and lim['kind'] != 'fragment':
            res.warn('BRACKETS', f'unbalanced {o}{c}')
    ja = rules.BRACED.sub('', rec['text'])
    if any(rules.is_japanese(c) for c in ja) and not re.search(r'[A-Za-z]', plain) and not any(
            t in rec['translation'] for t in rules.NAME_TOKENS):
        res.warn('NO_LETTERS', 'no letters in the translation')


def check_record(rec, ctx):
    tr = rec.get('translation')
    lim = rules.limit_for(rec, ctx.limits, ctx.labels)
    res = Result(rec, lim)
    if lim['kind'] == 'skip':
        res.fail('TRANSLATE_FALSE', f'limits.json: translate=false ({lim["display"]}); would change non-display text')
        return res
    if not isinstance(tr, str) or not tr.strip():
        res.fail('EMPTY', 'empty translation')
        return res
    src = rec.get('_src')
    if src and src != store.src_hash(rec['text']):
        res.warn('SRC_STALE', f'the store header says this line was written against Japanese {src}, '
                 f'which is now {store.src_hash(rec["text"])}; check the English, then sync --accept-src')
    if not check_braces(res, tr):
        return res
    check_codes(res, rec['control_codes'], rules.brace_tokens(tr), rec['text'], tr)
    if rec['id'] not in ctx.allowed_ids:
        check_chars(res, ctx, rec, tr, lim)
    prepared = rules.prepare_text(tr, lim) if ctx.wrap else tr
    check_fit(res, ctx, rec, lim, prepared)
    check_composites(res, ctx, rec)
    check_glossary(res, ctx, rec)
    check_suspicious(res, rec, tr, lim)
    if lim.get('unknown'):
        res.warn('NO_LIMIT', 'system record without a limits.json entry; measured against 576 px, one line')
    return res


def load_whitelist(path):
    if not path:
        return '', set()
    d = rules.load_json(path)
    return d.get('chars', ''), set(d.get('ids', []))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('text_dir')
    ap.add_argument('--trans', help='translation store directory (default translation/en; "none" = no store)')
    ap.add_argument('--files', nargs='+', help='scene names, file names, paths or globs (default: all)')
    ap.add_argument('--json', help='write the full report here')
    ap.add_argument('--glossary')
    ap.add_argument('--limits')
    ap.add_argument('--allow-chars', default='', help='extra characters allowed outside braces')
    ap.add_argument('--whitelist', help='JSON {"chars": "...", "ids": ["ID", ...]}: allowed characters; ids skip the character checks')
    ap.add_argument('--no-wrap', action='store_true', help='measure the translation as written (no automatic wrapping)')
    ap.add_argument('--require-all', action='store_true', help='records without translation FAIL')
    ap.add_argument('--strict', action='store_true', help='WARN also gives exit status 1')
    ap.add_argument('-v', '--verbose', action='store_true', help='print PASS lines too')
    a = ap.parse_args()

    wl_chars, wl_ids = load_whitelist(a.whitelist)
    limits = rules.load_limits(a.limits)
    terms = rules.load_glossary(a.glossary)
    tdir = store.DEFAULT_DIR if a.trans is None else (None if a.trans.lower() == 'none' else a.trans)
    ctx = Context(a.text_dir, limits, terms, a.allow_chars + wl_chars, wl_ids, wrap=not a.no_wrap,
                  trans_dir=tdir or None)
    paths = rules.resolve_files(a.text_dir, a.files)
    merged = store.merge(a.text_dir, tdir)
    if not terms:
        print('note: no glossary loaded; glossary check skipped', file=sys.stderr)

    counts = collections.Counter()
    codes = collections.Counter()
    report = []
    untranslated = skipped = 0
    for p in paths:
        for rec in merged[store.scene_of(p)]:
            lim0 = rules.limit_for(rec, limits, ctx.labels)
            if not rec.get('translation') and rec.get('translation') != '':
                if lim0['kind'] == 'skip':
                    skipped += 1
                elif a.require_all:
                    counts['FAIL'] += 1
                    codes['MISSING'] += 1
                    report.append({'id': rec['id'], 'status': 'FAIL', 'reasons': [
                        {'level': 'FAIL', 'code': 'MISSING', 'msg': 'no translation'}]})
                    print(f'FAIL  {rec["id"]}  MISSING: no translation')
                else:
                    untranslated += 1
                continue
            res = check_record(rec, ctx)
            counts[res.status] += 1
            for lv, code, _ in res.items:
                codes[f'{lv}:{code}'] += 1
            entry = {'id': rec['id'], 'file': os.path.basename(p), 'status': res.status, 'kind': res.lim['kind'],
                     'speaker': rec.get('speaker'),
                     'reasons': [{'level': lv, 'code': c, 'msg': m} for lv, c, m in res.items]}
            entry.update(res.info)
            if res.status != 'PASS':
                entry['ja'] = rec['text']
                entry['en'] = rec['translation']
            report.append(entry)
            if res.status != 'PASS' or a.verbose:
                print(f'{res.status:<5} {rec["id"]}  [{res.lim["kind"]}]')
                for lv, c, m in res.items:
                    print(f'        {lv} {c}: {m}')
    checked = counts['PASS'] + counts['WARN'] + counts['FAIL'] - codes['MISSING']
    print()
    print(f'checked {checked}: PASS {counts["PASS"]}, WARN {counts["WARN"]}, FAIL {counts["FAIL"]}'
          f' | no translation yet {untranslated}, translate=false {skipped} | {len(paths)} file(s)')
    if codes:
        print('flags: ' + ', '.join(f'{k} {v}' for k, v in sorted(codes.items())))
    if a.json:
        summary = {'PASS': counts['PASS'], 'WARN': counts['WARN'], 'FAIL': counts['FAIL'],
                   'untranslated': untranslated, 'translate_false': skipped, 'flags': dict(codes)}
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump({'summary': summary, 'results': report}, f, ensure_ascii=False, indent=1)
    sys.exit(1 if counts['FAIL'] or (a.strict and counts['WARN']) else 0)


if __name__ == '__main__':
    main()
