#!/usr/bin/env python3
"""Check the GRAPH0 rewrite (font + redrawn textures, D-019).

Usage: test_graph0_textures.py <orig GRAPH0.ARC> [built GRAPH0.PAC]

Builds the patched archive in memory and requires:
  * same length and same ARC directory; every entry outside {font, labelled
    textures} is byte-identical to the original;
  * a redrawn texture keeps its TIM2 header, palette and size, differs from the
    original only inside its label boxes, and does change there;
  * the build is deterministic (two runs give the same bytes);
  * labels are printable ASCII and point at TIM2 entries;
  * if a built PAC is given, it decompresses to the built archive (the engine
    reads the PAC).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(TOOLS, 'texture'), os.path.join(TOOLS, 'extract'), os.path.join(TOOLS, 'font')]
import apply_graph0  # noqa: E402
import arc  # noqa: E402
import lzss  # noqa: E402
import redraw  # noqa: E402
import tim2  # noqa: E402


def main():
    orig = open(sys.argv[1], 'rb').read()
    fails = []

    def check(ok, msg):
        if not ok:
            fails.append(msg)
            print('FAIL', msg)

    new, changed, _ = apply_graph0.build(orig)
    again, _, _ = apply_graph0.build(orig)
    check(new == again, 'build is not deterministic')
    a = arc.parse(orig)
    check(len(new) == len(orig), 'archive length changed')
    labels = redraw.load_labels()
    check(changed == {apply_graph0.apply_en_font.FONT_ENTRY} | set(labels), 'changed set != font + labels')
    same = 0
    for e in a['entries']:
        i = e['index']
        o = orig[e['offset']:e['offset'] + e['size']]
        n = new[e['offset']:e['offset'] + e['size']]
        if i not in changed:
            check(o == n, f'entry {i} changed but has no label')
            same += 1
    for i, lines in labels.items():
        e = a['entries'][i]
        o = orig[e['offset']:e['offset'] + e['size']]
        n = new[e['offset']:e['offset'] + e['size']]
        check(o[:4] == b'TIM2', f'entry {i} is not a TIM2')
        for l in lines:
            check(all(0x20 <= ord(c) < 0x7F for c in l['english'].replace('|', ' ')),
                  f'entry {i}: english is not ASCII')
        to, tn = tim2.parse(o), tim2.parse(n)
        check(tn['palette'] == to['palette'] and tn['header'] == to['header']
              and (tn['w'], tn['h']) == (to['w'], to['h']), f'entry {i}: header/palette/size differ')
        tex = redraw.Tex(o)
        allowed = [redraw.auto_box(tex, l) for l in lines]
        w = to['w']
        diff = [k for k in range(len(to['indices'])) if to['indices'][k] != tn['indices'][k]]
        outside = [k for k in diff if not any(b[0] <= k % w < b[2] and b[1] <= k // w < b[3] for b in allowed)]
        check(not outside, f'entry {i}: {len(outside)} pixels changed outside the label boxes')
        check(bool(diff), f'entry {i}: nothing changed')
    if len(sys.argv) > 2:
        pac = open(sys.argv[2], 'rb').read()
        check(lzss.decompress(pac)[0] == new, 'PAC does not decompress to the built archive')
    print(f'{same} untouched entries identical; {len(labels)} textures redrawn; '
          f'{"FAIL" if fails else "PASS"}')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
