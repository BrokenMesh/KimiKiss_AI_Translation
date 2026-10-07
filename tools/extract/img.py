#!/usr/bin/env python3
"""Unpack SCRIPT.IMG (LZSS-wrapped archive of named members).

Decompressed layout (all LE):
  u32 total_size, u32 count,
  u32 name_offset[count], u32 data_offset[count],
  NUL-terminated ASCII names, member data.
Member i spans data_offset[i] .. data_offset[i+1] (last ends at total_size).

Usage: img.py unpack <SCRIPT.IMG> <out_dir>
Writes <out_dir>/<name>.scf and <out_dir>/index.json (archive order, offsets).
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lzss  # noqa: E402


def parse(data):
    total, count = struct.unpack_from('<II', data, 0)
    if total != len(data):
        raise ValueError(f'header size {total} != data size {len(data)}')
    name_offs = struct.unpack_from(f'<{count}I', data, 8)
    data_offs = struct.unpack_from(f'<{count}I', data, 8 + 4 * count)
    ends = list(data_offs[1:]) + [total]
    members = []
    for i in range(count):
        no = name_offs[i]
        name = data[no:data.index(b'\0', no)].decode('ascii')
        members.append({'name': name, 'name_offset': no,
                        'offset': data_offs[i], 'size': ends[i] - data_offs[i]})
    return members


def unpack(img_path, out_dir):
    raw = open(img_path, 'rb').read()
    data, used = lzss.decompress(raw)
    members = parse(data)
    os.makedirs(out_dir, exist_ok=True)
    for m in members:
        with open(os.path.join(out_dir, m['name'] + '.scf'), 'wb') as f:
            f.write(data[m['offset']:m['offset'] + m['size']])
    index = {'compressed_size': len(raw), 'decompressed_size': len(data),
             'names_start': members[0]['name_offset'] if members else 0,
             'members': members}
    with open(os.path.join(out_dir, 'index.json'), 'w') as f:
        json.dump(index, f, indent=1)
        f.write('\n')
    print(f'{len(members)} members, {len(data)} bytes -> {out_dir}')


if __name__ == '__main__':
    if len(sys.argv) != 4 or sys.argv[1] != 'unpack':
        sys.exit(__doc__)
    unpack(sys.argv[2], sys.argv[3])
