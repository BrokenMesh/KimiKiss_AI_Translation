"""Minimal UDF 1.02 reader/updater for the KimiKiss bridge image.

Shared by tools/build/iso_patch.py (updates file entries) and
tools/qa/check_iso_udf.py (verifies them). Layout notes: docs/formats/iso.md.

All offsets here are byte offsets into the image; `sector` arguments are
absolute 2048-byte sectors. Descriptor tag locations inside the partition
are relative to the partition start (ECMA-167 3/7.2.1 for FSD/FE/FID);
volume descriptors (AVDP, VDS, LVID) carry absolute sector numbers.
"""
import struct

SECTOR = 2048

# Tag identifiers (ECMA-167 3/7.2.1 and 4/7.2.1)
TAG_PVD, TAG_AVDP, TAG_PD, TAG_LVD, TAG_USD, TAG_TD, TAG_LVID = 1, 2, 5, 6, 7, 8, 9
TAG_FSD, TAG_FID, TAG_TERMINAL, TAG_FE, TAG_EFE = 256, 257, 260, 261, 266
# Descriptors whose tag location is partition-relative
PARTITION_RELATIVE = {TAG_FSD, TAG_FID, TAG_FE, TAG_EFE, TAG_TERMINAL, 258, 259, 262, 263, 264, 265}


def _make_crc_table():
    table = []
    for i in range(256):
        c = i << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
        table.append(c)
    return table


_CRC = _make_crc_table()


def crc_itu_t(data):
    """CRC-ITU-T (CRC-16/XMODEM: poly 0x1021, init 0), as in ECMA-167 7.2.6."""
    crc = 0
    for b in data:
        crc = ((crc << 8) & 0xFFFF) ^ _CRC[(crc >> 8) ^ b]
    return crc


def tag_checksum(buf):
    """Sum of tag bytes 0-15 except byte 4, modulo 256."""
    return (sum(buf[:4]) + sum(buf[5:16])) & 0xFF


def parse_tag(buf):
    ident, version, cksum, _res, serial, crc, crc_len, loc = struct.unpack_from('<HHBBHHHI', buf, 0)
    return dict(ident=ident, version=version, checksum=cksum, serial=serial, crc=crc, crc_len=crc_len, loc=loc)


def tag_problems(buf, expect_loc=None):
    """List of problems with the descriptor tag at the start of buf (empty = valid).

    buf must hold at least 16 + crc_len bytes.
    """
    t = parse_tag(buf)
    bad = []
    if tag_checksum(buf) != t['checksum']:
        bad.append(f'tag checksum {t["checksum"]} != computed {tag_checksum(buf)}')
    if t['crc_len'] and 16 + t['crc_len'] <= len(buf):
        c = crc_itu_t(buf[16:16 + t['crc_len']])
        if c != t['crc']:
            bad.append(f'CRC {t["crc"]:#06x} != computed {c:#06x} (length {t["crc_len"]})')
    elif t['crc_len']:
        bad.append(f'CRC length {t["crc_len"]} runs past the buffer')
    if expect_loc is not None and t['loc'] != expect_loc:
        bad.append(f'tag location {t["loc"]} != expected {expect_loc}')
    return bad


def seal_tag(buf, crc_len=None):
    """Recompute CRC (over crc_len bytes after the tag, default: keep the tag's own) and checksum, in place."""
    if crc_len is None:
        crc_len = struct.unpack_from('<H', buf, 10)[0]
    struct.pack_into('<H', buf, 10, crc_len)
    struct.pack_into('<H', buf, 8, crc_itu_t(bytes(buf[16:16 + crc_len])) if crc_len else 0)
    buf[4] = tag_checksum(buf)


class UdfError(Exception):
    pass


class Entry:
    """A directory or file in the UDF tree."""

    def __init__(self, path, is_dir, sector, buf, lbn):
        self.path = path
        self.is_dir = is_dir
        self.sector = sector       # absolute sector of the (E)FE
        self.lbn = lbn             # partition-relative block of the (E)FE
        self.buf = buf             # bytearray of the FE sector(s), as read
        t = parse_tag(buf)
        self.extended = t['ident'] == TAG_EFE
        if self.extended:
            self.off_len, self.off_blocks, self.off_lea = 56, 72, 208
        else:
            self.off_len, self.off_blocks, self.off_lea = 56, 64, 168
        self.length = struct.unpack_from('<Q', buf, self.off_len)[0]
        self.blocks = struct.unpack_from('<Q', buf, self.off_blocks)[0]
        self.l_ea = struct.unpack_from('<I', buf, self.off_lea)[0]
        self.l_ad = struct.unpack_from('<I', buf, self.off_lea + 4)[0]
        self.off_ad = self.off_lea + 8 + self.l_ea
        self.icb_flags = struct.unpack_from('<H', buf, 34)[0]
        self.ad_type = self.icb_flags & 7           # 0 short, 1 long, 2 extended, 3 inline
        self.file_type = buf[27]
        self.desc_len = self.off_ad + self.l_ad
        self.ads = self._parse_ads()

    def _parse_ads(self):
        """[(length_bytes, ext_type, lbn, partition_ref)]; inline data returns []."""
        out = []
        ad = bytes(self.buf[self.off_ad:self.off_ad + self.l_ad])
        if self.ad_type == 0:
            for i in range(0, len(ad), 8):
                v, lbn = struct.unpack_from('<II', ad, i)
                out.append((v & 0x3FFFFFFF, v >> 30, lbn, 0))
        elif self.ad_type == 1:
            for i in range(0, len(ad), 16):
                v, lbn, part = struct.unpack_from('<IIH', ad, i)
                out.append((v & 0x3FFFFFFF, v >> 30, lbn, part))
        elif self.ad_type == 2:
            for i in range(0, len(ad), 20):
                v, _rec, _info, lbn, part = struct.unpack_from('<IIIIH', ad, i)
                out.append((v & 0x3FFFFFFF, v >> 30, lbn, part))
        return out

    def set_single_extent(self, length, lbn):
        """Point a single-extent file at (lbn, length) and fix length/blocks fields. Does not seal."""
        if self.ad_type not in (0, 1):
            raise UdfError(f'{self.path}: unsupported allocation descriptor type {self.ad_type}')
        if len(self.ads) > 1:
            raise UdfError(f'{self.path}: has {len(self.ads)} extents; only single-extent files are supported')
        if length > 0x3FFFFFFF:
            raise UdfError(f'{self.path}: {length} bytes needs more than one extent (limit 1 GiB - 1)')
        blocks = -(-length // SECTOR)
        struct.pack_into('<Q', self.buf, self.off_len, length)
        struct.pack_into('<Q', self.buf, self.off_blocks, blocks)
        if self.extended:
            struct.pack_into('<Q', self.buf, 64, length)    # object size
        if not self.ads:
            # zero-length file with no AD: nothing to point at
            if length:
                raise UdfError(f'{self.path}: has no allocation descriptor to extend')
            return
        if self.ad_type == 0:
            struct.pack_into('<II', self.buf, self.off_ad, length, lbn)
        else:
            struct.pack_into('<IIH', self.buf, self.off_ad, length, lbn, self.ads[0][3])
        self.length, self.blocks = length, blocks
        self.ads = self._parse_ads()

    def seal(self):
        """Recompute the (E)FE tag CRC/checksum. CRC length covers the whole descriptor."""
        seal_tag(self.buf, self.desc_len - 16)


class Udf:
    def __init__(self, f):
        self.f = f
        self.avdp_sector = 256
        self.pvd = self.pd = self.lvd = None
        self.part_start = self.part_len = None
        self.vds_sectors = {}       # ident -> sector (main VDS)
        self.root = None
        self.parse_volume()

    def read(self, sector, n=1):
        self.f.seek(sector * SECTOR)
        return bytearray(self.f.read(n * SECTOR))

    def parse_volume(self):
        avdp = self.read(self.avdp_sector)
        t = parse_tag(avdp)
        if t['ident'] != TAG_AVDP:
            raise UdfError('no Anchor Volume Descriptor Pointer at sector 256')
        self.avdp = avdp
        m_len, m_loc, r_len, r_loc = struct.unpack_from('<IIII', avdp, 16)
        self.main_vds = (m_loc, m_len // SECTOR)
        self.reserve_vds = (r_loc, r_len // SECTOR)
        for i in range(self.main_vds[1]):
            s = self.main_vds[0] + i
            d = self.read(s)
            ident = parse_tag(d)['ident']
            if ident == TAG_TD:
                break
            self.vds_sectors[ident] = s
            if ident == TAG_PVD:
                self.pvd = d
            elif ident == TAG_PD:
                self.pd = d
                self.part_start, self.part_len = struct.unpack_from('<II', d, 188)
                self.part_number = struct.unpack_from('<H', d, 22)[0]
            elif ident == TAG_LVD:
                self.lvd = d
        if not (self.pvd and self.pd and self.lvd):
            raise UdfError('main VDS lacks PVD, partition descriptor or LVD')
        self.block_size = struct.unpack_from('<I', self.lvd, 212)[0]
        if self.block_size != SECTOR:
            raise UdfError(f'unsupported logical block size {self.block_size}')
        # FSD location: long_ad at LVD offset 248
        fsd_len, fsd_lbn, fsd_part = struct.unpack_from('<IIH', self.lvd, 248)
        self.fsd_lbn = fsd_lbn
        fsd = self.read(self.part_start + fsd_lbn)
        if parse_tag(fsd)['ident'] != TAG_FSD:
            raise UdfError('File Set Descriptor not found')
        self.fsd = fsd
        rlen, rlbn, rpart = struct.unpack_from('<IIH', fsd, 400)
        self.root_lbn = rlbn
        l_iu_loc = struct.unpack_from('<II', self.lvd, 432)   # integrity sequence extent (length, sector)
        self.lvid_extent = l_iu_loc

    def read_entry(self, lbn, path):
        sector = self.part_start + lbn
        buf = self.read(sector)
        t = parse_tag(buf)
        if t['ident'] not in (TAG_FE, TAG_EFE):
            raise UdfError(f'{path or "/"}: sector {sector} (block {lbn}) is not a file entry (tag {t["ident"]})')
        return Entry(path, False, sector, buf, lbn)

    def dir_data(self, e):
        out = b''
        for length, _typ, lbn, _part in e.ads:
            self.f.seek((self.part_start + lbn) * SECTOR)
            out += self.f.read(length)
        return out[:e.length]

    def walk(self, entry=None, prefix=''):
        """Yield every Entry below the root (root itself first, path '')."""
        if entry is None:
            entry = self.read_entry(self.root_lbn, '')
            entry.is_dir = True
            yield entry
        data = self.dir_data(entry)
        pos = 0
        while pos + 38 <= len(data):
            t = parse_tag(data[pos:pos + 16])
            if t['ident'] != TAG_FID:
                raise UdfError(f'{prefix or "/"}: expected FID at directory offset {pos}, tag {t["ident"]}')
            chars = data[pos + 18]
            l_fi = data[pos + 19]
            _len, lbn, _part = struct.unpack_from('<IIH', data, pos + 20)
            l_iu = struct.unpack_from('<H', data, pos + 36)[0]
            name_raw = data[pos + 38 + l_iu:pos + 38 + l_iu + l_fi]
            size = (38 + l_iu + l_fi + 3) & ~3
            if not chars & 0x08 and not chars & 0x04:    # not deleted, not parent
                if name_raw and name_raw[0] == 8:
                    name = name_raw[1:].decode('latin-1')
                elif name_raw and name_raw[0] == 16:
                    name = name_raw[1:].decode('utf-16-be')
                else:
                    name = name_raw.decode('latin-1')
                path = prefix + name
                child = self.read_entry(lbn, path)
                child.is_dir = bool(chars & 0x02)
                child.fid_offset = pos
                yield child
                if child.is_dir:
                    yield from self.walk(child, path + '/')
            pos += size

    # ---- volume-level updates -------------------------------------------------

    def lvid_sector(self):
        return self.lvid_extent[1]
