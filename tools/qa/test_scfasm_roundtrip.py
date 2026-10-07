#!/usr/bin/env python3
"""Disassemble every method of every SCF and reassemble it; bytes must match.

Usage: test_scfasm_roundtrip.py <script_dir>
Checks the opcode table, operand encodings, jump resolution and the pad rule.
"""
import glob
import os
import sys

HERE = os.path.dirname(__file__)
sys.path[:0] = [os.path.join(HERE, '..', 'extract'), os.path.join(HERE, '..', 'reinsert')]
import scf  # noqa: E402
import scfasm  # noqa: E402

bad = total = 0
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.scf'))):
    d = scf.parse(open(f, 'rb').read())
    for name, argc, code in d['methods'] + d['methods2']:
        total += 1
        consts = list(d['constants'])
        out = scfasm.assemble(scfasm.listing(code, consts), consts)
        if out != code or consts != d['constants']:
            bad += 1
            if bad <= 5:
                print(f'MISMATCH {os.path.basename(f)} {name!r}: {len(code)} -> {len(out)} bytes')
print(f'{total - bad}/{total} methods reassemble byte for byte')
print('PASS' if bad == 0 else 'FAIL')
sys.exit(1 if bad else 0)
