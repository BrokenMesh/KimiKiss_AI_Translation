#!/usr/bin/env python3
"""Rebuild an ARC archive from a directory written by `arc.py unpack`.

Usage: arc_pack.py <unpacked_dir> <out.arc>

Entry table, hashes, flags and bucket tables are kept from index.json. Data
is laid out contiguously in the original offset order, so unchanged inputs
reproduce the original archive byte for byte.
"""
import json
import os
import struct
import sys


def main():
    src_dir, out_path = sys.argv[1:3]
    arc = json.load(open(os.path.join(src_dir, 'index.json')))
    entries = arc['entries']
    count = arc['count']
    blobs = {}
    for e in entries:
        ext = 'tm2' if e['magic'] == 'TIM2' else 'bin'
        blobs[e['index']] = open(os.path.join(src_dir, f"{e['index']:04d}_{e['hash']:08x}.{ext}"), 'rb').read()
    pos = 8 + 20 * count
    data = bytearray()
    placed = {}
    for e in sorted(entries, key=lambda e: e['offset']):
        placed[e['index']] = (pos + len(data), len(blobs[e['index']]))
        data += blobs[e['index']]
    out = bytearray(struct.pack('<II', count, 8 + 20 * count))
    out += struct.pack(f'<{count}H', *arc['bucket_len'])
    out += struct.pack(f'<{count}H', *arc['bucket_start'])
    for e in entries:
        off, size = placed[e['index']]
        out += struct.pack('<4I', e['flag'], e['hash'], off, size)
    with open(out_path, 'wb') as f:
        f.write(out + data)
    print(f'{count} entries, {len(out) + len(data)} bytes -> {out_path}')


if __name__ == '__main__':
    main()
