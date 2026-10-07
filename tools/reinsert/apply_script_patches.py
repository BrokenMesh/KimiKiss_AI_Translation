#!/usr/bin/env python3
"""Apply the bytecode patches in patches/scripts/ to unpacked SCF members.

Usage: apply_script_patches.py <script_dir> <patch_dir>

Each patch file replaces one method. Its header names the target and pins
the original bytecode:

  ; target: <Class> <method> argc=<n> table=<methods|methods2>
  ; original-sha1: <sha1 of the original bytecode>

A patch headed `; add: <Class> <method> argc=<n> table=<...>` instead
appends a new method; it is refused if a different method of that name
and argc already exists.
A patch is refused if the method in <script_dir> matches neither the
original hash nor the patched result (so applying twice is a no-op).
`@EN_WIDTHS` is replaced by a float array constant holding the advance
widths of codes 0x8540..0x859F from tools/font/en_widths.json (trail 0x7F,
which does not exist, gets 0). `@EN_SYMBOLS` is replaced by an int array
constant of 0x5F entries indexed by (code - 0x8140): the English code of each
full-width symbol 0x8140..0x819E that has an ASCII twin (name entry, D-016),
0 for the others. Members are modified in place.
"""
import glob
import hashlib
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'extract'), os.path.join(HERE, '..', 'font')]
import encoding  # noqa: E402
import scf  # noqa: E402
import scfasm  # noqa: E402


def width_array():
    widths = json.load(open(os.path.join(HERE, '..', 'font', 'en_widths.json')))['widths']
    out = []
    for k in range(0x60):
        ch = encoding.char_of(0x8540 + k)
        out.append((3, struct.pack('<f', float(widths[ch]) if ch else 0.0)))
    return (8, out)


# full-width symbol (Shift-JIS row 1/2) -> ASCII character with an English glyph.
# The slash, backslash and bar are left out: 0x815E and 0x8162 are the engine's
# line-break and pause codes.
SYMBOLS = {'　': ' ', '，': ',', '．': '.', '：': ':', '；': ';', '？': '?', '！': '!', '＾': '^', '＿': '_',
           '‐': '-', '～': '~', '‘': "'", '’': "'", '“': '"', '”': '"', '（': '(', '）': ')', '［': '[',
           '］': ']', '＋': '+', '－': '-', '＝': '=', '＜': '<', '＞': '>', '＄': '$', '％': '%', '＃': '#',
           '＆': '&', '＊': '*', '＠': '@'}


def symbol_array():
    table = [0] * 0x5F
    for full, ascii_ch in SYMBOLS.items():
        code = int.from_bytes(full.encode('cp932'), 'big')
        table[code - 0x8140] = encoding.code_of(ascii_ch)
    return (8, [(1, struct.pack('<i', v)) for v in table])


def apply(script_dir, patch_path, widths, symbols):
    text = open(patch_path, encoding='utf-8').read()
    m = re.search(r'^; (target|add): (\S+) (\S+) argc=(\d+) table=(methods2?)$', text, re.M)
    h = re.search(r'^; original-sha1: ([0-9a-f]{40})', text, re.M)
    if not (m and (h or m.group(1) == 'add')):
        raise ValueError(f'{patch_path}: missing target or original-sha1 header')
    kind, cls, meth, argc, table = m.group(1), m.group(2), m.group(3).encode(), int(m.group(4)), m.group(5)
    path = os.path.join(script_dir, cls + '.scf')
    d = scf.parse(open(path, 'rb').read())
    consts = d['constants']
    idx = consts.index(widths) if widths in consts else None
    if '@EN_WIDTHS' in text:
        if idx is None:
            consts.append(widths)
            idx = len(consts) - 1
        text = text.replace('@EN_WIDTHS', f'idx:{idx}')
    if '@EN_SYMBOLS' in text:
        if symbols not in consts:
            consts.append(symbols)
        text = text.replace('@EN_SYMBOLS', f'idx:{consts.index(symbols)}')
    new = scfasm.assemble(text, consts)
    hits = [i for i, (n, a, _) in enumerate(d[table]) if n == meth and a == argc]
    if kind == 'add':
        if hits:
            if d[table][hits[0]][2] == new:
                return f'{cls}>>{meth.decode()}: already added'
            raise ValueError(f'{patch_path}: {cls}>>{meth.decode()} argc={argc} already exists, refusing')
        d[table].append((meth, argc, new))
        open(path, 'wb').write(scf.serialize(d))
        return f'{cls}>>{meth.decode()}: added, {len(new)} bytes'
    if len(hits) != 1:
        raise ValueError(f'{patch_path}: {len(hits)} methods match {cls}>>{meth.decode()} argc={argc}')
    old = d[table][hits[0]][2]
    if old == new:
        return f'{cls}>>{meth.decode()}: already patched'
    if hashlib.sha1(old).hexdigest() != h.group(1):
        raise ValueError(f'{patch_path}: original bytecode hash mismatch, refusing')
    d[table][hits[0]] = (meth, argc, new)
    open(path, 'wb').write(scf.serialize(d))
    return f'{cls}>>{meth.decode()}: {len(old)} -> {len(new)} bytes'


def main():
    script_dir, patch_dir = sys.argv[1:3]
    widths, symbols = width_array(), symbol_array()
    for p in sorted(glob.glob(os.path.join(patch_dir, '*.asm'))):
        print(apply(script_dir, p, widths, symbols))


if __name__ == '__main__':
    main()
