"""The translation store: committed English text, one file per scene (translation/en/<SCENE>.txt).

text/<SCENE>.json holds the Japanese extracted from the user's own disc and never enters the repo.
The English lives here instead, keyed by record id plus a hash of the Japanese it was written
against, so the store contains no Japanese at all. Format (docs/translation-format.md):

    # <SCENE> -- English. Edit the line under each @ header. Empty line under a header = untranslated.
    # Format: docs/translation-format.md

    # a translator note, belongs to the record below
    @ASU_DAT_A:12 YUM 3f2a91c0
    "Hey, {Nn}. Wait a second."

    @ASU_DAT_A:13 SYS 9b01de44

Header: '@<id> <speaker or -> <src>'; src = first 8 hex digits of the SHA-1 of the Japanese text
(UTF-8). The translation is the one physical line under the header (may be empty). Escapes: \\n is a
newline, \\\\ a backslash; a line that would begin with '#' or '@' is written with a leading
backslash (\\# or \\@). Records are separated by one blank line. Lines starting with '#' are
comments; a comment block before a header belongs to that record, the block at the top of the file
(followed by a blank line) is the file comment. Tools regenerate headers and record order; humans
edit translation lines and comments.

Public API: src_hash, parse, dump, load_scene, write_scene, sync_scene, sync, merge, merged_index.
"""
import glob
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import rules  # noqa: E402

DEFAULT_DIR = os.path.join(REPO, 'translation', 'en')
HEADER_RE = re.compile(r'^@(\S+) (\S+) ([0-9a-f]{8})$')
STALE_MARK = '# STALE src'
ORPHAN_MARK = '# ORPHAN'


class StoreError(ValueError):
    pass


# ---------------------------------------------------------------------------- hashing, escapes

def src_hash(ja):
    return hashlib.sha1(ja.encode('utf-8')).hexdigest()[:8]


def escape(s):
    if '\r' in s:
        raise StoreError('carriage return in a translation')
    out = s.replace('\\', '\\\\').replace('\n', '\\n')
    if out[:1] in ('#', '@'):
        out = '\\' + out
    return out


def unescape(s, where=''):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c != '\\':
            out.append(c)
            i += 1
            continue
        nxt = s[i + 1:i + 2]
        if nxt == 'n':
            out.append('\n')
        elif nxt in ('\\', '#', '@'):
            out.append(nxt)
        else:
            raise StoreError(f'{where}unknown escape \\{nxt} (use \\\\ for a backslash, \\n for a newline)')
        i += 2
    return ''.join(out)


def japanese_chars(s):
    """Japanese or full-width characters in s, except the three the engine needs in English text
    (the line break U+FF0F, the pause U+FF5C, U+3000). The store must hold none of the others."""
    return [c for c in dict.fromkeys(s) if rules.is_japanese(c) and c not in rules.DEFAULT_ALLOWED]


# ---------------------------------------------------------------------------- file model

class Entry:
    def __init__(self, id, speaker, src, tr='', comments=None):
        self.id = id
        self.speaker = speaker      # None is written as '-'
        self.src = src
        self.tr = tr
        self.comments = list(comments or [])

    def header(self):
        return f'@{self.id} {self.speaker or "-"} {self.src}'


class SceneFile:
    def __init__(self, scene, top=None, entries=None, tail=None):
        self.scene = scene
        self.top = list(top) if top is not None else default_top(scene)
        self.entries = entries or []
        self.tail = list(tail or [])

    def by_id(self):
        return {e.id: e for e in self.entries}


def default_top(scene):
    return [f'# {scene} -- English. Edit the line under each @ header. Empty line under a header = untranslated.',
            '# Format: docs/translation-format.md']


def parse(text, scene='?', path='<string>'):
    lines = text.replace('\r\n', '\n').split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    i, n = 0, len(lines)
    top = []
    j = 0
    while j < n and lines[j].startswith('#'):
        j += 1
    if j > 0 and (j == n or lines[j] == ''):
        top, i = lines[:j], j
    entries, seen, pending = [], set(), []
    while i < n:
        ln = lines[i]
        where = f'{path}:{i + 1}: '
        if ln == '':
            i += 1
        elif ln.startswith('#'):
            pending.append(ln)
            i += 1
        elif ln.startswith('@'):
            m = HEADER_RE.match(ln)
            if not m:
                raise StoreError(f'{where}malformed header {ln!r} (expected "@<id> <speaker or -> <8 hex>")')
            rid, sp, src = m.groups()
            if rid in seen:
                raise StoreError(f'{where}duplicate id {rid}')
            seen.add(rid)
            tr = ''
            i += 1
            if i < n and not lines[i].startswith(('#', '@')):
                tr = unescape(lines[i], f'{path}:{i + 1}: ')
                i += 1
            entries.append(Entry(rid, None if sp == '-' else sp, src, tr, pending))
            pending = []
        else:
            raise StoreError(f'{where}unexpected line {ln[:40]!r} (a translation goes on the line right under an @ header)')
    return SceneFile(scene, top, entries, pending)


def dump(f):
    out = list(f.top)
    first = not out
    for e in f.entries:
        if not first:
            out.append('')
        first = False
        out += e.comments
        out.append(e.header())
        out.append(escape(e.tr))
    if f.tail:
        if out:
            out.append('')
        out += f.tail
    return '\n'.join(out) + '\n'


def load_scene(path):
    scene = os.path.splitext(os.path.basename(path))[0]
    with open(path, encoding='utf-8', newline='') as fh:
        return parse(fh.read(), scene, path)


def write_scene(path, f):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='') as fh:
        fh.write(dump(f))
    os.replace(tmp, path)


def scene_path(trans_dir, scene):
    return os.path.join(trans_dir, scene + '.txt')


def scene_of(path):
    return os.path.splitext(os.path.basename(path))[0]


# ---------------------------------------------------------------------------- sync

def exported(rec, limits):
    """Records that appear in the store: everything except translate=false."""
    lim = limits.get(rec['id'])
    return lim is None or bool(lim.get('translate'))


def _own(c):
    return c.startswith(STALE_MARK) or c.startswith(ORPHAN_MARK)


def sync_scene(scene, recs, existing, limits, accept_src=False):
    """Bring one scene file in line with the Japanese records. Returns (SceneFile, report).
    existing is a SceneFile or None. Nothing is written here."""
    old = existing.by_id() if existing else {}
    rep = {'added': [], 'stale': [], 'accepted': [], 'refreshed': [], 'orphans': [], 'dropped': [], 'kept': 0}
    entries, live = [], set()
    for r in recs:
        if not exported(r, limits):
            continue
        rid, h = r['id'], src_hash(r['text'])
        live.add(rid)
        e = old.get(rid)
        if e is None:
            entries.append(Entry(rid, r['speaker'], h))
            rep['added'].append(rid)
            continue
        e.speaker = r['speaker']
        e.comments = [c for c in e.comments if not _own(c)]
        if e.src != h:
            if not e.tr:
                e.src = h
                rep['refreshed'].append(rid)
            elif accept_src:
                e.src = h
                rep['accepted'].append(rid)
            else:
                e.comments.append(f'{STALE_MARK}: the Japanese changed after this line was written '
                                  f'(written against {e.src}, now {h}); check it, then run sync --accept-src')
                rep['stale'].append(rid)
        if e.tr:
            rep['kept'] += 1
        entries.append(e)
    for e in (existing.entries if existing else []):
        if e.id in live:
            continue
        e.comments = [c for c in e.comments if not _own(c)]
        if not e.tr and not e.comments:
            rep['dropped'].append(e.id)
            continue
        e.comments.append(f'{ORPHAN_MARK}: this id is no longer in the extracted text; kept, not deleted')
        rep['orphans'].append(e.id)
        entries.append(e)
    top = existing.top if existing and existing.top else None
    return SceneFile(scene, top, entries, existing.tail if existing else None), rep


def sync(text_dir, trans_dir, limits=None, accept_src=False, scenes=None, dry_run=False):
    """Create or update translation/en/*.txt for the scenes of text_dir. Returns a report dict."""
    limits = rules.load_limits() if limits is None else limits
    paths = rules.resolve_files(text_dir, scenes)
    total = {'files_created': 0, 'files_changed': 0, 'scenes': len(paths), 'added': [], 'stale': [],
             'accepted': [], 'refreshed': [], 'orphans': [], 'dropped': [], 'orphan_files': [], 'kept': 0}
    for p in paths:
        scene = scene_of(p)
        out = scene_path(trans_dir, scene)
        existing = load_scene(out) if os.path.exists(out) else None
        f, rep = sync_scene(scene, rules.load_json(p), existing, limits, accept_src)
        new_text = dump(f)
        if existing is None:
            total['files_created'] += 1
        else:
            with open(out, encoding='utf-8', newline='') as fh:
                if fh.read() == new_text:
                    new_text = None
            if new_text is not None:
                total['files_changed'] += 1
        if new_text is not None and not dry_run:
            write_scene(out, f)
        for k in ('added', 'stale', 'accepted', 'refreshed', 'orphans', 'dropped'):
            total[k] += rep[k]
        total['kept'] += rep['kept']
    if os.path.isdir(trans_dir) and not scenes:
        names = {scene_of(p) for p in paths}
        total['orphan_files'] = sorted(scene_of(x) for x in glob.glob(os.path.join(trans_dir, '*.txt'))
                                       if scene_of(x) not in names)
    return total


# ---------------------------------------------------------------------------- merge

def merge(text_dir, trans_dir, scenes=None):
    """{scene: records} = the Japanese records of text_dir with 'translation' filled from the store.
    An empty store line means untranslated (no 'translation' key). A record that already carries a
    'translation' in its json (legacy or test directories) keeps it unless the store has a line.
    Each translated record also gets '_src', the hash stored with the line (None if unknown)."""
    out = {}
    for p in rules.resolve_files(text_dir, scenes):
        scene = scene_of(p)
        recs = rules.load_json(p)
        entries = {}
        sp = scene_path(trans_dir, scene) if trans_dir else None
        if sp and os.path.exists(sp):
            entries = load_scene(sp).by_id()
        for r in recs:
            e = entries.get(r['id'])
            if e is not None and e.tr:
                r['translation'] = e.tr
                r['_src'] = e.src
        out[scene] = recs
    return out


def merged_index(text_dir, trans_dir):
    """{id: record} over the merged text directory (cross references: speaker labels, topic parts)."""
    idx = {}
    for recs in merge(text_dir, trans_dir).values():
        for r in recs:
            idx[r['id']] = r
    return idx


def strip_internal(rec):
    rec.pop('_src', None)
    return rec
