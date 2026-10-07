#!/usr/bin/env python3
"""Unit tests for tools/qa/check_translation.py and tools/translate/batch.py.

Usage: test_check_translation.py

Every string here is invented; no game text is used. A small text directory (Japanese) and a
translation store (English) are built in a temporary folder with a hand-written limits table and
glossary. Store format and sync tests are in test_translation_store.py.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TOOLS, 'translate'))
import check_translation as ct  # noqa: E402
import rules  # noqa: E402
import store  # noqa: E402

BATCH = os.path.join(TOOLS, 'translate', 'batch.py')
CHECK = os.path.join(HERE, 'check_translation.py')

LIMITS = {
    'Sys:1': {'display': 'ConfirmDialog', 'max_px': 576, 'lines': 4, 'translate': True, 'note': ''},
    'Sys:2': {'display': 'TextLine', 'max_px': 200, 'lines': 1, 'translate': True, 'note': ''},
    'Sys:3': {'display': 'TextWindow', 'max_px': 92, 'lines': 1, 'translate': True, 'note': 'label'},
    'Sys:4': {'display': 'debug-console', 'max_px': None, 'lines': 0, 'translate': False, 'note': ''},
    'Sys:5': {'display': 'TextWindow', 'max_px': 552, 'lines': 2, 'translate': True, 'note': 'Exactly 2 lines.'},
    'K2_Script:240': {'display': 'TextWindow', 'max_px': 200, 'lines': 1, 'translate': True, 'note': ''},
    'K2_Script:241': {'display': 'TextWindow', 'max_px': 100, 'lines': 1, 'translate': True, 'note': ''},
    'WadaiTable:0.0': {'display': 'TextWindow', 'max_px': 250, 'lines': 1, 'translate': True, 'note': ''},
    'MemoryCard:11.1': {'display': 'ConfirmDialog', 'max_px': 576, 'lines': 5, 'translate': True, 'note': ''},
    'MemoryCardCheck:9.19': {'display': 'ConfirmDialog', 'max_px': 576, 'lines': 8, 'translate': True, 'note': ''},
}
GLOSSARY = {'terms': [
    {'ja': '山田', 'en': 'Yamada', 'kind': 'name', 'note': 'family name'},
    {'ja': 'さん', 'en': '-san', 'kind': 'honorific', 'note': ''},
    {'ja': '魔法使い', 'en': 'wizard|sorcerer', 'kind': 'term', 'note': ''},
], 'policy': {}}


def mk(id_, text, speaker='YUM', route='YUM', translation=None):
    codes = rules.brace_tokens(text)
    r = {'file': 'X.scf', 'offset': 0, 'id': id_, 'speaker': speaker, 'text': text, 'control_codes': codes,
         'byte_budget': 0, 'route': route, 'context_prev': None, 'context_next': None}
    if translation is not None:
        r['translation'] = translation
    return r


def sysrec(id_, text, translation=None, speaker=None):
    return mk(id_, text, speaker=speaker, route='system', translation=translation)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.limits_path = os.path.join(self.dir, 'limits.json')
        self.gloss_path = os.path.join(self.dir, 'glossary.json')
        with open(self.limits_path, 'w') as f:
            json.dump(LIMITS, f)
        with open(self.gloss_path, 'w', encoding='utf-8') as f:
            json.dump(GLOSSARY, f, ensure_ascii=False)
        self.text = os.path.join(self.dir, 'text')
        self.trans = os.path.join(self.dir, 'en')   # never the repo's translation/en
        os.makedirs(self.text)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, recs):
        with open(os.path.join(self.text, name + '.json'), 'w', encoding='utf-8') as f:
            json.dump(recs, f, ensure_ascii=False, indent=1)

    def write_split(self, name, recs):
        """Japanese into text/, the 'translation' fields into the store (as the real flow keeps them)."""
        plain = [{k: v for k, v in r.items() if k != 'translation'} for r in recs]
        self.write(name, plain)
        f, _ = store.sync_scene(name, plain, None, LIMITS)
        by = f.by_id()
        for r in recs:
            if r.get('translation') and r['id'] in by:
                by[r['id']].tr = r['translation']
        store.write_scene(store.scene_path(self.trans, name), f)

    def ctx(self, **kw):
        return ct.Context(self.text, LIMITS, rules.load_glossary(self.gloss_path), kw.get('allow', ''), set(),
                          wrap=kw.get('wrap', True))

    def run_check(self, rec, **kw):
        self.write('Scene', [rec])
        return ct.check_record(rec, self.ctx(**kw))

    def codes(self, res):
        return {c for _, c, _ in res.items}

    def levels(self, res):
        return {(lv, c) for lv, c, _ in res.items}


class ControlCodes(Base):
    JA = '「{V0858}あのね、{W30}聞いて。{Ec}{W15}」'

    def test_identical(self):
        r = self.run_check(mk('Scene:1', self.JA, translation='"{V0858}Listen, {W30}okay. {Ec}{W15}"'))
        self.assertEqual(r.status, 'PASS', r.items)

    def test_missing_and_extra(self):
        r = self.run_check(mk('Scene:1', self.JA, translation='"{V0858}Listen, {W30}okay."'))
        self.assertIn(('FAIL', 'CC_MISSING'), self.levels(r))
        r = self.run_check(mk('Scene:1', self.JA, translation='"{V0858}Listen, {W31}okay. {Ec}{W15}"'))
        self.assertIn(('FAIL', 'CC_EXTRA'), self.levels(r))
        self.assertIn(('FAIL', 'CC_MISSING'), self.levels(r))  # {W30} is gone

    def test_moved_wait_is_allowed(self):
        r = self.run_check(mk('Scene:1', self.JA, translation='"{V0858}Listen,{W15} okay. {Ec}{W30}"'))
        self.assertEqual(self.levels(r), {('WARN', 'CC_MOVED')})

    def test_family_reorder_fails(self):
        ja = '{Ec}あ{Eo}い'
        r = self.run_check(mk('Scene:1', ja, translation='{Eo}a {Ec}b'))
        self.assertIn(('FAIL', 'CC_ORDER'), self.levels(r))

    def test_name_tokens_may_swap(self):
        ja = '「{Nm}{Nn}さん」'
        r = self.run_check(mk('Scene:1', ja, translation='"{Nn} {Nm}"'))
        self.assertEqual(self.levels(r), {('WARN', 'CC_MOVED')})

    def test_leading_prefix(self):
        r = self.run_check(mk('Scene:1', '{Ti0}あい', translation='x {Ti0}'))
        self.assertIn(('FAIL', 'CC_PREFIX'), self.levels(r))

    def test_unbalanced_braces(self):
        r = self.run_check(mk('Scene:1', '{W15}あ', translation='{W15 hello'))
        self.assertIn(('FAIL', 'CC_BRACE'), self.levels(r))


class Characters(Base):
    def test_kana_left(self):
        r = self.run_check(mk('Scene:1', 'あい', translation='Hello ありがとう'))
        self.assertIn(('FAIL', 'JP_LEFT'), self.levels(r))

    def test_braces_are_not_japanese(self):
        r = self.run_check(mk('Scene:1', '{W15}あい', translation='Hello {W15}'))
        self.assertEqual(r.status, 'PASS', r.items)

    def test_break_allowed_other_fullwidth_not(self):
        r = self.run_check(mk('Scene:1', 'あい', translation='One／two'))
        self.assertEqual(r.status, 'PASS', r.items)
        r = self.run_check(mk('Scene:1', 'あい', translation='Fullwidth Ａ'))
        self.assertIn(('FAIL', 'JP_LEFT'), self.levels(r))

    def test_allow_chars(self):
        rec = mk('Scene:1', 'あい', translation='Cheers ★')
        self.write('Scene', [rec])
        self.assertIn(('FAIL', 'JP_LEFT'), self.levels(ct.check_record(rec, self.ctx())))
        self.assertEqual(ct.check_record(rec, self.ctx(allow='★')).status, 'PASS')

    def test_not_encodable(self):
        for text in ('Café time', 'He said “hi”', 'Wait…', 'Tab\there'):
            r = self.run_check(mk('Scene:1', 'あい', translation=text))
            self.assertEqual(r.status, 'FAIL', text)
            self.assertTrue(self.codes(r) & {'NOT_ENCODABLE', 'CONTROL_CHAR'}, text)

    def test_newline_rules(self):
        r = self.run_check(mk('Scene:1', 'あい', translation='one\ntwo'))
        self.assertIn(('FAIL', 'CONTROL_CHAR'), self.levels(r))
        r = self.run_check(sysrec('Sys:1', 'あ\nい', translation='one\ntwo'))
        self.assertEqual(r.status, 'PASS', r.items)

    def test_normalize_typography(self):
        self.assertEqual(rules.normalize_typography('“Hi” — it’s…'), '"Hi" -- it\'s...')


class Fit(Base):
    def words(self, n, word='wonder'):
        return ' '.join([word] * n)

    def test_short_line(self):
        r = self.run_check(mk('Scene:1', 'あ', translation='A short line.', speaker='SYS'))
        self.assertEqual(r.status, 'PASS', r.items)

    def test_three_lines_ok_four_fail(self):
        lim = rules.dialogue_limit('SYS', {})
        n = 1
        while rules.fit(rules.prepare_text(self.words(n), lim), lim)['rows'] <= 3:
            n += 1
        self.assertTrue(self.run_check(mk('Scene:1', 'あ', translation=self.words(n - 1), speaker='SYS')).status != 'FAIL')
        r = self.run_check(mk('Scene:1', 'あ', translation=self.words(n), speaker='SYS'))
        self.assertIn(('FAIL', 'FIT_LINES'), self.levels(r))

    def test_speaker_indent_costs_room(self):
        narr = rules.dialogue_limit('SYS', {})
        spk = rules.dialogue_limit('YUM', {})
        self.assertEqual((narr['first_px'], narr['cont_px']), (552, 552))
        self.assertEqual(spk['cont_px'], 552 - 115)
        # a text that fits three narration lines but not three speaker lines
        n = 1
        while True:
            t = self.words(n)
            a = rules.fit(rules.prepare_text(t, narr), narr)['rows']
            b = rules.fit(rules.prepare_text(t, spk), spk)['rows']
            if b > 3:
                break
            n += 1
        self.assertLessEqual(a, 3)
        self.assertEqual(self.run_check(mk('Scene:1', 'あ', translation=t, speaker='SYS')).status, 'PASS')
        self.assertIn(('FAIL', 'FIT_LINES'), self.levels(self.run_check(mk('Scene:1', 'あ', translation=t, speaker='YUM'))))

    def test_label_translation_changes_first_line(self):
        labels = {'YUM': 'Yumi'}
        # D-023: line 1 starts at the indent column, or a gap after a wider plate
        self.assertEqual(rules.dialogue_limit('YUM', labels)['first_px'], 552 - 115)
        wide = {'YUM': 'Kobayakawa Kobayakawa'}
        self.assertEqual(rules.dialogue_limit('YUM', wide)['first_px'],
                         552 - rules.text_px(wide['YUM']) - rules.en_text.PLATE_GAP_PX)
        # PLY label is the player's name at run time
        self.assertEqual(rules.dialogue_limit('PLY', {'PLY': 'A'})['label_px'],
                         rules.en_text.NAME_PX + rules.en_text.PLATE_GAP_PX)

    def test_ruby_may_be_dropped_whole(self):
        ja = '「{V5001}{R}柊{R4}ひいらぎだよ」'
        ok = self.run_check(mk('Scene:1', ja, translation='"{V5001}It\'s Hiiragi."', speaker='AKI'))
        self.assertNotIn('CC_MISSING', [c for _, c in self.levels(ok)])
        half = self.run_check(mk('Scene:1', ja, translation='"{V5001}{R}It\'s Hiiragi."', speaker='AKI'))
        self.assertIn(('FAIL', 'CC_MISSING'), self.levels(half))

    def test_name_token_width(self):
        self.assertEqual(rules.text_px('{Nm}'), rules.en_text.NAME_PX)
        self.assertEqual(rules.text_px('{W30}'), 0)

    def test_unbreakable_word_warns(self):
        r = self.run_check(mk('Scene:1', 'あ', translation='W' * 40))
        self.assertIn(('WARN', 'FIT_WORD'), self.levels(r))

    def test_confirm_dialog(self):
        long_line = ' '.join(['wonder'] * 30)
        # auto-wrapped when prepared, so it fits; with --no-wrap the single line is too wide
        self.assertEqual(self.run_check(sysrec('Sys:1', 'あ', translation=long_line)).status, 'PASS')
        r = self.run_check(sysrec('Sys:1', 'あ', translation=long_line), wrap=False)
        self.assertIn(('FAIL', 'FIT_PX'), self.levels(r))
        r = self.run_check(sysrec('Sys:1', 'あ', translation='a\nb\nc\nd\ne'))
        self.assertIn(('FAIL', 'FIT_LINES'), self.levels(r))
        # scale 0.75: a line that is too wide at 1.0 may fit a dialog
        t = 'W' * 30
        self.assertGreater(rules.text_px(t, 'TextWindow'), 576)
        self.assertLessEqual(rules.text_px(t, 'ConfirmDialog'), 576)
        self.assertEqual(self.run_check(sysrec('Sys:1', 'あ', translation=t)).status, 'PASS')

    def test_single_line_limits(self):
        r = self.run_check(sysrec('Sys:2', 'あ', translation='W' * 20))
        self.assertIn(('FAIL', 'FIT_PX'), self.levels(r))
        r = self.run_check(sysrec('Sys:2', 'あ', translation='two\nlines'))
        self.assertIn(('FAIL', 'CONTROL_CHAR'), self.levels(r))
        r = self.run_check(sysrec('Sys:3', 'あ', translation='Extremely long label'))
        self.assertIn(('FAIL', 'FIT_PX'), self.levels(r))
        self.assertEqual(self.run_check(sysrec('Sys:3', 'あ', translation='Yumi')).status, 'PASS')

    def test_choices(self):
        ja = '{Ti0}・あ／・い／・う'
        rec = mk('Scene:7.1', ja, speaker=None, route='YUM', translation='{Ti0}- one/two')
        self.assertIn(('FAIL', 'CHOICE_COUNT'), self.levels(self.run_check(rec)))
        rec = mk('Scene:7.1', ja, speaker=None, route='YUM', translation='{Ti0}- one／- two／- three')
        self.assertEqual(self.run_check(rec).status, 'PASS')
        # the original bullet is accepted in choices only
        rec = mk('Scene:7.1', ja, speaker=None, route='YUM', translation='{Ti0}・one／・two／・three')
        self.assertEqual(self.run_check(rec).status, 'PASS')
        rec = mk('Scene:8', 'あ', translation='・bullet')
        self.assertIn(('FAIL', 'JP_LEFT'), self.levels(self.run_check(rec)))
        long = ' '.join(['wonder'] * 12)
        rec = mk('Scene:7.1', ja, speaker=None, route='YUM', translation='{Ti0}' + long + '／b／c')
        self.assertIn(('FAIL', 'FIT_PX'), self.levels(self.run_check(rec)))

    def test_two_line_choice_from_limits(self):
        rec = sysrec('Sys:5', 'あ／い', translation='one')
        self.assertIn(('FAIL', 'CHOICE_COUNT'), self.levels(self.run_check(rec)))
        self.assertEqual(self.run_check(sysrec('Sys:5', 'あ／い', translation='one／two')).status, 'PASS')

    def test_topic_message_sum(self):
        self.write('K2_Script', [sysrec('K2_Script:240', 'あ', translation='W' * 13),
                                 sysrec('K2_Script:241', 'い', translation='obtained')])
        topic = sysrec('WadaiTable:0.0', 'う', translation='Q' * 16)
        self.write('WadaiTable', [topic])
        r = ct.check_record(topic, self.ctx())
        self.assertIn(('FAIL', 'FIT_COMPOSITE'), self.levels(r))
        topic['translation'] = 'Short'
        self.write('WadaiTable', [topic])
        self.assertEqual(ct.check_record(topic, self.ctx()).status, 'PASS')

    def test_memory_card_message_lines(self):
        status = sysrec('MemoryCard:11.1', 'あ', translation='a\nb\nc\nd\ne')
        check = sysrec('MemoryCardCheck:9.19', 'い', translation='a\nb\nc\nd\ne\nf\ng\nh')
        self.write('MemoryCard', [status])
        self.write('MemoryCardCheck', [check])
        self.assertIn(('FAIL', 'FIT_COMPOSITE'), self.levels(ct.check_record(check, self.ctx())))
        check['translation'] = 'a\nb\nc\nd\ne\nf\ng'
        self.write('MemoryCardCheck', [check])
        self.assertEqual(ct.check_record(check, self.ctx()).status, 'PASS')


class Misc(Base):
    def test_glossary(self):
        ja = '山田さんは魔法使い'
        r = self.run_check(mk('Scene:1', ja, translation='Mr. Tanaka is a wizard'))
        self.assertEqual(self.levels(r), {('WARN', 'GLOSSARY')})
        r = self.run_check(mk('Scene:1', ja, translation='YAMADA is a Sorcerer'))
        self.assertEqual(r.status, 'PASS', r.items)

    def test_glossary_missing_file(self):
        self.assertEqual(rules.load_glossary(os.path.join(self.dir, 'nope.json')), [])
        bad = os.path.join(self.dir, 'bad.json')
        with open(bad, 'w') as f:
            f.write('{not json')
        self.assertEqual(rules.load_glossary(bad), [])

    def test_suspicious(self):
        self.assertIn(('FAIL', 'EMPTY'), self.levels(self.run_check(mk('Scene:1', 'あ', translation='  '))))
        self.assertIn(('FAIL', 'UNTRANSLATED'), self.levels(self.run_check(mk('Scene:1', 'abc', translation='abc'))))
        self.assertIn(('WARN', 'DOUBLE_SPACE'), self.levels(self.run_check(mk('Scene:1', 'あ', translation='a  b'))))
        self.assertIn(('WARN', 'QUOTES'), self.levels(self.run_check(mk('Scene:1', 'あ', translation='"a'))))
        self.assertIn(('WARN', 'BRACKETS'), self.levels(self.run_check(mk('Scene:1', 'あ', translation='(a'))))
        self.assertIn(('WARN', 'NO_LETTERS'), self.levels(self.run_check(mk('Scene:1', 'あ', translation='...'))))

    def test_translate_false(self):
        r = self.run_check(sysrec('Sys:4', 'あ', translation='x'))
        self.assertIn(('FAIL', 'TRANSLATE_FALSE'), self.levels(r))

    def test_wrap_prepare(self):
        lim = rules.dialogue_limit('SYS', {})
        text = ' '.join(['wonder'] * 20)
        wrapped = rules.prepare_text(text, lim)
        self.assertIn(rules.BREAK, wrapped)
        self.assertEqual(wrapped.replace(rules.BREAK, ' '), text)
        # choices and labels are never wrapped
        self.assertEqual(rules.prepare_text(text, {'kind': 'choice'}), text)


class Cli(Base):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, *args], capture_output=True, text=True)

    def test_check_exit_codes_and_json(self):
        self.write_split('Scene', [mk('Scene:1', 'あ', translation='Fine.'), mk('Scene:2', 'い'),
                                   sysrec('Sys:4', 'う')])
        out = os.path.join(self.dir, 'r.json')
        args = [CHECK, self.text, '--trans', self.trans, '--limits', self.limits_path,
                '--glossary', self.gloss_path, '--json', out]
        p = self.run_cli(*args)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn('PASS 1', p.stdout)
        self.assertEqual(self.run_cli(*args, '--require-all').returncode, 1)
        self.write_split('Scene', [mk('Scene:1', 'あ', translation='Bad ありがとう')])
        p = self.run_cli(*args)
        self.assertEqual(p.returncode, 1)
        with open(out, encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data['summary']['FAIL'], 1)
        self.assertEqual(data['results'][0]['reasons'][0]['code'], 'JP_LEFT')

    def test_files_filter(self):
        self.write_split('Aaa', [mk('Aaa:1', 'あ', translation='Fine.')])
        self.write_split('Bbb', [mk('Bbb:1', 'あ', translation='Bad ありがとう')])
        base = [CHECK, self.text, '--trans', self.trans, '--limits', self.limits_path, '--glossary', self.gloss_path]
        self.assertEqual(self.run_cli(*base, '--files', 'Aaa').returncode, 0)
        self.assertEqual(self.run_cli(*base, '--files', 'Bbb.json').returncode, 1)


class Batch(Base):
    def setUp(self):
        super().setUp()
        self.write_split('Scene', [mk('Scene:1', '山田「{V0001}おはよう」'), mk('Scene:2', '「うん」', speaker='ASU'),
                             mk('Scene:3', '「{W15}ああ」', translation='Existing.'),
                             mk('Scene:4.1', '{Ti0}・あ／・い', speaker=None),
                             sysrec('Sys:4', 'debug'), sysrec('Sys:1', 'メッセージ')])

    def batch(self, *args):
        return subprocess.run([sys.executable, BATCH, *args, '--trans', self.trans], capture_output=True, text=True)

    def read_json(self):
        with open(os.path.join(self.text, 'Scene.json'), encoding='utf-8') as f:
            return json.load(f)

    def read_store(self):
        """{id: English} of the store file (empty string = untranslated)."""
        return {e.id: e.tr for e in store.load_scene(store.scene_path(self.trans, 'Scene')).entries}

    def test_export_fields_and_skips(self):
        out = os.path.join(self.dir, 'b.jsonl')
        p = self.batch('export', self.text, 'Scene', out, '--limits', self.limits_path, '--glossary', self.gloss_path,
                       '--context', '1')
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(out, encoding='utf-8') as f:
            rows = [json.loads(l) for l in f]
        self.assertEqual([r['id'] for r in rows], ['Scene:1', 'Scene:2', 'Scene:4.1', 'Sys:1'])
        first = rows[0]
        for key in ('id', 'scene', 'speaker', 'ja', 'control_codes', 'prev', 'next', 'limit', 'glossary'):
            self.assertIn(key, first)
        self.assertEqual(first['control_codes'], ['V0001'])
        self.assertEqual(first['glossary'][0]['en'], 'Yamada')
        self.assertEqual(first['limit']['kind'], 'dialogue')
        self.assertEqual(first['next'][0]['id'], 'Scene:2')
        self.assertEqual(rows[1]['next'][0]['en'], 'Existing.')   # neighbours carry finished translations
        self.assertEqual(rows[2]['limit']['kind'], 'choice')
        self.assertEqual(rows[3]['limit']['kind'], 'confirm')
        self.assertEqual(rows[3]['limit']['max_px'], 576)

    def test_export_compact_text(self):
        out = os.path.join(self.dir, 'b.txt')
        p = self.batch('export', self.text, 'Scene', out, '--limits', self.limits_path, '--glossary', self.gloss_path,
                       '--format', 'text')
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(out, encoding='utf-8') as f:
            lines = f.read().splitlines()
        body = [l for l in lines if not l.startswith('#')]
        self.assertTrue(lines[0].startswith('# scene Scene'))
        self.assertTrue(any(l.startswith('# glossary: \u5c71\u7530 = Yamada') for l in lines))
        self.assertEqual(body[0], 'Scene:1 YUM \u5c71\u7530\u300c{V0001}\u304a\u306f\u3088\u3046\u300d')  # dialogue: no tag
        self.assertIn('~Scene:3 YUM \u300c{W15}\u3042\u3042\u300d', body)    # translated: context, no tag
        self.assertIn('  = Existing.', body)
        self.assertTrue(any(l.startswith('Scene:4.1 - [choice x2') for l in body))
        self.assertTrue(any(l.startswith('Sys:1 - [dialog box') for l in body))
        self.assertFalse(any('Sys:4' in l for l in body))                      # translate=false left out

    def test_export_tolerates_missing_glossary(self):
        out = os.path.join(self.dir, 'b.jsonl')
        p = self.batch('export', self.text, 'Scene', out, '--limits', self.limits_path,
                       '--glossary', os.path.join(self.dir, 'none.json'))
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(out, encoding='utf-8') as f:
            self.assertEqual(json.loads(f.readline())['glossary'], [])

    def test_import_roundtrip_and_refusals(self):
        inp = os.path.join(self.dir, 'in.jsonl')

        def put(rows):
            with open(inp, 'w', encoding='utf-8') as f:
                f.write('\n'.join(json.dumps(r) for r in rows) + '\n')
        args = ['--limits', self.limits_path]
        put([{'id': 'Scene:1', 'translation': 'Hello.'}, {'id': 'Scene:2', 'translation': None}])
        self.assertEqual(self.batch('import', self.text, inp, *args).returncode, 0)
        recs = self.read_store()
        self.assertEqual(recs['Scene:1'], 'Hello.')
        self.assertEqual(recs['Scene:2'], '')
        self.assertTrue(all('translation' not in r for r in self.read_json()))   # text/ stays Japanese
        # unknown id: nothing is written, even for the good lines
        put([{'id': 'Scene:2', 'translation': 'Fine.'}, {'id': 'Nope:1', 'translation': 'x'}])
        p = self.batch('import', self.text, inp, *args)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(self.read_store()['Scene:2'], '')
        # overwrite needs --force
        put([{'id': 'Scene:1', 'translation': 'Changed.'}])
        self.assertEqual(self.batch('import', self.text, inp, *args).returncode, 1)
        self.assertEqual(self.batch('import', self.text, inp, '--force', *args).returncode, 0)
        self.assertEqual(self.read_store()['Scene:1'], 'Changed.')
        # translate=false, empty text, duplicates
        for rows in ([{'id': 'Sys:4', 'translation': 'x'}], [{'id': 'Scene:2', 'translation': ' '}],
                     [{'id': 'Scene:2', 'translation': 'a'}, {'id': 'Scene:2', 'translation': 'b'}]):
            put(rows)
            self.assertEqual(self.batch('import', self.text, inp, '--force', *args).returncode, 1, rows)

    def test_import_normalize_and_format(self):
        inp = os.path.join(self.dir, 'in.jsonl')
        with open(inp, 'w', encoding='utf-8') as f:
            f.write('```\n' + json.dumps({'id': 'Scene:2', 'translation': 'It\u2019s \u201cfine\u201d\u2026'}) + '\n```\n')
        p = self.batch('import', self.text, inp, '--normalize', '--limits', self.limits_path)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.read_store()['Scene:2'], 'It\'s "fine"...')
        # text/ is not touched: Japanese only
        self.assertEqual({r['id']: r for r in self.read_json()}['Scene:1']['text'], '山田「{V0001}おはよう」')

    def test_prepare_wraps(self):
        recs = self.read_json()
        recs[1]['translation'] = ' '.join(['wonder'] * 25)
        recs[5]['translation'] = ' '.join(['wonder'] * 25)
        recs[2]['translation'] = 'Existing.'
        self.write_split('Scene', recs)
        out = os.path.join(self.dir, 'prepared')
        p = self.batch('prepare', self.text, out, '--limits', self.limits_path)
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(os.path.join(out, 'Scene.json'), encoding='utf-8') as f:
            new = {r['id']: r for r in json.load(f)}
        self.assertIn(rules.BREAK, new['Scene:2']['translation'])
        self.assertIn('\n', new['Sys:1']['translation'])
        self.assertEqual(new['Scene:3']['translation'], 'Existing.')


if __name__ == '__main__':
    unittest.main(verbosity=1)
