#!/usr/bin/env python3
"""Gate G3 check for textures.

Usage: test_texture_roundtrip.py <work_dir> <file.arc>...

For each archive: unpack, convert every TIM2 to PNG and back, repack, and
require the TIM2 files and the archive to be byte-identical to the input.
Also checks the PS2 alpha <-> PNG alpha mapping is invertible.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(TOOLS, 'extract'))
import tim2  # noqa: E402


def main():
    work, arcs = sys.argv[1], sys.argv[2:]
    failures = 0
    if any(tim2.alpha_from_png(tim2.alpha_to_png(a)) != a for a in range(0x81)):
        print('FAIL alpha mapping is not invertible')
        failures += 1
    for arc_path in arcs:
        name = os.path.basename(arc_path)
        unpacked = os.path.join(work, name)
        shutil.rmtree(unpacked, ignore_errors=True)
        subprocess.run([sys.executable, os.path.join(TOOLS, 'extract', 'arc.py'), 'unpack',
                        arc_path, unpacked], check=True, stdout=subprocess.DEVNULL)
        bad = textures = 0
        for fn in sorted(os.listdir(unpacked)):
            if not fn.endswith('.tm2'):
                continue
            textures += 1
            path = os.path.join(unpacked, fn)
            orig = open(path, 'rb').read()
            back = tim2.from_png(tim2.to_png(tim2.parse(orig)))
            if back != orig:
                bad += 1
                print(f'FAIL {name}/{fn}: TIM2 -> PNG -> TIM2 differs')
            with open(path, 'wb') as f:
                f.write(back)
        rebuilt = os.path.join(work, name + '.rebuilt')
        subprocess.run([sys.executable, os.path.join(TOOLS, 'reinsert', 'arc_pack.py'),
                        unpacked, rebuilt], check=True, stdout=subprocess.DEVNULL)
        same = open(rebuilt, 'rb').read() == open(arc_path, 'rb').read()
        print(f"{'PASS' if same and not bad else 'FAIL'} {name}: {textures} textures via PNG, "
              f"archive {'byte-identical' if same else 'differs'}")
        failures += bad + (not same)
        shutil.rmtree(unpacked)
        os.unlink(rebuilt)
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
