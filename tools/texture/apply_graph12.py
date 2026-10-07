#!/usr/bin/env python3
"""Write hand-edited GRAPH1/GRAPH2 textures into copies of the archives (D-020).

Usage: apply_graph12.py <orig GRAPH dir> <out dir> [--overrides DIR]

For GRAPH1 and GRAPH2 in turn: if the overrides directory (overrides.py;
$KIMIKISS_OVERRIDES or ../kimikiss-private/texture_overrides) holds
GRAPHn_NNNN.png files, <out dir>/GRAPHn.ARC is written: a copy of the original
with those entries replaced. Without overrides for an archive nothing is
written for it, so the build leaves the file on the disc alone.

GRAPH1.ARC and GRAPH2.ARC have no PAC. The engine opens them as plain
streams (LoadGraph1 0x00104738 and LoadGraph2 0x00104928 open the .ARC and
never touch an LZSS data file; "GRAPH0.PAC" is referenced only by LoadGraph0)
and every entry is a raw TIM2 inside the ARC, so the patch is the same as for
GRAPH0 minus the compression: same-size TIM2 written at the entry's offset.
Every other byte of the file stays as it was; this is verified after writing.

Prints one line per written archive: "wrote <path>".
"""
import mmap
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'extract')]
import arc  # noqa: E402
import overrides  # noqa: E402


def patch_file(src, dst, blobs):
    """Copy src to dst and write blobs {entry: bytes} at their entries; checks that only those bytes changed."""
    with open(src, 'rb') as f:
        orig = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        a = arc.parse(orig)
        for i, blob in blobs.items():
            if len(blob) != a['entries'][i]['size']:
                raise ValueError(f'entry {i}: {len(blob)} bytes, original {a["entries"][i]["size"]}')
        shutil.copyfile(src, dst)
        with open(dst, 'r+b') as out:
            for i, blob in sorted(blobs.items()):
                out.seek(a['entries'][i]['offset'])
                out.write(blob)
        # verify: directory, and every byte outside the replaced entries, identical
        with open(dst, 'rb') as g:
            new = mmap.mmap(g.fileno(), 0, access=mmap.ACCESS_READ)
            if len(new) != len(orig):
                raise ValueError('length changed')
            spans = sorted((a['entries'][i]['offset'], a['entries'][i]['offset'] + a['entries'][i]['size'])
                           for i in blobs)
            pos, step = 0, 1 << 24
            for lo, hi in spans + [(len(orig), len(orig))]:
                while pos < lo:
                    n = min(step, lo - pos)
                    if orig[pos:pos + n] != new[pos:pos + n]:
                        raise ValueError(f'bytes changed outside the replaced entries near {pos:#x}')
                    pos += n
                pos = hi
            new.close()
        orig.close()


def main():
    args = sys.argv[1:]
    ov_dir = None
    if '--overrides' in args:
        i = args.index('--overrides')
        ov_dir = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2:
        sys.exit(__doc__)
    graph_dir, out_dir = args
    try:
        found = overrides.find(ov_dir)
        os.makedirs(out_dir, exist_ok=True)
        for name in ('GRAPH1', 'GRAPH2'):
            entries = found.get(name)
            if not entries:
                continue
            src = os.path.join(graph_dir, name + '.ARC')
            with open(src, 'rb') as f:
                orig = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                blobs, infos = overrides.convert(orig, name, entries)
                orig.close()
            for info in infos:
                print(overrides.describe(info))
                for w in info['warnings']:
                    print('  warning:', w)
            dst = os.path.join(out_dir, name + '.ARC')
            patch_file(src, dst, blobs)
            print(f'wrote {dst}: {len(blobs)} entries replaced')
    except overrides.OverrideError as e:
        sys.exit(f'error: {e}')


if __name__ == '__main__':
    main()
