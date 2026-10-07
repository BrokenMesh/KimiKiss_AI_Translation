#!/usr/bin/env python3
"""Build a patched disc image from a verified clean copy.

Usage: iso_patch.py <clean.iso> <out.iso> <ISO/PATH=local_file> ...

1. Refuses to run unless the clean image's SHA-1 equals tools/build/iso.sha1.
2. Copies it to <out.iso>; the original is never opened for writing.
3. Each replacement is written in place if it fits the file's slot (up to
   the next file's first sector, or the end of the UDF partition for the
   last file); otherwise it is relocated to the free sectors after the
   last file. If those run out, the image grows (step 6).
4. The file's ISO9660 directory record (LBA and size, both byte orders)
   is updated. The game resolves names with sceCdSearchFile, which reads
   ISO9660 (docs/phase-3-text-engine.md).
5. The file's UDF (E)FE is updated too (decision D-014, docs/formats/iso.md):
   information length, logical blocks recorded, the allocation descriptor,
   then the descriptor tag CRC and checksum.
6. If the image grows: ISO9660 volume space size, UDF partition length in
   both Volume Descriptor Sequences, the LVID size table, and the second
   Anchor (moved to the new last sector) are updated.

tools/qa/check_iso_udf.py verifies the result.
"""
import hashlib
import os
import shutil
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import udf  # noqa: E402

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


def extent_sectors(size):
    return -(-size // SECTOR)


def update_pd_and_lvid(f, u, part_len):
    """Set the partition length in every Partition Descriptor copy and in the LVID size table."""
    for start, count in (u.main_vds, u.reserve_vds):
        for s in range(start, start + count):
            f.seek(s * SECTOR)
            d = bytearray(f.read(SECTOR))
            ident = udf.parse_tag(d)['ident']
            if ident == udf.TAG_TD:
                break
            if ident == udf.TAG_PD:
                struct.pack_into('<I', d, 192, part_len)
                udf.seal_tag(d)
                f.seek(s * SECTOR)
                f.write(d)
    lvid_len, lvid_sector = u.lvid_extent
    f.seek(lvid_sector * SECTOR)
    d = bytearray(f.read(SECTOR))
    if udf.parse_tag(d)['ident'] != udf.TAG_LVID:
        sys.exit('error: no Logical Volume Integrity Descriptor where the LVD says')
    n_parts = struct.unpack_from('<I', d, 72)[0]
    if n_parts != 1:
        sys.exit(f'error: LVID lists {n_parts} partitions; only one is supported')
    struct.pack_into('<I', d, 80 + 4 * n_parts, part_len)    # size table follows the free-space table
    udf.seal_tag(d)
    f.seek(lvid_sector * SECTOR)
    f.write(d)


def grow(f, u, old_total, new_end, extents):
    """Extend the image so the UDF partition ends at sector new_end (exclusive); returns the new total."""
    new_total = new_end + 1                      # one sector for the trailing Anchor
    avdp = bytearray(u.read(u.avdp_sector))
    old_last = old_total - 1
    if not any(lba <= old_last < lba + n for lba, n in extents):
        f.seek(old_last * SECTOR)
        f.write(bytes(SECTOR))                   # old trailing Anchor is no longer last
    f.seek(0, os.SEEK_END)
    if f.tell() < new_total * SECTOR:
        f.truncate(new_total * SECTOR)
    struct.pack_into('<I', avdp, 12, new_total - 1)
    udf.seal_tag(avdp)
    f.seek((new_total - 1) * SECTOR)
    f.write(avdp)
    update_pd_and_lvid(f, u, new_end - u.part_start)
    f.seek(16 * SECTOR)
    pvd = bytearray(f.read(SECTOR))
    struct.pack_into('<I', pvd, 80, new_total)
    struct.pack_into('>I', pvd, 84, new_total)
    f.seek(16 * SECTOR)
    f.write(pvd)
    return new_total


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

        u = udf.Udf(f)
        entries = {e.path: e for e in u.walk() if not e.is_dir}
        if set(entries) != set(by_path):
            sys.exit('error: ISO9660 and UDF disagree on the file list; run tools/qa/check_iso_udf.py')
        for path, (_p, _off, lba, size) in by_path.items():
            e = entries[path]
            if len(e.ads) != 1 or e.ads[0][2] + u.part_start != lba or e.length != size:
                sys.exit(f'error: {path}: ISO9660 ({lba}, {size}) and UDF ({e.ads}, {e.length}) disagree')
        part_end = u.part_start + u.part_len      # exclusive; the sector after it holds the trailing Anchor

        # current extent of every file: path -> (lba, size)
        cur = {p: (r[2], r[3]) for p, r in by_path.items()}
        grown = False
        for spec in repl:
            iso_path, local = spec.split('=', 1)
            rec_off = by_path[iso_path][1]
            data = open(local, 'rb').read()
            lba, size = cur[iso_path]
            others = [(l, s) for p, (l, s) in cur.items() if p != iso_path]
            nxt = min((l for l, _s in others if l > lba), default=part_end)
            slot = (nxt - lba) * SECTOR
            if len(data) <= slot:
                new_lba, where = lba, 'in place'
            else:
                need = extent_sectors(len(data))
                free = max(l + extent_sectors(s) for l, s in others)
                new_lba, where = free, 'relocated'
                if free + need > part_end:
                    where = 'relocated, image grown'
                    grown = True
                    part_end = free + need
                f.seek(lba * SECTOR)
                f.write(bytes(extent_sectors(size) * SECTOR))  # clear the old copy
            f.seek(new_lba * SECTOR)
            f.write(data + bytes(-len(data) % SECTOR))
            cur[iso_path] = (new_lba, len(data))
            f.seek(rec_off + 2)
            f.write(struct.pack('<I', new_lba) + struct.pack('>I', new_lba)
                    + struct.pack('<I', len(data)) + struct.pack('>I', len(data)))
            e = entries[iso_path]
            e.set_single_extent(len(data), new_lba - u.part_start)
            e.seal()
            f.seek(e.sector * SECTOR)
            f.write(e.buf)
            print(f'{iso_path}: {size} -> {len(data)} bytes, LBA {lba} -> {new_lba} ({where})')
        if grown:
            extents = [(l, extent_sectors(s)) for l, s in cur.values()]
            total = grow(f, u, volume, part_end, extents)
            print(f'image grown: {volume} -> {total} sectors, UDF partition length {part_end - u.part_start}')
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
