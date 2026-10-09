#!/usr/bin/env python3
"""Read translation/textures.toml, the English text of the game's pictures (D-019, D-035).

Usage: texdefs.py check [textures.toml]     parse the file and print a summary

The format is described at the top of translation/textures.toml. This module turns it
into what tools/texture/redraw.py works with:
  load() -> {'textures': {entry: {'entry', 'name', 'size', 'note', 'lines': [line]}},
             'sprites': {record name: (w, h)}}
  line   -> {'entry', 'line', 'japanese', 'english' ("|" = line break), 'notes',
             'bg' (redraw spec, e.g. "mode,T"), 'box' ("auto" or "x0,y0,x1,y1"),
             'align' ("t", "c" or "l"), 'opts' {key: str}}
Unknown keys, wrong types and duplicate entries are errors, so a typo cannot be
silently ignored.
"""
import os
import sys

try:
    import tomllib
except ImportError:                     # Python < 3.11
    try:
        import tomli as tomllib
    except ImportError:
        raise SystemExit('reading translation/textures.toml needs Python 3.11+ or `pip install tomli`')

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, '..', '..', 'translation', 'textures.toml')

BACKGROUND = {'transparent': 'T', 'commonest': 'mode', 'edge': 'ring'}
ALIGN = {'old-text': 't', 'centre': 'c', 'left': 'l'}
TEXTURE_KEYS = {'entry', 'name', 'size', 'note', 'line'}
LINE_KEYS = {'japanese', 'english', 'note', 'background', 'box', 'align', 'font', 'max_size', 'squeeze',
             'fill', 'outline', 'rings', 'style', 'shadow', 'move', 'x_min', 'x_max'}
SPRITE_KEYS = {'name', 'size', 'note'}
STYLES = {'auto', 'plain', 'outline', 'shadow'}
FONTS = {'SemiBold', 'Bold', 'BoldItalic'}          # the Inter files in tools/font


class TexDefError(Exception):
    pass


def _colour(v, where):
    if not (isinstance(v, str) and len(v) == 7 and v[0] == '#'):
        raise TexDefError(f'{where}: colour {v!r} must look like "#ffbd65"')
    try:
        int(v[1:], 16)
    except ValueError:
        raise TexDefError(f'{where}: colour {v!r} is not hex') from None
    return v[1:].lower()


def _ints(v, n, where):
    if not (isinstance(v, list) and len(v) == n and all(isinstance(x, int) for x in v)):
        raise TexDefError(f'{where}: expected a list of {n} whole numbers, got {v!r}')
    return v


def _line(entry, k, raw, where):
    bad = set(raw) - LINE_KEYS
    if bad:
        raise TexDefError(f'{where}: unknown key(s) {", ".join(sorted(bad))} (allowed: {", ".join(sorted(LINE_KEYS))})')
    for key in ('japanese', 'english'):
        if not isinstance(raw.get(key), str):
            raise TexDefError(f'{where}: "{key}" is missing or not text')
    if '|' in raw['english']:
        raise TexDefError(f'{where}: write a line break as \\n, not |')
    bg = raw.get('background', ['transparent'])
    if isinstance(bg, str):
        bg = [bg]
    spec = []
    for b in bg:
        if b in BACKGROUND:
            spec.append(BACKGROUND[b])
        elif isinstance(b, str) and b.startswith('#'):
            spec.append('rgb:' + _colour(b, where))
        else:
            raise TexDefError(f'{where}: background {b!r}: use transparent, commonest, edge or a colour "#rrggbb"')
    box = 'auto'
    if 'box' in raw:
        x0, y0, x1, y1 = _ints(raw['box'], 4, f'{where}: box')
        if not (0 <= x0 < x1 and 0 <= y0 < y1):
            raise TexDefError(f'{where}: box {raw["box"]} must be [left, top, right, bottom] with left < right, top < bottom')
        box = f'{x0},{y0},{x1},{y1}'
    align = raw.get('align', 'old-text')
    if align not in ALIGN:
        raise TexDefError(f'{where}: align {align!r}: use old-text, centre or left')
    opts = {}
    if 'font' in raw:
        if raw['font'] not in FONTS:
            raise TexDefError(f'{where}: font {raw["font"]!r}: use one of {", ".join(sorted(FONTS))}')
        opts['font'] = raw['font']
    if 'max_size' in raw:
        if not isinstance(raw['max_size'], (int, float)) or raw['max_size'] < 6:
            raise TexDefError(f'{where}: max_size must be a number of pixels >= 6')
        opts['smax'] = f'{raw["max_size"]:g}'
    if 'squeeze' in raw:
        if not isinstance(raw['squeeze'], (int, float)) or not 0.5 <= raw['squeeze'] <= 1:
            raise TexDefError(f'{where}: squeeze must be between 0.5 and 1')
        opts['squeeze'] = f'{raw["squeeze"]:g}'
    if 'fill' in raw:
        opts['fill'] = _colour(raw['fill'], where)
    if 'outline' in raw:
        cols = raw['outline'] if isinstance(raw['outline'], list) else [raw['outline']]
        opts['outline'] = ','.join(_colour(c, where) for c in cols)
    if 'rings' in raw:
        if not isinstance(raw['rings'], int) or raw['rings'] < 0:
            raise TexDefError(f'{where}: rings must be a whole number >= 0')
        opts['rings'] = str(raw['rings'])
    if 'style' in raw:
        if raw['style'] not in STYLES:
            raise TexDefError(f'{where}: style {raw["style"]!r}: use one of {", ".join(sorted(STYLES))}')
        opts['style'] = raw['style']
    if 'shadow' in raw:
        dx, dy = _ints(raw['shadow'], 2, f'{where}: shadow')
        opts['shadow'] = f'{dx},{dy}'
    if 'move' in raw:
        dx, dy = _ints(raw['move'], 2, f'{where}: move')
        opts['move'] = f'{dx},{dy}'
    for key, o in (('x_min', 'xmin'), ('x_max', 'xmax')):
        if key in raw:
            if not isinstance(raw[key], int):
                raise TexDefError(f'{where}: {key} must be a whole number')
            opts[o] = str(raw[key])
    return {'entry': entry, 'line': k, 'japanese': raw['japanese'], 'english': raw['english'].replace('\n', '|'),
            'notes': raw.get('note', ''), 'bg': ','.join(spec), 'box': box, 'align': ALIGN[align], 'opts': opts}


def load(path=DEFAULT):
    try:
        with open(path, 'rb') as f:
            doc = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise TexDefError(f'{os.path.basename(path)}: {e}') from None
    bad = set(doc) - {'texture', 'sprite'}
    if bad:
        raise TexDefError(f'{os.path.basename(path)}: unknown top-level key(s) {", ".join(sorted(bad))}')
    sprites = {}
    for i, s in enumerate(doc.get('sprite', [])):
        where = f'[[sprite]] #{i + 1}'
        bad = set(s) - SPRITE_KEYS
        if bad:
            raise TexDefError(f'{where}: unknown key(s) {", ".join(sorted(bad))}')
        if not isinstance(s.get('name'), str):
            raise TexDefError(f'{where}: "name" (the sprite-table name, e.g. "sysgraph/menu_set2") is missing')
        w, h = _ints(s.get('size'), 2, f'{where} {s["name"]}: size')
        if s['name'] in sprites:
            raise TexDefError(f'{where}: {s["name"]} is listed twice')
        sprites[s['name']] = (w, h)
    textures = {}
    for i, t in enumerate(doc.get('texture', [])):
        where = f'[[texture]] #{i + 1}'
        bad = set(t) - TEXTURE_KEYS
        if bad:
            raise TexDefError(f'{where}: unknown key(s) {", ".join(sorted(bad))} (allowed: {", ".join(sorted(TEXTURE_KEYS))})')
        e = t.get('entry')
        if not isinstance(e, int) or e < 0:
            raise TexDefError(f'{where}: "entry" (the GRAPH0 entry number) is missing')
        where = f'texture {e}'
        if e in textures:
            raise TexDefError(f'{where}: listed twice')
        lines = t.get('line', [])
        if not lines:
            raise TexDefError(f'{where}: no [[texture.line]]')
        size = tuple(_ints(t['size'], 2, f'{where}: size')) if 'size' in t else None
        textures[e] = {'entry': e, 'name': t.get('name', ''), 'size': size, 'note': t.get('note', ''),
                       'lines': [_line(e, k, raw, f'{where} line {k + 1}') for k, raw in enumerate(lines)]}
    return {'textures': textures, 'sprites': sprites}


def main():
    if len(sys.argv) < 2 or sys.argv[1] != 'check':
        sys.exit(__doc__)
    try:
        d = load(sys.argv[2] if len(sys.argv) > 2 else DEFAULT)
    except TexDefError as e:
        sys.exit(f'error: {e}')
    n = sum(len(t['lines']) for t in d['textures'].values())
    print(f'{len(d["textures"])} textures, {n} lines, {len(d["sprites"])} resized sprites')


if __name__ == '__main__':
    main()
