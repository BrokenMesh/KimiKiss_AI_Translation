#!/usr/bin/env python3
"""Extract an ISO9660 image and write a manifest of every file.

The manifest records each file's path, LBA, size, and SHA-1 so later build
steps can patch files in place at their original sectors.

Usage: iso_extract.py <image.iso> <out_dir> <manifest.json>
"""
import hashlib
import json
import os
import struct
import sys

SECTOR = 2048


def read_dir(f, lba, size):
    f.seek(lba * SECTOR)
    data = f.read(size)
    pos = 0
    while pos < size:
        length = data[pos]
        if length == 0:
            pos = (pos // SECTOR + 1) * SECTOR
            continue
        rec = data[pos:pos + length]
        name_len = rec[32]
        name = rec[33:33 + name_len]
        if name not in (b'\x00', b'\x01'):
            yield {
                'name': name.decode('ascii').split(';')[0],
                'lba': struct.unpack_from('<I', rec, 2)[0],
                'size': struct.unpack_from('<I', rec, 10)[0],
                'is_dir': bool(rec[25] & 2),
            }
        pos += length


def walk(f, lba, size, prefix=''):
    for entry in read_dir(f, lba, size):
        path = prefix + entry['name']
        if entry['is_dir']:
            yield from walk(f, entry['lba'], entry['size'], path + '/')
        else:
            yield path, entry['lba'], entry['size']


def main():
    iso_path, out_dir, manifest_path = sys.argv[1:4]
    with open(iso_path, 'rb') as f:
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)
        if pvd[1:6] != b'CD001':
            sys.exit('error: no ISO9660 primary volume descriptor')
        root = pvd[156:190]
        root_lba = struct.unpack_from('<I', root, 2)[0]
        root_size = struct.unpack_from('<I', root, 10)[0]
        volume_sectors = struct.unpack_from('<I', pvd, 80)[0]

        files = []
        for path, lba, size in walk(f, root_lba, root_size):
            f.seek(lba * SECTOR)
            data = f.read(size)
            dest = os.path.join(out_dir, path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'wb') as out:
                out.write(data)
            files.append({'path': path, 'lba': lba, 'size': size,
                          'sha1': hashlib.sha1(data).hexdigest()})

    files.sort(key=lambda e: e['lba'])
    manifest = {'volume_sectors': volume_sectors, 'files': files}
    with open(manifest_path, 'w') as out:
        json.dump(manifest, out, indent=1)
        out.write('\n')
    print(f'{len(files)} files, {sum(e["size"] for e in files)} bytes -> {out_dir}')


if __name__ == '__main__':
    main()
