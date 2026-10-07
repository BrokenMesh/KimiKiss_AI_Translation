#!/usr/bin/env python3
"""Build a patched disc image from a verified clean copy.

Usage: iso_patch.py <clean.iso> <out.iso> <ISO/PATH=local_file> ...

1. Refuses to run unless the clean image's SHA-1 equals tools/build/iso.sha1.
2. Copies it to <out.iso>; the original is never opened for writing.
3. Each replacement is written in place if it fits the file's slot (up to
   the next file's first sector); otherwise it is relocated to the free
   sectors after the last file, inside the existing volume.
4. The file's ISO9660 directory record (LBA and size, both byte orders)
   is updated. The game resolves names with sceCdSearchFile, which reads
   ISO9660 (docs/phase-3-text-engine.md).

The UDF bridge descriptors are not updated (decision D-014): PS2 hardware
and PCSX2 read ISO9660 only.
"""
import hashlib
import os
import shutil
import struct
import sys

SECTOR = 2048
HERE = os.path.dirname(os.path.abspath(__file__))


def sha1_file(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 22), b''):
            h.update(chunk)
    return h.hexdigest()


def records(f, lba, size, prefix=''):
    """Yield (path, record_offset, lba, size) for every file, recursively."""
    f.seek(lba * SECTOR)
    data = f.read(size)
    pos = 0
    while pos < size:
        length = data[pos]
        if length == 0:
            pos = (pos // SECTOR + 1) * SECTOR
            continue
        rec = data[pos:pos + length]
        name = rec[33:33 + rec[32]]
        if name not in (b'\x00', b'\x01'):
            path = prefix + name.decode('ascii').split(';')[0]
            r_lba, r_size = struct.unpack_from('<I', rec, 2)[0], struct.unpack_from('<I', rec, 10)[0]
            if rec[25] & 2:
                yield from records(f, r_lba, r_size, path + '/')
            else:
                yield path, lba * SECTOR + pos, r_lba, r_size
        pos += length


def main():
    clean, out, *repl = sys.argv[1:]
    want = open(os.path.join(HERE, 'iso.sha1')).read().split()[0]
    got = sha1_file(clean)
    if got != want:
        sys.exit(f'error: {clean} SHA-1 {got} does not match recorded {want}')
    if os.path.abspath(out) == os.path.abspath(clean):
        sys.exit('error: output must differ from the clean image')
    shutil.copyfile(clean, out)
    os.chmod(out, 0o600)

    with open(out, 'r+b') as f:
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)
        volume = struct.unpack_from('<I', pvd, 80)[0]
        root = pvd[156:190]
        files = sorted(records(f, struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0]),
                       key=lambda r: r[2])
        by_path = {r[0]: r for r in files}
        free = max(r[2] + -(-r[3] // SECTOR) for r in files)
        for spec in repl:
            iso_path, local = spec.split('=', 1)
            path, rec_off, lba, size = by_path[iso_path]
            data = open(local, 'rb').read()
            nxt = min((r[2] for r in files if r[2] > lba), default=volume)
            slot = (nxt - lba) * SECTOR
            if len(data) <= slot:
                new_lba, where = lba, 'in place'
            else:
                need = -(-len(data) // SECTOR)
                if free + need > volume:
                    sys.exit(f'error: no room for {iso_path} ({need} sectors) inside the volume')
                new_lba, free, where = free, free + need, 'relocated'
                f.seek(lba * SECTOR)
                f.write(bytes(-(-size // SECTOR) * SECTOR))  # clear the old copy
            f.seek(new_lba * SECTOR)
            f.write(data + bytes(-len(data) % SECTOR))
            f.seek(rec_off + 2)
            f.write(struct.pack('<I', new_lba) + struct.pack('>I', new_lba)
                    + struct.pack('<I', len(data)) + struct.pack('>I', len(data)))
            print(f'{iso_path}: {size} -> {len(data)} bytes, LBA {lba} -> {new_lba} ({where})')
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
