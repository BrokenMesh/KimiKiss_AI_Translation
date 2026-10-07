#!/usr/bin/env python3
"""Rebuild SCRIPT.IMG from a directory of .scf members.

Usage: img_pack.py <script_dir> <out.img>

Member order and names come from <script_dir>/index.json (written by
img.py unpack). Names follow the two offset tables, data follows the names,
then the whole archive is LZSS-compressed with tools/lzss/lzss_enc.c, which
reproduces the original SCRIPT.IMG byte for byte.
"""
import json
import os
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
ENC_SRC = os.path.join(ROOT, 'tools', 'lzss', 'lzss_enc.c')
ENC_BIN = os.path.join(ROOT, 'build', 'bin', 'lzss_enc')


def lzss_encoder():
    if not os.path.exists(ENC_BIN) or os.path.getmtime(ENC_BIN) < os.path.getmtime(ENC_SRC):
        os.makedirs(os.path.dirname(ENC_BIN), exist_ok=True)
        subprocess.run(['gcc', '-O2', '-Wall', '-o', ENC_BIN, ENC_SRC], check=True)
    return ENC_BIN


def build(script_dir):
    index = json.load(open(os.path.join(script_dir, 'index.json')))
    members = index['members']
    count = len(members)
    names = bytearray()
    name_offs = []
    names_start = 8 + 8 * count
    for m in members:
        name_offs.append(names_start + len(names))
        names += m['name'].encode('ascii') + b'\0'
    data = bytearray()
    data_offs = []
    data_start = names_start + len(names)
    for m in members:
        data_offs.append(data_start + len(data))
        data += open(os.path.join(script_dir, m['name'] + '.scf'), 'rb').read()
    total = data_start + len(data)
    out = struct.pack('<II', total, count)
    out += struct.pack(f'<{count}I', *name_offs) + struct.pack(f'<{count}I', *data_offs)
    return out + names + data


def main():
    script_dir, out_path = sys.argv[1:3]
    raw = build(script_dir)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(raw)
    try:
        subprocess.run([lzss_encoder(), tmp.name, out_path], check=True)
    finally:
        os.unlink(tmp.name)
    print(f'{len(raw)} bytes -> {out_path} ({os.path.getsize(out_path)} compressed)')


if __name__ == '__main__':
    main()
