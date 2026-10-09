#!/usr/bin/env python3
"""Check hand-edited texture overrides (D-020).

Usage: test_graph_overrides.py <orig GRAPH dir>
       test_graph_overrides.py <orig GRAPH dir> --iso <built.iso> --overrides <dir>

Mode 1 (default) makes a temporary overrides directory under build/ (ignored by
git) with a rectangle drawn into a GRAPH0 texture without label, a GRAPH0
texture with a label, a GRAPH1 and a GRAPH2 texture (RGBA PNGs), an indexed PNG
with a new palette, and checks:
  * an unmodified PNG (indexed export or RGBA copy) converts to the identical TIM2;
  * a drawn rectangle changes only pixels inside it, the TIM2 keeps header,
    length and palette (RGBA) or takes the new palette and the same indices
    (indexed, same palette size);
  * GRAPH0: the entry is replaced, the redraw of a labelled entry gives way
    to the override, every other entry equals the build without overrides, the
    PAC decompresses to the ARC;
  * GRAPH1/GRAPH2: the output has the same length and differs from the
    original only inside the overridden entries, which hold the converted TIM2;
  * wrong size, unknown entry, entry that is not a TIM2, the font entry, an
    unknown name, two files for one entry and an overrides directory inside the
    repo (not ignored) are refused with a message;
  * no overrides directory: apply_graph12 writes nothing.

Mode 2 checks a built ISO against an overrides directory: for every override the
ISO9660 file holds the converted entry, all other bytes of GRAPH1/GRAPH2 equal the
original, GRAPH0.PAC decompresses to a GRAPH0.ARC with the same entries.
"""
import mmap
import os
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.realpath(os.path.join(HERE, '..', '..'))
TOOLS = os.path.join(REPO, 'tools')
sys.path[:0] = [os.path.join(TOOLS, 'texture'), os.path.join(TOOLS, 'extract'), os.path.join(TOOLS, 'font'),
                os.path.join(TOOLS, 'build')]
import apply_graph0  # noqa: E402
import apply_graph12  # noqa: E402
import arc  # noqa: E402
import lzss  # noqa: E402
import overrides  # noqa: E402
import redraw  # noqa: E402
import sprites  # noqa: E402
import texdefs  # noqa: E402
import tim2  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

FAILS = []


def check(ok, msg):
    if not ok:
        FAILS.append(msg)
        print('FAIL', msg)


def entry_blob(data, a, i):
    e = a['entries'][i]
    return bytes(data[e['offset']:e['offset'] + e['size']])


def refused(fn, needle):
    try:
        fn()
    except overrides.OverrideError as e:
        return needle in str(e)
    return False


def same_outside(orig, new, spans):
    """True if orig and new (buffers) are equal everywhere except in the (lo, hi) spans."""
    if len(orig) != len(new):
        return False
    pos, step = 0, 1 << 24
    for lo, hi in sorted(spans) + [(len(orig), len(orig))]:
        while pos < lo:
            n = min(step, lo - pos)
            if orig[pos:pos + n] != new[pos:pos + n]:
                return False
            pos += n
        pos = hi
    return True


def rect_png(blob, path, rect=(4, 4, 12, 10), colour=(255, 0, 0, 255), indexed=False):
    """Export `blob` as PNG with a rectangle drawn in. Returns the rectangle and the PNG's pixel array."""
    t = tim2.parse(blob)
    open(path, 'wb').write(tim2.to_png(t))
    if indexed:
        # new palette, same size: entry 1 becomes the drawing colour, indices of the rectangle point to it
        im = Image.open(path)
        idx = np.array(im)
        x0, y0, x1, y1 = rect
        idx[y0:y1, x0:x1] = 1
        pal = list(im.getpalette())[:768]
        pal[3:6] = colour[:3]
        out = Image.fromarray(idx, 'P')
        out.putpalette(pal)
        trns = bytearray(im.info['transparency'])
        trns[1] = 255
        out.save(path, transparency=bytes(trns))
        return rect
    rgba = np.array(Image.open(path).convert('RGBA'))
    x0, y0, x1, y1 = rect
    rgba[y0:y1, x0:x1] = colour
    Image.fromarray(rgba, 'RGBA').save(path)
    return rect


def run_synthetic(graph_dir):
    work = tempfile.mkdtemp(prefix='ov_', dir=os.path.join(REPO, 'build'))
    try:
        _run(graph_dir, work)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _run(graph_dir, work):
    arcs = {}
    for n in ('GRAPH0', 'GRAPH1', 'GRAPH2'):
        f = open(os.path.join(graph_dir, n + '.ARC'), 'rb')
        data = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        arcs[n] = (data, arc.parse(data))
    labels = redraw.load_labels()
    labelled = sorted(labels)[0]
    plain0 = next(i for i, e in enumerate(arcs['GRAPH0'][1]['entries'])
                  if i not in labels and i != 77 and arcs['GRAPH0'][0][e['offset']:e['offset'] + 4] == b'TIM2')
    g1 = 58
    g2 = next(i for i, e in enumerate(arcs['GRAPH2'][1]['entries'])
              if i >= 10 and arcs['GRAPH2'][0][e['offset']:e['offset'] + 4] == b'TIM2')
    d = os.path.join(work, 'ov')
    os.makedirs(d)

    # 1. an unmodified PNG gives the identical TIM2, in both modes
    for n, i in (('GRAPH0', plain0), ('GRAPH1', g1), ('GRAPH2', g2)):
        blob = entry_blob(arcs[n][0], arcs[n][1], i)
        p = os.path.join(work, 'plain.png')
        open(p, 'wb').write(tim2.to_png(tim2.parse(blob)))
        out, info = overrides.to_tim2(p, blob)
        check(out == blob and info['mode'] == 'palette' and info['changed'] == 0, f'{n} {i}: indexed export not identical')
        Image.open(p).convert('RGBA').save(p)
        out, info = overrides.to_tim2(p, blob)
        check(out == blob and info['mode'] == 'quantized' and info['changed'] == 0, f'{n} {i}: RGBA copy not identical')

    # 2. drawn rectangles
    rects = {}
    for name, n, i, kw in (('GRAPH0_%04d.png' % plain0, 'GRAPH0', plain0, {}),
                           ('GRAPH0_%04d.png' % labelled, 'GRAPH0', labelled, {}),
                           ('GRAPH1_%04d.png' % g1, 'GRAPH1', g1, {}),
                           ('GRAPH2_%04d.png' % g2, 'GRAPH2', g2, {'indexed': True})):
        blob = entry_blob(arcs[n][0], arcs[n][1], i)
        rects[(n, i)] = rect_png(blob, os.path.join(d, name), **kw)
    found = overrides.find(d)
    check({k: sorted(v) for k, v in found.items()} == {'GRAPH0': sorted([plain0, labelled]), 'GRAPH1': [g1], 'GRAPH2': [g2]},
          'find() did not see the files')
    conv = {}
    for n in ('GRAPH0', 'GRAPH1', 'GRAPH2'):
        conv[n], infos = overrides.convert(arcs[n][0], n, found[n])
        for info in infos:
            print('  ', overrides.describe(info), info['warnings'])
        for i, out in conv[n].items():
            blob = entry_blob(arcs[n][0], arcs[n][1], i)
            to, tn = tim2.parse(blob), tim2.parse(out)
            check(len(out) == len(blob) and out[:64] == blob[:64], f'{n} {i}: length/header changed')
            x0, y0, x1, y1 = rects[(n, i)]
            w = to['w']
            diff = [k for k in range(len(to['indices'])) if to['indices'][k] != tn['indices'][k]]
            check(bool(diff), f'{n} {i}: nothing changed')
            check(all(x0 <= k % w < x1 and y0 <= k // w < y1 for k in diff), f'{n} {i}: pixels changed outside the rectangle')
            if (n, i) == ('GRAPH2', g2):
                check(tn['palette'] != to['palette'] and tn['palette'][1][:3] == (255, 0, 0)
                      and all(tn['palette'][k] == to['palette'][k] for k in range(2, 256)),
                      'GRAPH2: indexed override did not carry its palette')
                check(tn['palette'][1][3] == 128, 'GRAPH2: opaque PNG entry is not PS2 alpha 0x80')
                check(all(tn['indices'][k] == 1 for k in diff), 'GRAPH2: rectangle indices wrong')
            else:
                check(tn['palette'] == to['palette'], f'{n} {i}: palette changed in the RGBA path')

    # 3. GRAPH0 build: override replaces the entry and the redraw of a labelled entry
    orig0 = bytes(arcs['GRAPH0'][0])
    elf = open(os.path.join(os.path.dirname(os.path.abspath(graph_dir)), 'SLPS_258.50'), 'rb').read()
    base, base_changed, _ = apply_graph0.build(orig0, elf=elf)
    new, changed, reports = apply_graph0.build(orig0, True, found['GRAPH0'], elf)
    check(changed == base_changed | {plain0}, 'GRAPH0 changed set != base + plain override')
    an, ab = arc.parse(new), arc.parse(base)       # larger sprites (D-035) move offsets: read each directory
    for e in an['entries']:
        i = e['index']
        got = entry_blob(new, an, i)
        if i in conv['GRAPH0']:
            check(got == conv['GRAPH0'][i], f'GRAPH0 {i}: not the converted override')
        else:
            check(got == entry_blob(base, ab, i), f'GRAPH0 {i}: differs from the build without overrides')
    check(entry_blob(new, an, labelled) != entry_blob(base, ab, labelled), 'labelled entry still redrawn')
    check(sum(1 for r in reports if r.get('override')) == 2, 'override reports missing')
    check(new == apply_graph0.build(orig0, True, found['GRAPH0'], elf)[0], 'override build is not deterministic')
    # an override of a resized sprite's texture must have the larger size
    defs = texdefs.load()
    grown = sorted(sprites.resolve(elf, orig0, defs['sprites'])[0])
    if grown:
        g = grown[0]
        small = os.path.join(work, 'small.png')
        open(small, 'wb').write(tim2.to_png(tim2.parse(entry_blob(arcs['GRAPH0'][0], arcs['GRAPH0'][1], g))))
        try:
            apply_graph0.build(orig0, True, {g: small}, elf)
            check(False, f'GRAPH0 {g}: an override of the old size was accepted for a larger sprite')
        except overrides.OverrideError as e:
            check('[[sprite]]' in str(e), f'GRAPH0 {g}: unclear refusal: {e}')
    out_arc, out_pac = os.path.join(work, 'g0.arc'), os.path.join(work, 'g0.pac')
    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'texture', 'apply_graph0.py'),
                        os.path.join(graph_dir, 'GRAPH0.ARC'), out_arc, out_pac, '--overrides', d],
                       capture_output=True, text=True)
    check(r.returncode == 0 and open(out_arc, 'rb').read() == new, 'apply_graph0 CLI output differs from build()')
    check(lzss.decompress(open(out_pac, 'rb').read())[0] == new, 'PAC does not decompress to the built archive')

    # 4. GRAPH1 / GRAPH2 files
    out_dir = os.path.join(work, 'out')
    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'texture', 'apply_graph12.py'),
                        graph_dir, out_dir, '--overrides', d], capture_output=True, text=True)
    check(r.returncode == 0, f'apply_graph12 failed: {r.stderr}')
    for n in ('GRAPH1', 'GRAPH2'):
        with open(os.path.join(out_dir, n + '.ARC'), 'rb') as f:
            built = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            a = arcs[n][1]
            spans = [(a['entries'][i]['offset'], a['entries'][i]['offset'] + a['entries'][i]['size']) for i in conv[n]]
            check(same_outside(arcs[n][0], built, spans), f'{n}.ARC differs outside the overridden entries')
            for i, out in conv[n].items():
                check(entry_blob(built, a, i) == out, f'{n} {i}: entry is not the converted override')
            built.close()
    empty = os.path.join(work, 'empty')
    os.makedirs(empty)
    out2 = os.path.join(work, 'out2')
    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'texture', 'apply_graph12.py'),
                        graph_dir, out2, '--overrides', empty], capture_output=True, text=True)
    check(r.returncode == 0 and not (os.path.isdir(out2) and os.listdir(out2)),
          'apply_graph12 wrote files without overrides')

    # 5. refusals
    bad = os.path.join(work, 'bad')

    def fresh(*files):
        shutil.rmtree(bad, ignore_errors=True)
        os.makedirs(bad)
        for name, src in files:
            shutil.copy(os.path.join(d, src), os.path.join(bad, name))
        return bad

    src1 = 'GRAPH1_%04d.png' % g1
    blob1 = entry_blob(arcs['GRAPH1'][0], arcs['GRAPH1'][1], g1)
    wrong = os.path.join(work, 'wrong.png')
    Image.new('RGBA', (639, 448)).save(wrong)
    check(refused(lambda: overrides.to_tim2(wrong, blob1), 'size must not change'), 'wrong size accepted')
    check(refused(lambda: overrides.convert(arcs['GRAPH1'][0], 'GRAPH1', {9999: os.path.join(d, src1)}), 'no entry 9999'),
          'unknown entry accepted')
    nont = next(i for i, e in enumerate(arcs['GRAPH0'][1]['entries']) if arcs['GRAPH0'][0][e['offset']:e['offset'] + 4] != b'TIM2')
    check(refused(lambda: overrides.convert(arcs['GRAPH0'][0], 'GRAPH0', {nont: os.path.join(d, src1)}), 'not a TIM2'),
          'non-TIM2 entry accepted')
    check(refused(lambda: overrides.convert(arcs['GRAPH0'][0], 'GRAPH0', {77: os.path.join(d, src1)}), 'font'),
          'font entry accepted')
    check(refused(lambda: overrides.find(fresh(('GRAPH5_0001.png', src1))), 'not a texture name'), 'bad archive name accepted')
    check(refused(lambda: overrides.find(fresh(('foo.png', src1))), 'not a texture name'), 'bad file name accepted')
    check(refused(lambda: overrides.find(fresh(('GRAPH1_0058.png', src1), ('GRAPH1_58.png', src1))), 'both'),
          'duplicate entry accepted')
    check(refused(lambda: overrides.find(os.path.join(work, 'nope')), 'does not exist'), 'missing dir accepted')
    check(refused(lambda: overrides.find(os.path.join(REPO, 'tools')), 'inside the repository'), 'in-repo dir accepted')
    junk = os.path.join(work, 'junk.png')
    open(junk, 'wb').write(b'not a png')
    check(refused(lambda: overrides.to_tim2(junk, blob1), 'cannot read PNG'), 'junk file accepted')
    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'texture', 'apply_graph12.py'), graph_dir,
                        os.path.join(work, 'out3'), '--overrides', fresh(('GRAPH1_9999.png', src1))],
                       capture_output=True, text=True)
    check(r.returncode != 0 and 'no entry 9999' in r.stderr, 'apply_graph12 did not fail clearly on an unknown entry')


def run_iso(graph_dir, iso, directory):
    import iso_patch
    found = overrides.find(directory)
    with open(iso, 'rb') as f:
        f.seek(16 * 2048)
        pvd = f.read(2048)
        root = pvd[156:190]
        files = {p: (lba, size) for p, _o, lba, size in iso_patch.records(
            f, struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0])}
        m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        def file(path):
            lba, size = files[path]
            return m[lba * 2048:lba * 2048 + size]

        for n in ('GRAPH0', 'GRAPH1', 'GRAPH2'):
            with open(os.path.join(graph_dir, n + '.ARC'), 'rb') as g:
                orig = mmap.mmap(g.fileno(), 0, access=mmap.ACCESS_READ)
                a = arc.parse(orig)
                blobs, _ = overrides.convert(orig, n, found.get(n, {}))
                if n == 'GRAPH0':
                    built = lzss.decompress(bytes(file('GRAPH/GRAPH0.PAC')))[0]
                    check(bytes(file('GRAPH/GRAPH0.ARC')) == built, 'ISO: GRAPH0.PAC does not decompress to GRAPH0.ARC')
                    for i, b in blobs.items():
                        check(entry_blob(built, a, i) == b, f'ISO: GRAPH0 {i} is not the override')
                    print(f'ISO GRAPH0: {len(blobs)} overrides present')
                    continue
                data = file(f'GRAPH/{n}.ARC')
                if not blobs:
                    check(same_outside(orig, data, []), f'ISO: {n}.ARC changed without overrides')
                    print(f'ISO {n}: untouched')
                    continue
                spans = [(a['entries'][i]['offset'], a['entries'][i]['offset'] + a['entries'][i]['size']) for i in blobs]
                check(same_outside(orig, data, spans), f'ISO: {n}.ARC differs outside the overridden entries')
                for i, b in blobs.items():
                    check(entry_blob(data, a, i) == b, f'ISO: {n} {i} is not the override')
                print(f'ISO {n}: {len(blobs)} overrides present, rest identical')


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    graph_dir = args[0]
    if '--iso' in args:
        run_iso(graph_dir, args[args.index('--iso') + 1], args[args.index('--overrides') + 1])
    else:
        run_synthetic(graph_dir)
    print('FAIL' if FAILS else 'PASS')
    sys.exit(1 if FAILS else 0)


if __name__ == '__main__':
    main()
