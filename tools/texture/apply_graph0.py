#!/usr/bin/env python3
"""Rebuild GRAPH0.ARC/PAC with the English font and the redrawn textures (D-019).

Usage: apply_graph0.py <orig GRAPH0.ARC> <out GRAPH0.ARC> <out GRAPH0.PAC>
                       [--no-textures] [--overrides DIR] [--report report.json]

One pass over the original archive:
  * entry 77 (dialogue font): English glyphs, as tools/font/apply_en_font.py;
  * every texture of tools/texture/labels.tsv: Japanese text replaced by
    English (redraw.py);
  * every GRAPH0_NNNN.png of the overrides directory (hand-edited textures,
    overrides.py, D-020; $KIMIKISS_OVERRIDES or ../kimikiss-private/texture_overrides)
    replaces its entry instead of the automatic redraw.
Each replaced entry keeps its exact length (same palette, same size), so no ARC
offset or size changes, and every other entry stays byte-identical; both are
checked before anything is written. The engine reads the ARC header as the
directory and the LZSS-compressed PAC as the data (LoadGraph0, 0x00104410), so
both files are written.

Needs Pillow and numpy for the textures (not for the font).
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'font'), os.path.join(HERE, '..', 'extract'),
                os.path.join(HERE, '..', 'reinsert')]
import arc  # noqa: E402
import apply_en_font  # noqa: E402
from img_pack import lzss_encoder  # noqa: E402


def replace_entries(arc_data, blobs):
    """Return arc_data with entry index -> bytes replaced; sizes must not change."""
    a = arc.parse(arc_data)
    out = bytearray(arc_data)
    for i, blob in blobs.items():
        e = a['entries'][i]
        if len(blob) != e['size']:
            raise ValueError(f'entry {i}: {len(blob)} bytes, original {e["size"]}')
        out[e['offset']:e['offset'] + e['size']] = blob
    return bytes(out)


def check_untouched(orig, new, changed):
    """Directory identical; entries outside `changed` byte-identical."""
    a, b = arc.parse(orig), arc.parse(new)
    if len(orig) != len(new) or a['entries'] != b['entries'] or orig[:a['header_size']] != new[:b['header_size']]:
        raise ValueError('ARC directory or length changed')
    bad = [e['index'] for e in a['entries'] if e['index'] not in changed
           and orig[e['offset']:e['offset'] + e['size']] != new[e['offset']:e['offset'] + e['size']]]
    if bad:
        raise ValueError(f'entries changed that should not: {bad[:10]}')


def build(orig, textures=True, found=None):
    """-> (new ARC bytes, set of changed entries, texture reports)

    found: {entry: PNG path} of GRAPH0 overrides (None = none); they replace the
    redraw of their entry.
    """
    data = apply_en_font.patch_font(orig, apply_en_font.load_cells())
    changed, reports = {apply_en_font.FONT_ENTRY}, []
    if textures:
        import overrides
        import redraw
        ov, ov_infos = overrides.convert(orig, 'GRAPH0', found or {})
        blobs, reports = redraw.redraw_arc(orig, skip=set(ov))
        if apply_en_font.FONT_ENTRY in blobs:
            raise ValueError('a label points at the font entry')
        blobs.update(ov)
        reports += [dict(i, override=True, flags=i['warnings']) for i in ov_infos]
        data = replace_entries(data, blobs)
        changed |= set(blobs)
    check_untouched(orig, data, changed)
    return data, changed, reports


def main():
    args = sys.argv[1:]
    textures = '--no-textures' not in args
    args = [a for a in args if a != '--no-textures']
    report = None
    ov_dir = None
    if '--overrides' in args:
        i = args.index('--overrides')
        ov_dir = args[i + 1]
        del args[i:i + 2]
    if '--report' in args:
        i = args.index('--report')
        report = args[i + 1]
        del args[i:i + 2]
    if len(args) != 3:
        sys.exit(__doc__)
    src, out_arc, out_pac = args
    found = {}
    try:
        if textures:
            import overrides
            found = overrides.find(ov_dir).get('GRAPH0', {})
        data, changed, reports = build(open(src, 'rb').read(), textures, found)
    except Exception as e:
        if type(e).__name__ != 'OverrideError':
            raise
        sys.exit(f'error: {e}')
    for r in reports:
        if r.get('override'):
            print(overrides.describe(r))
            for w in r['warnings']:
                print('  warning:', w)
    with open(out_arc, 'wb') as f:
        f.write(data)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(data)
    try:
        subprocess.run([lzss_encoder(), tmp.name, out_pac], check=True)
    finally:
        os.unlink(tmp.name)
    if report:
        with open(report, 'w') as f:
            json.dump(reports, f, indent=1, ensure_ascii=False,
                      default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    flagged = {r['entry'] for r in reports if r['flags'] and not r.get('override')}
    print(f'{out_arc}: {len(data)} bytes, {len(changed)} entries replaced '
          f'(font + {len(changed) - 1} textures, {len(found)} of them hand-edited, {len(flagged)} flagged); '
          f'{out_pac}: {os.path.getsize(out_pac)} bytes')


if __name__ == '__main__':
    main()
