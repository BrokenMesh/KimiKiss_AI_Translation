#!/usr/bin/env python3
"""Verify that a KimiKiss disc image is consistent in ISO9660 and UDF.

Usage: check_iso_udf.py <image.iso>        (read-only; exit 1 on any error)

Checks, for the ISO9660 tree and the UDF bridge tree of the same image:
  - ISO9660 PVD volume size equals the file size; directory records are
    well formed and both byte orders agree.
  - Volume Recognition Sequence (BEA01, NSR02/03, TEA01), both Anchors,
    both Volume Descriptor Sequences: tag checksum, CRC-ITU-T, tag location;
    main and reserve sequences agree.
  - Partition lies inside the image; LVID size table equals the partition
    length; the File Set Descriptor and every File Entry / Extended File
    Entry / File Identifier Descriptor has a valid tag, CRC and location.
  - Every file is present in both trees with the same LBA and size, its
    UDF information length / logical blocks recorded / allocation
    descriptors are consistent, and no two files overlap or leave the
    partition.
Layout notes: docs/formats/iso.md. The image is only ever opened for reading.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build'))
import udf  # noqa: E402

SECTOR = 2048


class Report:
    def __init__(self):
        self.errors = []
        self.notes = []

    def err(self, msg):
        self.errors.append(msg)

    def note(self, msg):
        self.notes.append(msg)


def check_tag(rep, what, buf, expect_loc=None, accept_loc=()):
    """Validate a tag; buf must hold the whole descriptor (at least 16 + CRC length bytes)."""
    probs = udf.tag_problems(buf, expect_loc)
    if expect_loc is not None and any(p.startswith('tag location') for p in probs) and \
            udf.parse_tag(buf)['loc'] in accept_loc:
        probs = [p for p in probs if not p.startswith('tag location')]
    for p in probs:
        rep.err(f'{what}: {p}')
    return not probs


def iso_walk(f, lba, size, prefix, rep, out_files, out_dirs):
    f.seek(lba * SECTOR)
    data = f.read(size)
    pos = 0
    while pos < size:
        length = data[pos]
        if length == 0:
            pos = (pos // SECTOR + 1) * SECTOR
            continue
        rec = data[pos:pos + length]
        l_fi = rec[32]
        name = rec[33:33 + l_fi]
        r_lba, r_lba_be, r_size, r_size_be = struct.unpack_from('<I', rec, 2)[0], struct.unpack_from('>I', rec, 6)[0], \
            struct.unpack_from('<I', rec, 10)[0], struct.unpack_from('>I', rec, 14)[0]
        if name not in (b'\x00', b'\x01'):
            path = prefix + name.decode('ascii').split(';')[0]
            if (r_lba, r_size) != (r_lba_be, r_size_be):
                rep.err(f'ISO9660 {path}: little/big-endian LBA or size disagree '
                        f'({r_lba}/{r_lba_be}, {r_size}/{r_size_be})')
            if rec[25] & 2:
                out_dirs.append(path)
                iso_walk(f, r_lba, r_size, path + '/', rep, out_files, out_dirs)
            else:
                out_files[path] = (r_lba, r_size)
        pos += length


def check_vds(rep, f, u, start, count, label):
    """Validate one Volume Descriptor Sequence; returns {sector offset: descriptor body} for comparison."""
    bodies = []
    for i in range(count):
        s = start + i
        f.seek(s * SECTOR)
        d = f.read(SECTOR)
        t = udf.parse_tag(d)
        if t['ident'] == 0 and not any(d):
            continue
        ok = check_tag(rep, f'{label} descriptor at sector {s}', d, s)
        bodies.append((i, t['ident'], d[16:16 + t['crc_len']] if ok else None))
        if t['ident'] == udf.TAG_TD:
            break
    else:
        rep.err(f'{label}: no Terminating Descriptor within {count} sectors')
    return bodies


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    rep = Report()
    total_bytes = os.path.getsize(path)
    total = total_bytes // SECTOR
    if total_bytes % SECTOR:
        rep.err(f'image size {total_bytes} is not a multiple of {SECTOR}')

    with open(path, 'rb') as f:
        # ---- ISO9660 ----
        f.seek(16 * SECTOR)
        pvd = f.read(SECTOR)
        if pvd[:6] != b'\x01CD001':
            sys.exit('error: no ISO9660 primary volume descriptor at sector 16')
        vol_le, vol_be = struct.unpack_from('<I', pvd, 80)[0], struct.unpack_from('>I', pvd, 84)[0]
        if vol_le != vol_be:
            rep.err(f'ISO9660 volume space size LE {vol_le} != BE {vol_be}')
        if vol_le != total:
            rep.err(f'ISO9660 volume space size {vol_le} sectors != image size {total} sectors')
        root = pvd[156:190]
        iso_files, iso_dirs = {}, []
        iso_walk(f, struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0], '', rep,
                 iso_files, iso_dirs)

        # ---- UDF volume recognition sequence ----
        seq = []
        for s in range(16, 40):
            f.seek(s * SECTOR)
            d = f.read(6)
            if d[1:6] in (b'BEA01', b'NSR02', b'NSR03', b'TEA01'):
                seq.append((s, d[1:6].decode()))
        ids = [x[1] for x in seq]
        if not ids or ids[0] != 'BEA01' or ids[-1] != 'TEA01' or not any(i.startswith('NSR') for i in ids):
            rep.err(f'volume recognition sequence incomplete: {seq}')
        nsr = next((i for i in ids if i.startswith('NSR')), None)

        try:
            u = udf.Udf(f)
        except udf.UdfError as ex:
            rep.err(f'UDF: {ex}')
            return finish(rep, path, total, nsr, None, iso_files, iso_dirs)

        # ---- anchors ----
        anchors = []
        for s in (256, total - 256, total - 1):
            if 0 < s < total:
                f.seek(s * SECTOR)
                d = f.read(SECTOR)
                if udf.parse_tag(d)['ident'] == udf.TAG_AVDP:
                    anchors.append(s)
                    check_tag(rep, f'AVDP at sector {s}', d, s)
                    if d[16:32] != u.avdp[16:32]:
                        rep.err(f'AVDP at sector {s} points to a different VDS than the one at 256')
                elif s != total - 256:
                    rep.err(f'no Anchor Volume Descriptor Pointer at sector {s}')
        # ---- VDS main / reserve ----
        main_b = check_vds(rep, f, u, *u.main_vds, 'main VDS')
        res_b = check_vds(rep, f, u, *u.reserve_vds, 'reserve VDS')
        if [(i, t, b) for i, t, b in main_b] != [(i, t, b) for i, t, b in res_b]:
            rep.err('main and reserve Volume Descriptor Sequences differ')

        # ---- partition, LVID ----
        part_end = u.part_start + u.part_len
        if part_end > total:
            rep.err(f'UDF partition ends at sector {part_end}, beyond the image ({total} sectors)')
        for a in anchors:
            if u.part_start <= a < part_end:
                rep.err(f'Anchor at sector {a} lies inside the UDF partition')
        lvid_len, lvid_s = u.lvid_extent
        f.seek(lvid_s * SECTOR)
        lvid = f.read(SECTOR)
        n_files = n_dirs = None
        if check_tag(rep, f'LVID at sector {lvid_s}', lvid, lvid_s):
            n_parts = struct.unpack_from('<I', lvid, 72)[0]
            sizes = struct.unpack_from(f'<{n_parts}I', lvid, 80 + 4 * n_parts)
            if sizes[0] != u.part_len:
                rep.err(f'LVID size table {sizes[0]} != partition length {u.part_len}')
            l_iu = struct.unpack_from('<I', lvid, 76)[0]
            iu = lvid[80 + 8 * n_parts:80 + 8 * n_parts + l_iu]
            if len(iu) >= 40:
                n_files, n_dirs = struct.unpack_from('<II', iu, 32)
        f.seek((lvid_s + 1) * SECTOR)
        check_tag(rep, f'terminator after LVID (sector {lvid_s + 1})', f.read(SECTOR), lvid_s + 1)
        fsd = u.fsd
        check_tag(rep, f'FSD (block {u.fsd_lbn})', fsd[:16 + udf.parse_tag(fsd)['crc_len']], u.fsd_lbn)
        # The mastering tool tags the descriptor that ends the FSD sequence with its absolute
        # sector rather than the partition-relative block; accept either.
        fsd_term = u.part_start + u.fsd_lbn + 1
        f.seek(fsd_term * SECTOR)
        check_tag(rep, f'terminator after FSD (sector {fsd_term})', f.read(SECTOR), fsd_term,
                  accept_loc=(u.fsd_lbn + 1,))

        # ---- tree ----
        udf_files, udf_dirs, extents = {}, [], []
        n_f = n_d = 0
        for e in u.walk():
            t = udf.parse_tag(e.buf)
            check_tag(rep, f'UDF {e.path or "/"} file entry (block {e.lbn})', e.buf[:16 + t['crc_len']], e.lbn)
            if t['crc_len'] != e.desc_len - 16:
                rep.err(f'UDF {e.path or "/"}: CRC length {t["crc_len"]} != descriptor length {e.desc_len} - 16')
            if e.is_dir:
                n_d += 1
                udf_dirs.append(e.path)
                data = u.dir_data(e)
                check_fids(rep, u, e, data)
                continue
            n_f += 1
            if e.ad_type not in (0, 1) or not e.ads:
                rep.err(f'UDF {e.path}: unsupported or empty allocation descriptors (type {e.ad_type})')
                continue
            ad_total = sum(a[0] for a in e.ads)
            if ad_total != e.length:
                rep.err(f'UDF {e.path}: allocation descriptors cover {ad_total} bytes, information length {e.length}')
            if e.blocks != -(-e.length // SECTOR):
                rep.err(f'UDF {e.path}: logical blocks recorded {e.blocks} != {-(-e.length // SECTOR)}')
            if any(a[1] != 0 for a in e.ads):
                rep.err(f'UDF {e.path}: allocation descriptor not of type "recorded and allocated"')
            if len(e.ads) != 1:
                rep.note(f'UDF {e.path}: {len(e.ads)} extents; only the first is compared with ISO9660')
            length, _typ, lbn, _part = e.ads[0]
            udf_files[e.path] = (u.part_start + lbn, e.length)
            for ln, _t, lb, _p in e.ads:
                extents.append((u.part_start + lb, -(-ln // SECTOR), e.path))
                if lb + -(-ln // SECTOR) > u.part_len:
                    rep.err(f'UDF {e.path}: extent block {lb}+{-(-ln // SECTOR)} outside the partition '
                            f'(length {u.part_len})')
        if n_files is not None and (n_files, n_dirs) != (n_f, n_d):
            rep.err(f'LVID counts {n_files} files / {n_dirs} directories, tree has {n_f} / {n_d}')

        # ---- agreement ----
        for p in sorted(set(iso_files) | set(udf_files)):
            a, b = iso_files.get(p), udf_files.get(p)
            if a is None:
                rep.err(f'{p}: in UDF only')
            elif b is None:
                rep.err(f'{p}: in ISO9660 only')
            elif a != b:
                rep.err(f'{p}: ISO9660 (LBA {a[0]}, size {a[1]}) != UDF (LBA {b[0]}, size {b[1]})')
        if sorted(iso_dirs) != sorted(d for d in udf_dirs if d):
            rep.err(f'directory lists differ: ISO9660 {sorted(iso_dirs)} vs UDF {sorted(d for d in udf_dirs if d)}')
        # ---- overlap ----
        extents.sort()
        for (a_lba, a_n, a_p), (b_lba, _b_n, b_p) in zip(extents, extents[1:]):
            if a_lba + a_n > b_lba:
                rep.err(f'extents overlap: {a_p} [{a_lba}, {a_lba + a_n}) and {b_p} starting at {b_lba}')
        return finish(rep, path, total, nsr, u, iso_files, iso_dirs, udf_files, extents, anchors)


def check_fids(rep, u, d, data):
    """Walk the FIDs of directory entry d, validating each tag."""
    pos = 0
    base_lbn = d.ads[0][2] if d.ads else 0
    while pos + 38 <= len(data):
        l_fi = data[pos + 19]
        l_iu = struct.unpack_from('<H', data, pos + 36)[0]
        size = (38 + l_iu + l_fi + 3) & ~3
        t = udf.parse_tag(data[pos:pos + 16])
        if t['ident'] != udf.TAG_FID:
            rep.err(f'UDF {d.path or "/"}: bad FID tag {t["ident"]} at offset {pos}')
            return
        blk = base_lbn + pos // SECTOR
        check_tag(rep, f'UDF {d.path or "/"} FID at offset {pos}', data[pos:pos + size], blk)
        pos += size


def finish(rep, path, total, nsr, u, iso_files, iso_dirs, udf_files=None, extents=None, anchors=None):
    print(f'image: {path}')
    print(f'  size: {total} sectors, ISO9660 files: {len(iso_files)}, directories: {len(iso_dirs)}')
    if u is not None:
        print(f'  UDF: {nsr}, anchors at {anchors}, partition start {u.part_start} length {u.part_len} '
              f'(ends {u.part_start + u.part_len}), root block {u.root_lbn}')
        print(f'  UDF files: {len(udf_files or {})}; highest used sector: '
              f'{max((a + n for a, n, _p in extents), default=0)}')
    for n in rep.notes:
        print(f'  note: {n}')
    if rep.errors:
        print(f'FAIL: {len(rep.errors)} problem(s)')
        for e in rep.errors:
            print(f'  - {e}')
        return 1
    print('PASS: ISO9660 and UDF agree; all UDF tags and CRCs valid')
    return 0


if __name__ == '__main__':
    sys.exit(main())
