#!/usr/bin/env python3
"""Tests of the translation store (tools/translate/store.py) and its batch.py commands.

Usage: test_translation_store.py

Every string is invented; no game text is used. The last test also guards the committed
translation/en/*.txt files: they must hold no Japanese.
"""
import glob
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
REPO = os.path.dirname(TOOLS)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TOOLS, 'translate'))
import check_translation as ct  # noqa: E402
import rules  # noqa: E402
import store  # noqa: E402

BATCH = os.path.join(TOOLS, 'translate', 'batch.py')
LIMITS = {'Sys:9': {'display': 'debug-console', 'max_px': None, 'lines': 0, 'translate': False, 'note': ''},
          'Sys:1': {'display': 'ConfirmDialog', 'max_px': 576, 'lines': 4, 'translate': True, 'note': ''}}


def mk(id_, text, speaker='YUM', route='YUM'):
    return {'file': 'X.scf', 'offset': 0, 'id': id_, 'speaker': speaker, 'text': text,
            'control_codes': rules.brace_tokens(text), 'byte_budget': 0, 'route': route,
            'context_prev': None, 'context_next': None}


RECS = [mk('Sc:1', '「{V0001}おはよう」'), mk('Sc:2', '「うん」', speaker='ERI/PLY'),
        mk('Sc:3', '朝', speaker=None), mk('Sys:9', 'debug', speaker=None, route='system'),
        mk('Sys:1', 'メッセージ', speaker=None, route='system')]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.text = os.path.join(self.dir, 'text')
        self.trans = os.path.join(self.dir, 'en')
        os.makedirs(self.text)
        self.limits_path = os.path.join(self.dir, 'limits.json')
        with open(self.limits_path, 'w') as f:
            json.dump(LIMITS, f)
        self.write_text('Sc', RECS)

    def tearDown(self):
        self.tmp.cleanup()

    def write_text(self, name, recs):
        with open(os.path.join(self.text, name + '.json'), 'w', encoding='utf-8') as f:
            json.dump(recs, f, ensure_ascii=False, indent=1)

    @property
    def path(self):
        return store.scene_path(self.trans, 'Sc')

    def sync(self, **kw):
        return store.sync(self.text, self.trans, LIMITS, **kw)

    def read(self):
        with open(self.path, encoding='utf-8', newline='') as f:
            return f.read()

    def edit(self, old, new):
        s = self.read()
        self.assertIn(old, s)
        with open(self.path, 'w', encoding='utf-8', newline='') as f:
            f.write(s.replace(old, new, 1))

    def batch(self, *args):
        return subprocess.run([sys.executable, BATCH, *args, '--trans', self.trans, '--limits', self.limits_path],
                              capture_output=True, text=True)


class Format(unittest.TestCase):
    def test_src_hash(self):
        h = store.src_hash('「うん」')
        self.assertRegex(h, r'^[0-9a-f]{8}$')
        self.assertEqual(h, store.src_hash('「うん」'))
        self.assertNotEqual(h, store.src_hash('「うん」 '))
        self.assertEqual(store.src_hash('abc'), 'a9993e36')   # sha1('abc') = a9993e36...

    def test_roundtrip_exact(self):
        text = ('# Sc -- English. Edit the line under each @ header. Empty line under a header = untranslated.\n'
                '# Format: docs/translation-format.md\n'
                '\n'
                '# note for the next record\n'
                '@Sc:1 YUM 3f2a91c0\n'
                '"Hey, {Nn}. Wait a second."\n'
                '\n'
                '@Sc:2 - 9b01de44\n'
                '\n'
                '\n'
                '@Sc:3.1 ERI/PLY 00000001\n'
                'one\\ntwo \\\\ back\n'
                '\n'
                '# trailing note\n')
        f = store.parse(text)
        self.assertEqual([e.id for e in f.entries], ['Sc:1', 'Sc:2', 'Sc:3.1'])
        self.assertIsNone(f.entries[1].speaker)
        self.assertEqual(f.entries[1].tr, '')
        self.assertEqual(f.entries[2].speaker, 'ERI/PLY')
        self.assertEqual(f.entries[2].tr, 'one\ntwo \\ back')
        self.assertEqual(f.entries[0].comments, ['# note for the next record'])
        self.assertEqual(f.tail, ['# trailing note'])
        self.assertEqual(len(f.top), 2)
        self.assertEqual(store.dump(f), text)

    def test_untranslated_last_record_has_no_blank_run(self):
        f = store.SceneFile('Sc', None, [store.Entry('Sc:1', 'YUM', 'aaaaaaaa', 'x'), store.Entry('Sc:2', None, 'bbbbbbbb')])
        text = store.dump(f)
        self.assertTrue(text.endswith('@Sc:2 - bbbbbbbb\n\n'))
        self.assertEqual(store.dump(store.parse(text)), text)

    def test_escapes(self):
        for tr in ('plain', 'two\nlines', 'back\\slash', 'ends with \\', '\\n literal', '# not a comment',
                   '@Sc:1 not a header', '\\#', 'a\n\nb', ' lead and trail ', 'quote "x" {W15}'):
            e = store.Entry('Sc:1', 'YUM', 'aaaaaaaa', tr)
            text = store.dump(store.SceneFile('Sc', [], [e]))
            self.assertEqual(text.count('\n'), 2, tr)           # header + exactly one physical line
            self.assertEqual(store.parse(text).entries[0].tr, tr, tr)
            self.assertEqual(store.dump(store.parse(text)), text, tr)

    def test_bad_input(self):
        for text in ('@Sc:1 YUM nothex!!\nx\n', '@Sc:1 YUM aaaaaaaa\nbad \\q escape\n', 'stray line\n',
                     '@Sc:1 YUM aaaaaaaa\nx\n\n@Sc:1 YUM aaaaaaaa\ny\n'):
            with self.assertRaises(store.StoreError, msg=text):
                store.parse(text)
        with self.assertRaises(store.StoreError):
            store.escape('cr\rlf')

    def test_tolerant_reading(self):
        # CRLF, a deleted empty line under a header, a file without trailing newline
        f = store.parse('@Sc:1 YUM aaaaaaaa\r\n@Sc:2 YUM bbbbbbbb\r\nfine')
        self.assertEqual([e.tr for e in f.entries], ['', 'fine'])

    def test_comment_directly_before_first_header_is_not_the_file_comment(self):
        f = store.parse('# note\n@Sc:1 YUM aaaaaaaa\nx\n')
        self.assertEqual(f.top, [])
        self.assertEqual(f.entries[0].comments, ['# note'])
        self.assertEqual(store.dump(f), '# note\n@Sc:1 YUM aaaaaaaa\nx\n')


class Sync(Base):
    def test_creates_file_with_exported_records_in_order(self):
        rep = self.sync()
        self.assertEqual(rep['files_created'], 1)
        f = store.load_scene(self.path)
        self.assertEqual([e.id for e in f.entries], ['Sc:1', 'Sc:2', 'Sc:3', 'Sys:1'])   # Sys:9 is translate=false
        self.assertEqual([e.speaker for e in f.entries], ['YUM', 'ERI/PLY', None, None])
        self.assertEqual(f.entries[0].src, store.src_hash(RECS[0]['text']))
        self.assertTrue(all(e.tr == '' for e in f.entries))
        self.assertEqual(f.top[0], '# Sc -- English. Edit the line under each @ header. Empty line under a header = untranslated.')
        self.assertNotRegex(self.read(), r'[^\x00-\x7e]')
        # idempotent: second run changes nothing
        before = self.read()
        rep = self.sync()
        self.assertEqual((rep['files_changed'], rep['files_created'], rep['added']), (0, 0, []))
        self.assertEqual(self.read(), before)

    def test_keeps_translations_and_comments_adds_missing(self):
        self.sync()
        self.edit('@Sc:2 ERI/PLY', '# translator note: keep it short\n@Sc:2 ERI/PLY')
        self.edit('@Sc:1 YUM %s\n' % store.src_hash(RECS[0]['text']), '@Sc:1 YUM %s\nGood morning.' % store.src_hash(RECS[0]['text']) + '\n')
        f = store.load_scene(self.path)
        self.assertEqual(f.entries[0].tr, 'Good morning.')
        # a new record appears in the Japanese, between existing ones
        recs = RECS[:1] + [mk('Sc:1.5', 'new')] + RECS[1:]
        self.write_text('Sc', recs)
        rep = self.sync()
        self.assertEqual(rep['added'], ['Sc:1.5'])
        f = store.load_scene(self.path)
        self.assertEqual([e.id for e in f.entries], ['Sc:1', 'Sc:1.5', 'Sc:2', 'Sc:3', 'Sys:1'])
        self.assertEqual(f.by_id()['Sc:1'].tr, 'Good morning.')
        self.assertEqual(f.by_id()['Sc:2'].comments, ['# translator note: keep it short'])

    def test_stale_hash_keeps_translation_and_marks(self):
        self.sync()
        h0 = store.src_hash(RECS[0]['text'])
        self.edit('@Sc:1 YUM %s\n' % h0, '@Sc:1 YUM %s\nGood morning.\n' % h0)
        changed = [dict(r) for r in RECS]
        changed[0]['text'] = '「{V0001}おはよう！」'
        self.write_text('Sc', changed)
        rep = self.sync()
        self.assertEqual(rep['stale'], ['Sc:1'])
        e = store.load_scene(self.path).by_id()['Sc:1']
        self.assertEqual(e.tr, 'Good morning.')
        self.assertEqual(e.src, h0)                       # not updated automatically
        self.assertEqual(len([c for c in e.comments if c.startswith('# STALE src')]), 1)
        self.sync()                                       # still one STALE comment, nothing else changes
        e = store.load_scene(self.path).by_id()['Sc:1']
        self.assertEqual(len([c for c in e.comments if c.startswith('# STALE src')]), 1)
        self.assertEqual(e.src, h0)
        rep = self.sync(accept_src=True)
        self.assertEqual(rep['accepted'], ['Sc:1'])
        e = store.load_scene(self.path).by_id()['Sc:1']
        self.assertEqual(e.src, store.src_hash(changed[0]['text']))
        self.assertEqual(e.comments, [])
        self.assertEqual(e.tr, 'Good morning.')

    def test_stale_untranslated_just_refreshes_hash(self):
        self.sync()
        changed = [dict(r) for r in RECS]
        changed[1]['text'] = '「ううん」'
        self.write_text('Sc', changed)
        rep = self.sync()
        self.assertEqual((rep['stale'], rep['refreshed']), ([], ['Sc:2']))
        self.assertEqual(store.load_scene(self.path).by_id()['Sc:2'].src, store.src_hash('「ううん」'))

    def test_orphans_reported_not_deleted(self):
        self.sync()
        h = store.src_hash(RECS[1]['text'])
        self.edit('@Sc:2 ERI/PLY %s\n' % h, '@Sc:2 ERI/PLY %s\nKept line.\n' % h)
        self.write_text('Sc', [r for r in RECS if r['id'] != 'Sc:2'])
        rep = self.sync()
        self.assertEqual(rep['orphans'], ['Sc:2'])
        e = store.load_scene(self.path).by_id()['Sc:2']
        self.assertEqual(e.tr, 'Kept line.')
        self.assertTrue(any(c.startswith('# ORPHAN') for c in e.comments))
        self.assertEqual(self.sync()['orphans'], ['Sc:2'])    # still reported on the next run
        # an untranslated entry that vanished has nothing to lose
        self.write_text('Sc', [r for r in RECS if r['id'] not in ('Sc:2', 'Sc:3')])
        rep = self.sync()
        self.assertEqual(rep['dropped'], ['Sc:3'])

    def test_orphan_scene_file_reported(self):
        self.sync()
        store.write_scene(store.scene_path(self.trans, 'Gone'), store.SceneFile('Gone'))
        self.assertEqual(self.sync()['orphan_files'], ['Gone'])
        self.assertTrue(os.path.exists(store.scene_path(self.trans, 'Gone')))

    def test_cli_sync_prints_warning(self):
        self.sync()
        h0 = store.src_hash(RECS[0]['text'])
        self.edit('@Sc:1 YUM %s\n' % h0, '@Sc:1 YUM %s\nGood morning.\n' % h0)
        changed = [dict(r) for r in RECS]
        changed[0]['text'] = 'changed'
        self.write_text('Sc', changed)
        p = self.batch('sync', self.text)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('WARN stale src: Sc:1', p.stdout)
        p = self.batch('sync', self.text, '--accept-src')
        self.assertNotIn('WARN stale', p.stdout)


class Commands(Base):
    def put(self, rows):
        inp = os.path.join(self.dir, 'in.jsonl')
        with open(inp, 'w', encoding='utf-8') as f:
            f.write('\n'.join(json.dumps(r) for r in rows) + '\n')
        return inp

    def test_import_creates_store_and_leaves_text_alone(self):
        before = open(os.path.join(self.text, 'Sc.json'), 'rb').read()
        p = self.batch('import', self.text, self.put([{'id': 'Sc:1', 'translation': 'Good morning.'},
                                                       {'id': 'Sc:2', 'translation': 'Line one\nline two'}]))
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(open(os.path.join(self.text, 'Sc.json'), 'rb').read(), before)
        f = store.load_scene(self.path)
        self.assertEqual([e.tr for e in f.entries], ['Good morning.', 'Line one\nline two', '', ''])
        self.assertNotRegex(self.read(), r'[^\x00-\x7e]')

    def test_import_refusals(self):
        self.assertEqual(self.batch('import', self.text, self.put([{'id': 'Sc:1', 'translation': 'a'}])).returncode, 0)
        for rows in ([{'id': 'Nope:1', 'translation': 'x'}], [{'id': 'Sc:3', 'translation': ' '}],
                     [{'id': 'Sc:3', 'translation': 'a'}, {'id': 'Sc:3', 'translation': 'b'}],
                     [{'id': 'Sys:9', 'translation': 'x'}], [{'id': 'Sc:1', 'translation': 'different'}],
                     [{'id': 'Sc:3', 'translation': 'Kana ありがとう'}]):
            before = self.read()
            p = self.batch('import', self.text, self.put(rows))
            self.assertEqual(p.returncode, 1, rows)
            self.assertEqual(self.read(), before, rows)
        p = self.batch('import', self.text, self.put([{'id': 'Sc:1', 'translation': 'different'}]), '--force')
        self.assertEqual(p.returncode, 0)
        self.assertEqual(store.load_scene(self.path).by_id()['Sc:1'].tr, 'different')

    def test_import_clears_stale_marker_of_that_line(self):
        self.batch('import', self.text, self.put([{'id': 'Sc:1', 'translation': 'a'}]))
        changed = [dict(r) for r in RECS]
        changed[0]['text'] = 'changed'
        self.write_text('Sc', changed)
        self.sync()
        self.assertTrue(store.load_scene(self.path).by_id()['Sc:1'].comments)
        self.assertEqual(self.batch('import', self.text, self.put([{'id': 'Sc:1', 'translation': 'b'}]), '--force').returncode, 0)
        e = store.load_scene(self.path).by_id()['Sc:1']
        self.assertEqual((e.tr, e.comments, e.src), ('b', [], store.src_hash('changed')))

    def test_import_keeps_comments(self):
        self.sync()
        self.edit('@Sc:1', '# keep me\n@Sc:1')
        self.batch('import', self.text, self.put([{'id': 'Sc:1', 'translation': 'a'}]))
        self.assertEqual(store.load_scene(self.path).by_id()['Sc:1'].comments, ['# keep me'])

    def test_merge_and_prepare(self):
        self.batch('import', self.text, self.put([{'id': 'Sc:1', 'translation': ' '.join(['wonder'] * 25)},
                                                   {'id': 'Sys:1', 'translation': ' '.join(['wonder'] * 25)}]))
        merged = store.merge(self.text, self.trans)
        r = {x['id']: x for x in merged['Sc']}
        self.assertEqual(r['Sc:1']['translation'], ' '.join(['wonder'] * 25))
        self.assertNotIn('translation', r['Sc:2'])
        self.assertEqual(r['Sc:1']['text'], RECS[0]['text'])
        out = os.path.join(self.dir, 'prepared')
        p = self.batch('prepare', self.text, out)
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(os.path.join(out, 'Sc.json'), encoding='utf-8') as f:
            new = {x['id']: x for x in json.load(f)}
        self.assertIn(rules.BREAK, new['Sc:1']['translation'])
        self.assertIn('\n', new['Sys:1']['translation'])
        self.assertNotIn('translation', new['Sc:2'])
        self.assertTrue(all('_src' not in x for x in new.values()))
        self.assertEqual(new['Sc:1']['text'], RECS[0]['text'])
        # prepare of an already merged directory still works with --trans none
        out2 = os.path.join(self.dir, 'prepared2')
        subprocess.run([sys.executable, BATCH, 'prepare', out, out2, '--trans', 'none'], check=True, capture_output=True)

    def test_export_reads_english_from_store(self):
        self.batch('import', self.text, self.put([{'id': 'Sc:1', 'translation': 'Good morning.'}]))
        out = os.path.join(self.dir, 'b.jsonl')
        p = self.batch('export', self.text, 'Sc', out, '--context', '1', '--glossary', os.path.join(self.dir, 'none.json'))
        self.assertEqual(p.returncode, 0, p.stderr)
        with open(out, encoding='utf-8') as f:
            rows = [json.loads(l) for l in f]
        self.assertEqual([r['id'] for r in rows], ['Sc:2', 'Sc:3', 'Sys:1'])        # Sc:1 done, Sys:9 skipped
        self.assertEqual(rows[0]['prev'][0]['en'], 'Good morning.')
        self.assertEqual(self.batch('export', self.text, 'Sc', out, '--include-translated',
                                    '--glossary', os.path.join(self.dir, 'none.json')).returncode, 0)
        with open(out, encoding='utf-8') as f:
            self.assertEqual(json.loads(f.readline())['translation'], 'Good morning.')

    def test_show(self):
        self.batch('import', self.text, self.put([{'id': 'Sc:1', 'translation': 'Good morning.'}]))
        p = self.batch('show', self.text, 'Sc', '--id', 'Sc:1')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('おはよう', p.stdout)
        self.assertIn('EN  Good morning.', p.stdout)
        self.assertNotIn('Sc:2', p.stdout)
        p = self.batch('show', self.text, 'Sc')
        self.assertIn('Sc:2', p.stdout)
        self.assertNotIn('Sys:9', p.stdout)
        self.assertNotEqual(self.batch('show', self.text, 'Sc', '--id', 'Nope:1').returncode, 0)

    def test_check_reads_store_and_flags_stale(self):
        self.batch('import', self.text, self.put([{'id': 'Sc:1', 'translation': '"{V0001}Good morning."'}]))
        check = os.path.join(HERE, 'check_translation.py')
        args = [sys.executable, check, self.text, '--trans', self.trans, '--limits', self.limits_path,
                '--glossary', os.path.join(self.dir, 'none.json')]
        p = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn('PASS 1', p.stdout)
        self.assertNotIn('SRC_STALE', p.stdout)
        changed = [dict(r) for r in RECS]
        changed[0]['text'] = '「{V0001}おはよう！」'
        self.write_text('Sc', changed)
        p = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)                    # a warning, not a failure
        self.assertIn('WARN SRC_STALE', p.stdout)
        self.assertEqual(subprocess.run(args + ['--strict'], capture_output=True).returncode, 1)

    def test_migrate(self):
        recs = [dict(r) for r in RECS]
        recs[0]['translation'] = 'Moved.'
        recs[1]['translation'] = 'Kana ありがとう'
        self.write_text('Sc', recs)
        p = self.batch('migrate', self.text)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('1 translation(s) moved', p.stdout)
        self.assertEqual(store.load_scene(self.path).by_id()['Sc:1'].tr, 'Moved.')
        with open(os.path.join(self.text, 'Sc.json'), encoding='utf-8') as f:
            left = {r['id']: r for r in json.load(f)}
        self.assertNotIn('translation', left['Sc:1'])
        self.assertIn('translation', left['Sc:2'])           # Japanese never enters the store
        self.assertEqual(store.load_scene(self.path).by_id()['Sc:2'].tr, '')
        self.assertEqual(left['Sc:1']['text'], RECS[0]['text'])


class NoJapanese(unittest.TestCase):
    ALLOWED = set(rules.DEFAULT_ALLOWED)    # line break, pause, U+3000: engine characters

    def test_guard_function(self):
        self.assertEqual(store.japanese_chars('plain {W15} text'), [])
        self.assertEqual(store.japanese_chars('one／two ｜ x'), [])
        self.assertEqual(store.japanese_chars('a あ 山 Ａ ・'), ['あ', '山', 'Ａ', '・'])

    def test_committed_store_has_no_japanese(self):
        files = sorted(glob.glob(os.path.join(REPO, 'translation', 'en', '*.txt')))
        if not files:
            self.skipTest('translation/en not generated yet')
        bad = {}
        for p in files:
            with open(p, encoding='utf-8') as f:
                text = f.read()
            chars = [c for c in dict.fromkeys(text) if (ord(c) >= 0x3000 or ord(c) > 0x7E and rules.is_japanese(c))
                     and c not in self.ALLOWED]
            if chars or store.japanese_chars(text):
                bad[os.path.basename(p)] = chars
            self.assertNotIn('\r', text, p)
            store.parse(text, path=p)       # well-formed
        self.assertEqual(bad, {}, 'Japanese text in translation/en')


if __name__ == '__main__':
    unittest.main(verbosity=1)
