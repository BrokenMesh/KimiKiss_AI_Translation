#!/usr/bin/env python3
"""ARC container (GRAPH*.ARC, MUSIC.ARC): hashed archive without stored names.

Layout (all LE):
  u32 count, u32 header_size
  u16 bucket_len[count], u16 bucket_start[count]
  count x {u32 flag, u32 hash, u32 offset, u32 size}   (sorted by bucket)
  data
header_size == 8 + count * 20 in every archive on the disc.

Usage: arc.py list <file.arc>
       arc.py unpack <file.arc> <out_dir>
"""
import json
import os
import struct
import sys


def parse(data):
    count, header_size = struct.unpack_from('<II', data, 0)
    if header_size != 8 + count * 20:
        raise ValueError(f'header_size {header_size} != 8 + {count} * 20')
    bucket_len = struct.unpack_from(f'<{count}H', data, 8)
    bucket_start = struct.unpack_from(f'<{count}H', data, 8 + 2 * count)
    entries = []
    base = 8 + 4 * count
    for i in range(count):
        flag, h, off, size = struct.unpack_from('<4I', data, base + 16 * i)
        entries.append({'index': i, 'flag': flag, 'hash': h, 'offset': off, 'size': size})
    return {'count': count, 'header_size': header_size,
            'bucket_len': list(bucket_len), 'bucket_start': list(bucket_start),
            'entries': entries}


def magic(data):
    head = data[:4]
    return head.decode('ascii') if all(0x20 < b < 0x7f for b in head) else head.hex()


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ('list', 'unpack'):
        sys.exit(__doc__)
    data = open(sys.argv[2], 'rb').read()
    arc = parse(data)
    for e in arc['entries']:
        e['magic'] = magic(data[e['offset']:e['offset'] + 4])
    if sys.argv[1] == 'list':
        for e in arc['entries']:
            print(f"{e['index']:5} flag={e['flag']} hash={e['hash']:08x} "
                  f"off={e['offset']:#010x} size={e['size']:9} {e['magic']}")
        return
    out_dir = sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)
    for e in arc['entries']:
        ext = 'tm2' if e['magic'] == 'TIM2' else 'bin'
        with open(os.path.join(out_dir, f"{e['index']:04d}_{e['hash']:08x}.{ext}"), 'wb') as f:
            f.write(data[e['offset']:e['offset'] + e['size']])
    with open(os.path.join(out_dir, 'index.json'), 'w') as f:
        json.dump(arc, f, indent=1)
        f.write('\n')
    print(f"{arc['count']} entries -> {out_dir}")


if __name__ == '__main__':
    main()
