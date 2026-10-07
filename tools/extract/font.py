#!/usr/bin/env python3
"""Dump the dialogue font (GRAPH0.ARC entry 77, hash 0xffc76f47) as a PNG grid.

The TIM2 is a 672 x 4384 4bpp container, but each 672-pixel row is one
24 x 28 glyph stored row-major (24 * 28 = 672). Glyph g is JIS X 0208
row g // 94 + 1, cell g % 94 + 1, i.e. Shift-JIS order starting at 0x8140.

Usage: font.py <GRAPH0.ARC> <out.png> [first_glyph] [count]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arc  # noqa: E402
import tim2  # noqa: E402

FONT_ENTRY = 77
GW, GH = 24, 28
COLS = 94


def load(arc_path):
    data = open(arc_path, 'rb').read()
    e = arc.parse(data)['entries'][FONT_ENTRY]
    font = tim2.parse(data[e['offset']:e['offset'] + e['size']])
    if (font['w'], font['bpp']) != (GW * GH, 4):
        raise ValueError('entry 77 is not the 24x28 font sheet')
    return font


def glyph(font, g):
    return font['indices'][g * GW * GH:(g + 1) * GW * GH]


def sjis_of(g):
    row, cell = g // 94 + 1, g % 94 + 1
    j1, j2 = row + 0x20, cell + 0x20
    s1 = (j1 + 1) // 2 + (0x70 if j1 <= 0x5E else 0xB0)
    s2 = j2 + (0x1F if j1 % 2 else 0x7E)
    if j1 % 2 and s2 >= 0x7F:
        s2 += 1
    return s1 << 8 | s2


def main():
    arc_path, out = sys.argv[1:3]
    first = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    font = load(arc_path)
    total = font['h']
    count = int(sys.argv[4]) if len(sys.argv) > 4 else total - first
    rows = -(-count // COLS)
    w, h = COLS * GW, rows * GH
    pix = bytearray(w * h)
    for k in range(count):
        src = glyph(font, first + k)
        gx, gy = (k % COLS) * GW, (k // COLS) * GH
        for y in range(GH):
            pix[(gy + y) * w + gx:(gy + y) * w + gx + GW] = src[y * GW:(y + 1) * GW]
    pal = [(255 - 17 * i, 255 - 17 * i, 255 - 17 * i, 0x80) for i in range(16)]
    with open(out, 'wb') as f:
        f.write(tim2.to_png({'header': font['header'], 'w': w, 'h': h, 'bpp': 8,
                             'swizzled': False, 'palette': pal, 'indices': bytes(pix)}))
    print(f'glyphs {first}..{first + count - 1} (SJIS {sjis_of(first):04X}..'
          f'{sjis_of(first + count - 1):04X}) -> {out}')


if __name__ == '__main__':
    main()
