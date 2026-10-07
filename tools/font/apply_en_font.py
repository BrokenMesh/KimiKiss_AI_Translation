#!/usr/bin/env python3
"""Write the English glyphs into the dialogue font and rebuild GRAPH0.ARC/PAC.

Usage: apply_en_font.py <orig GRAPH0.ARC> <out GRAPH0.ARC> <out GRAPH0.PAC>

Reads tools/font/en_font.pgm (95 cells of 24 x 28, values 0..15) and puts
cell i at the glyph of the Shift-JIS code for chr(0x20 + i) (decision
D-012). Only pixels of entry 77 change, so every ARC offset and size stays
the same. The engine reads the ARC header as the directory and the
LZSS-compressed PAC as the data (LoadGraph0, 0x00104410), so both are
written. Pure Python plus the LZSS encoder in tools/lzss.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'extract'), os.path.join(HERE, '..', 'reinsert')]
import arc  # noqa: E402
import encoding  # noqa: E402
import tim2  # noqa: E402
from img_pack import lzss_encoder  # noqa: E402

FONT_ENTRY, GW, GH = 77, 24, 28


def load_cells(path=os.path.join(HERE, 'en_font.pgm')):
    data = open(path, 'rb').read()
    magic, dims, maxval, rest = data.split(b'\n', 3)
    w, h = map(int, dims.split())
    if magic != b'P5' or (w, h, int(maxval)) != (GW * 95, GH, 15):
        raise ValueError('unexpected en_font.pgm layout')
    return [bytes(rest[y * w + i * GW:y * w + (i + 1) * GW][x] for y in range(GH) for x in range(GW))
            for i in range(95)]


def patch_font(arc_data, cells):
    e = arc.parse(arc_data)['entries'][FONT_ENTRY]
    blob = arc_data[e['offset']:e['offset'] + e['size']]
    t = tim2.parse(blob)
    idx = bytearray(t['indices'])
    for i, cell in enumerate(cells):
        g = encoding.glyph_index(encoding.code_of(chr(0x20 + i)))
        idx[g * GW * GH:(g + 1) * GW * GH] = cell
    new = tim2.build(t['header'], t['w'], t['h'], t['bpp'], t['swizzled'], t['palette'], bytes(idx))
    if len(new) != len(blob):
        raise ValueError('font TIM2 changed size')
    return arc_data[:e['offset']] + new + arc_data[e['offset'] + e['size']:]


def main():
    src, out_arc, out_pac = sys.argv[1:4]
    data = patch_font(open(src, 'rb').read(), load_cells())
    with open(out_arc, 'wb') as f:
        f.write(data)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(data)
    try:
        subprocess.run([lzss_encoder(), tmp.name, out_pac], check=True)
    finally:
        os.unlink(tmp.name)
    print(f'{out_arc}: {len(data)} bytes; {out_pac}: {os.path.getsize(out_pac)} bytes')


if __name__ == '__main__':
    main()
