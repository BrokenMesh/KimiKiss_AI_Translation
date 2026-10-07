"""Shared rules for the translation pipeline (Phase 5): record loading, the display limit
that applies to a record, text measuring, automatic wrapping, glossary lookup.

Used by tools/translate/batch.py (export/import/prepare) and tools/qa/check_translation.py.
Everything here is deterministic; there are no model calls.

Kinds of record (see docs/phase-5-pipeline.md):
  dialogue  message window, up to 3 lines, wrapped automatically at word boundaries
  choice    one line per choice, choices separated by the line break; never wrapped
  fragment  a piece of text glued into another string or used as a label; one line
  single    one line at a fixed pixel budget (labels, credits, menu text)
  confirm   ConfirmDialog message: lines split on \\n and the line break only
  skip      limits.json says translate=false
"""
import glob
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(TOOLS, 'reinsert'))
sys.path.insert(0, os.path.join(TOOLS, 'font'))
import en_text  # noqa: E402
import encoding  # noqa: E402

LIMITS_PATH = os.path.join(TOOLS, 'reinsert', 'limits.json')
GLOSSARY_PATH = os.path.join(HERE, 'glossary.json')

BREAK = en_text.BREAK
TOKEN = en_text.TOKEN
BRACED = re.compile(r'\{([^{}]*)\}')
NAME_TOKENS = ('{Nn}', '{Nm}')

# Pixel scale of the English width table (en_widths.json is for scale 1.0) and the advance of one
# Japanese character, per consumer (docs/phase-4-system-text.md).
DISPLAYS = {
    'TextWindow': (1.0, en_text.FULL_PX),
    'TextLine': (1.0, 24),
    'NameEntryEdit': (1.0, 24),
    'ConfirmDialog': (0.75, 18),
}
CONFIRM_PX = 576

# K2_Script string slot of each speaker's label (docs/phase-4-system-text.md)
SPEAKER_LABEL_ID = {
    'PLY': 13, 'YUM': 19, 'NAR': 22, 'MAO': 24, 'ASU': 26, 'ERI': 28, 'MIT': 30, 'NAN': 32,
    'AKI': 34, 'TOM': 36, 'MEG': 38, 'GUN': 40, 'KAO': 42, 'MAN': 44, 'MIC': 46, 'KEI': 48,
    'EX1': 50, 'EX2': 52, 'ETB': 54, 'ETG': 56, 'ETC': 58,
}

# Characters that are allowed outside braces although they are not ASCII.
DEFAULT_ALLOWED = '／｜　'

# Typographic characters translators like to produce; the font has no glyph for them.
TYPOGRAPHY = {
    '‘': "'", '’': "'", '‚': ',', '‛': "'",
    '“': '"', '”': '"', '„': '"',
    '–': '-', '—': '--', '―': '--', '−': '-',
    '…': '...', ' ': ' ', ' ': ' ', ' ': ' ', '​': '',
    '•': '*', '·': '*',
}

JP_RANGES = [
    (0x3000, 0x30FF), (0x31F0, 0x31FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF),
    (0xF900, 0xFAFF), (0xFF00, 0xFFEF), (0x25A0, 0x25FF), (0x2600, 0x26FF),
]


# ---------------------------------------------------------------------------- loading

def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def load_limits(path=None):
    path = path or LIMITS_PATH
    return load_json(path) if os.path.exists(path) else {}


def load_glossary(path=None):
    """Tolerant glossary loader: {"terms": [{"ja","en","kind","note"}], "policy": {}}.
    A bare list of terms is accepted too. Returns a list of normalized terms ([] when missing)."""
    path = path or GLOSSARY_PATH
    if not os.path.exists(path):
        return []
    try:
        data = load_json(path)
    except (OSError, ValueError):
        return []
    raw = data.get('terms', []) if isinstance(data, dict) else data
    terms = []
    for t in raw if isinstance(raw, list) else []:
        if not isinstance(t, dict) or not t.get('ja'):
            continue
        en = t.get('en')
        variants = []
        if isinstance(en, str):
            variants += [v.strip() for v in en.split('|')]
        elif isinstance(en, list):
            variants += [str(v).strip() for v in en]
        extra = t.get('variants')
        if isinstance(extra, list):
            variants += [str(v).strip() for v in extra]
        variants = [v for v in variants if v]
        terms.append({'ja': t['ja'], 'en': en if isinstance(en, str) else (variants[0] if variants else ''),
                      'variants': variants, 'kind': t.get('kind') or '', 'note': t.get('note') or '',
                      'check': t.get('check', True) is not False})
    return terms


def glossary_checkable(term):
    """Terms that are checked as 'Japanese contains it, so English must too'."""
    if not term['check'] or not term['variants']:
        return False
    if term['kind'] in ('honorific', 'suffix'):
        return False
    ja = term['ja']
    if len(ja) <= 2 and all('぀' <= c <= 'ヿ' for c in ja):
        return False  # one or two kana match inside unrelated words
    return True


def glossary_hits(ja_text, terms):
    plain = BRACED.sub('', ja_text)
    return [t for t in terms if glossary_checkable(t) and t['ja'] in plain]


def resolve_files(text_dir, specs=None):
    """Map scene names / file names / paths / globs to a sorted list of .json paths."""
    if not specs:
        return sorted(glob.glob(os.path.join(text_dir, '*.json')))
    out = []
    for spec in specs:
        for part in str(spec).split(','):
            part = part.strip()
            if not part:
                continue
            cands = []
            if os.path.isfile(part):
                cands = [part]
            else:
                base = re.sub(r'\.(json|scf)$', '', os.path.basename(part))
                cands = sorted(glob.glob(os.path.join(text_dir, base + '.json')))
            if not cands:
                raise SystemExit(f'no text file matches {part!r} in {text_dir}')
            out += cands
    seen, uniq = set(), []
    for p in out:
        if os.path.abspath(p) not in seen:
            seen.add(os.path.abspath(p))
            uniq.append(p)
    return uniq


def load_records(paths):
    """{path: [records]} in file order."""
    return {p: load_json(p) for p in paths}


def index_dir(text_dir):
    """{id: record} over every json file of a text directory (for cross references)."""
    idx = {}
    for p in sorted(glob.glob(os.path.join(text_dir, '*.json'))):
        for r in load_json(p):
            idx[r['id']] = r
    return idx


def write_records(path, records, like=None):
    """Write with the extractor's formatting (indent 1, UTF-8, trailing newline as the original)."""
    text = json.dumps(records, ensure_ascii=False, indent=1)
    nl = True
    if like and os.path.exists(like):
        with open(like, encoding='utf-8', newline='') as f:
            nl = f.read().endswith('\n')
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='') as f:
        f.write(text + ('\n' if nl else ''))
    os.replace(tmp, path)


# ---------------------------------------------------------------------------- measuring

_W = None


def widths():
    global _W
    if _W is None:
        _W = en_text.widths()
    return _W


def scaled_widths(scale):
    w = widths()
    return w if scale == 1.0 else {k: v * scale for k, v in w.items()}


def tokens(text):
    return TOKEN.findall(text)


def tok_px(tok, w, scale=1.0, jp_px=en_text.FULL_PX):
    if tok in NAME_TOKENS:
        return en_text.NAME_PX * scale
    if tok.startswith('{') and len(tok) > 1:
        return 0
    if ' ' <= tok <= '~':
        return w[tok]
    return jp_px


def text_px(text, display='TextWindow'):
    scale, jp = DISPLAYS.get(display, (1.0, 24))
    w = scaled_widths(scale)
    return sum(tok_px(t, w, scale, jp) for t in tokens(text))


def split_lines(text, kind):
    """Lines as the engine sees them. confirm: \\n and the line break; dialogue: the line break."""
    if kind == 'confirm':
        return re.split(r'\n|' + BREAK, text)
    return text.split(BREAK)


# ---------------------------------------------------------------------------- limits

def speaker_labels(index):
    """{speaker: label translation or None} from the K2_Script label records."""
    out = {}
    for sp, n in SPEAKER_LABEL_ID.items():
        r = index.get(f'K2_Script:{n}')
        out[sp] = r.get('translation') if r else None
    return out


def label_px_for(speaker, labels):
    """Where line 1 starts after the speaker label (0 = no label)."""
    if not speaker or speaker == 'SYS':
        return 0
    px = 0
    for sp in speaker.split('/'):
        if sp == 'SYS':
            continue
        t = (labels or {}).get(sp)
        lab = text_px(t, 'TextWindow') if t else en_text.INDENT_PX
        if sp == 'PLY':
            lab = max(lab, en_text.NAME_PX)  # replaced by the player's surname at run time
        px = max(px, lab)
    # D-023: line 1 starts at the indent column, or PLATE_GAP_PX after a plate wider than the indent
    return max(en_text.INDENT_PX, px + en_text.PLATE_GAP_PX)


def dialogue_limit(speaker, labels, lines=3):
    lab = label_px_for(speaker, labels)
    if lab == 0:
        first, cont = en_text.LINE_PX, en_text.LINE_PX
    else:
        first, cont = en_text.LINE_PX - lab, en_text.LINE_PX - en_text.INDENT_PX
    return {'kind': 'dialogue', 'display': 'TextWindow', 'lines': lines, 'first_px': first, 'cont_px': cont,
            'max_px': en_text.LINE_PX, 'label_px': lab, 'scale': 1.0, 'jp_px': en_text.FULL_PX}


def limit_for(rec, limits, labels=None):
    """The display rule that applies to a record. Always returns a dict with 'kind'."""
    lim = limits.get(rec['id'])
    sysrec = rec.get('route') == 'system'
    if lim is not None:
        base = {'display': lim['display'], 'note': lim.get('note', '')}
        if not lim.get('translate'):
            return dict(base, kind='skip', lines=0, max_px=None)
        disp, note, mx, ln = lim['display'], lim.get('note', ''), lim['max_px'], lim['lines']
        scale, jp = DISPLAYS.get(disp, (1.0, 24))
        if disp == 'ConfirmDialog':
            return dict(base, kind='confirm', lines=ln, max_px=mx, first_px=mx, cont_px=mx, scale=scale, jp_px=jp)
        if disp == 'TextWindow':
            if 'Exactly 2 lines' in note:
                return dict(base, kind='choice', lines=2, choices=2, max_px=mx, first_px=mx, cont_px=mx,
                            scale=1.0, jp_px=jp)
            if ln > 1:
                m = re.search(r'Speaker (\w+)', note)
                speaker = rec.get('speaker') if rec.get('speaker') else (m.group(1) if m else None)
                d = dialogue_limit(speaker, labels, ln)
                d.update(base)
                return d
            return dict(base, kind='single', lines=1, max_px=mx, first_px=mx, cont_px=mx, scale=1.0, jp_px=jp)
        return dict(base, kind='single', lines=1, max_px=mx, first_px=mx, cont_px=mx, scale=scale, jp_px=jp)
    if sysrec:
        return {'kind': 'single', 'display': 'unknown', 'lines': 1, 'max_px': CONFIRM_PX, 'first_px': CONFIRM_PX,
                'cont_px': CONFIRM_PX, 'scale': 1.0, 'jp_px': 24, 'note': 'no entry in limits.json', 'unknown': True}
    if rec.get('speaker'):
        return dialogue_limit(rec['speaker'], labels)
    if '.' in rec['id'].split(':', 1)[1]:
        n = rec['text'].count(BREAK) + 1
        return {'kind': 'choice', 'display': 'TextWindow', 'lines': n, 'choices': n, 'max_px': en_text.LINE_PX,
                'first_px': en_text.LINE_PX, 'cont_px': en_text.LINE_PX, 'scale': 1.0, 'jp_px': en_text.FULL_PX,
                'note': 'one line per choice, same number of choices as the Japanese'}
    return {'kind': 'fragment', 'display': 'TextWindow', 'lines': 1, 'max_px': en_text.LINE_PX,
            'first_px': en_text.LINE_PX, 'cont_px': en_text.LINE_PX, 'scale': 1.0, 'jp_px': en_text.FULL_PX,
            'note': 'piece of a longer string or a label; one line'}


# ---------------------------------------------------------------------------- wrapping

def prepare_text(text, lim):
    """The text as it should be reinserted: dialogue is word-wrapped with the line break, ConfirmDialog
    lines are wrapped with \\n, everything else is unchanged."""
    kind = lim['kind']
    if kind == 'dialogue':
        return en_text.wrap(text, lim['first_px'], lim['cont_px'], widths())
    if kind == 'confirm':
        w = scaled_widths(lim['scale'])
        parts = re.split(r'(\n|' + BREAK + ')', text)  # keep the translator's own breaks as they are
        return ''.join(p if p in ('\n', BREAK) else
                       en_text.wrap(p, lim['max_px'], lim['max_px'], w).replace(BREAK, '\n') for p in parts)
    return text


def fit(text, lim):
    """Measure prepared text. Returns {'lines': [px], 'limits': [px], 'rows': n, 'overflow': [i]}.
    rows counts the engine's per-character overflow wrap of an over-long line as extra rows."""
    kind = lim['kind']
    scale, jp = lim.get('scale', 1.0), lim.get('jp_px', en_text.FULL_PX)
    w = scaled_widths(scale)
    lines = split_lines(text, kind)
    px = [sum(tok_px(t, w, scale, jp) for t in tokens(l)) for l in lines]
    limits = [lim['first_px'] if i == 0 else lim['cont_px'] for i in range(len(lines))]
    rows, over = 0, []
    last = len(px)
    while last > 1 and px[last - 1] == 0:
        last -= 1  # trailing lines that hold only control codes draw nothing
    for i, (p, l) in enumerate(zip(px[:last], limits)):
        if p > l:
            over.append(i)
            rows += math.ceil(p / l) if l > 0 else 99
        else:
            rows += 1
    return {'lines': px, 'limits': limits, 'rows': rows, 'overflow': over}


# ---------------------------------------------------------------------------- text helpers

def brace_tokens(text):
    return BRACED.findall(text)


def normalize_typography(text):
    return ''.join(TYPOGRAPHY.get(c, c) for c in text)


def is_japanese(ch):
    o = ord(ch)
    return any(a <= o <= b for a, b in JP_RANGES)


def has_english_glyph(ch):
    try:
        encoding.code_of(ch)
        return True
    except ValueError:
        return False
