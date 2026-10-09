#!/usr/bin/env python3
"""Render the English glyph set once from an OTF/TTF into tools/font/.

Usage: render_en_font.py <font.otf> <size_px> <out_dir>

Writes en_font.pgm (95 cells of 24 x 28, 16-level coverage stored as 0..15)
and en_widths.json (advance in pixels at scale 1.0, per character). These
outputs are committed so the build does not depend on the font file or
Pillow. Run only when changing the font. Requires Pillow.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

GW, GH = 24, 28
BASELINE = 20    # last pixel row of capitals; 3 px above the Japanese Latin (row 24) so
                 # descenders end on row 25 like the Japanese glyphs (D-033)
LAST_ROW = 25    # lowest ink row; the game does not show row 27 of a cell (D-033)
LEFT = 1         # pen x at the start of the cell
TRACKING = 0     # extra pixels per advance


def main():
    path, size, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    font = ImageFont.truetype(path, size)
    ascent, _ = font.getmetrics()
    sheet = Image.new('L', (GW * 95, GH), 0)
    widths = {}
    for i in range(95):
        ch = chr(0x20 + i)
        cell = Image.new('L', (GW, GH), 0)
        # draw with the baseline at BASELINE + 1 (pixel row BASELINE is the last ink row)
        ImageDraw.Draw(cell).text((LEFT, BASELINE + 1 - ascent), ch, font=font, fill=255)
        bbox = font.getbbox(ch)
        ink = cell.getbbox()
        top = BASELINE + 1 - ascent + bbox[1]
        bottom = BASELINE + 1 - ascent + bbox[3] - 1
        if ink and (ink[0] == 0 and LEFT + bbox[0] < 0 or ink[2] >= GW or top < 0 or bottom > LAST_ROW):
            print(f'warning: {ch!r} is clipped: ink rows {top}..{bottom}, cell rows 0..{LAST_ROW}', file=sys.stderr)
        sheet.paste(cell, (i * GW, 0))
        widths[ch] = round(font.getlength(ch)) + TRACKING
    q = bytes(round(v * 15 / 255) for v in sheet.tobytes())
    with open(os.path.join(out, 'en_font.pgm'), 'wb') as f:
        f.write(f'P5\n{GW * 95} {GH}\n15\n'.encode() + q)
    meta = {'source': os.path.basename(path), 'size_px': size, 'cell': [GW, GH],
            'baseline_row': BASELINE, 'left': LEFT, 'tracking': TRACKING, 'widths': widths}
    with open(os.path.join(out, 'en_widths.json'), 'w') as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
    print(f'{len(widths)} glyphs; widths {min(widths.values())}..{max(widths.values())}; '
          f'"The quick brown fox" = {sum(widths[c] for c in "The quick brown fox")} px')


if __name__ == '__main__':
    main()
