#!/usr/bin/env python3
"""Lossless TIM2 <-> indexed PNG conversion for the textures on this disc.

Every TIM2 here has one picture, no mipmaps, a 48-byte picture header and a
32-bit CLUT stored in CSM1 order. Image types: 5 = 8bpp (256 colours) and
4 = 4bpp (the font sheet, 64 CLUT entries = 4 palettes of 16).

The PNG is 8-bit indexed with the full CLUT as its palette (de-swizzled for
8bpp). Alpha goes to tRNS: scaled from PS2 0..128 to 0..255 when every entry
is <= 0x80, otherwise copied raw (some GRAPH1 palettes use 0xFF). The mode,
bpp, CLUT order and the original 64 header bytes ride along in a tEXt chunk
("tim2"), so png -> tim2 restores them.

Usage: tim2.py topng <in.tm2> <out.png>
       tim2.py totim2 <in.png> <out.tm2>
"""
import struct
import sys
import zlib

PNG_SIG = b'\x89PNG\r\n\x1a\n'


def csm1(i):
    """CSM1 swaps entries 8-15 and 16-23 in each block of 32 (an involution)."""
    b = i & 0x18
    return i + 8 if b == 8 else i - 8 if b == 16 else i


def alpha_to_png(a):
    if a > 0x80:
        raise ValueError(f'alpha {a:#x} above 0x80 cannot round-trip')
    return (a * 255 + 64) // 128


def alpha_from_png(a):
    return (a * 128 + 127) // 255


def parse(data):
    if data[:4] != b'TIM2' or struct.unpack_from('<H', data, 6)[0] != 1:
        raise ValueError('expected a one-picture TIM2')
    (total, clut_size, img_size, hdr_size, colors, _fmt, mips, clut_type, img_type,
     w, h) = struct.unpack_from('<IIIHHBBBBHH', data, 16)
    if hdr_size != 48 or mips != 1 or clut_type & 0x7F != 3 or img_type not in (4, 5):
        raise ValueError(f'unsupported TIM2 (hdr {hdr_size}, mips {mips}, '
                         f'clut {clut_type:#x}, img {img_type})')
    if 16 + total != len(data) or total != 48 + img_size + clut_size:
        raise ValueError('TIM2 size fields disagree with data length')
    bpp = 8 if img_type == 5 else 4
    if img_size != w * h * bpp // 8 or clut_size != colors * 4:
        raise ValueError('unexpected image or CLUT size')
    pixels = data[64:64 + img_size]
    clut = data[64 + img_size:]
    swizzled = bpp == 8 and not clut_type & 0x80
    palette = []
    for i in range(colors):
        src = csm1(i) if swizzled else i
        palette.append(tuple(clut[4 * src:4 * src + 4]))
    if bpp == 4:
        indices = bytearray()
        for b in pixels:
            indices += bytes((b & 0x0F, b >> 4))
    else:
        indices = bytearray(pixels)
    return {'header': data[:64], 'w': w, 'h': h, 'bpp': bpp, 'swizzled': swizzled,
            'palette': palette, 'indices': bytes(indices)}


def build(header, w, h, bpp, swizzled, palette, indices):
    if bpp == 4:
        pixels = bytes(indices[i] | indices[i + 1] << 4 for i in range(0, len(indices), 2))
    else:
        pixels = bytes(indices)
    clut = bytearray(4 * len(palette))
    for i, rgba in enumerate(palette):
        dst = csm1(i) if swizzled else i
        clut[4 * dst:4 * dst + 4] = bytes(rgba)
    hdr = bytearray(header)
    struct.pack_into('<III', hdr, 16, 48 + len(pixels) + len(clut), len(clut), len(pixels))
    struct.pack_into('<H', hdr, 30, len(palette))
    struct.pack_into('<HH', hdr, 36, w, h)
    return bytes(hdr) + pixels + bytes(clut)


def _chunk(kind, body):
    return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))


def to_png(t):
    w, h = t['w'], t['h']
    raw = b''.join(b'\0' + t['indices'][y * w:(y + 1) * w] for y in range(h))
    plte = b''.join(bytes(c[:3]) for c in t['palette'])
    scaled = all(c[3] <= 0x80 for c in t['palette'])
    trns = bytes(alpha_to_png(c[3]) if scaled else c[3] for c in t['palette'])
    meta = (b'tim2\0' + f"{t['bpp']} {int(t['swizzled'])} {'s' if scaled else 'r'} "
            f"{t['header'].hex()}".encode('ascii'))
    return (PNG_SIG + _chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 3, 0, 0, 0))
            + _chunk(b'PLTE', plte) + _chunk(b'tRNS', trns) + _chunk(b'tEXt', meta)
            + _chunk(b'IDAT', zlib.compress(raw, 6)) + _chunk(b'IEND', b''))


def _unfilter(raw, w, h, bpp_bytes):
    stride = w * bpp_bytes
    out = bytearray()
    prev = bytearray(stride)
    pos = 0
    for _ in range(h):
        ftype = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        for i in range(stride if ftype else 0):
            a = line[i - bpp_bytes] if i >= bpp_bytes else 0
            b = prev[i]
            c = prev[i - bpp_bytes] if i >= bpp_bytes else 0
            if ftype == 1:
                line[i] = (line[i] + a) & 0xFF
            elif ftype == 2:
                line[i] = (line[i] + b) & 0xFF
            elif ftype == 3:
                line[i] = (line[i] + ((a + b) >> 1)) & 0xFF
            elif ftype == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else b if pb <= pc else c
                line[i] = (line[i] + pred) & 0xFF
            elif ftype != 0:
                raise ValueError(f'bad PNG filter {ftype}')
        out += line
        prev = line
    return bytes(out)


def from_png(data):
    if data[:8] != PNG_SIG:
        raise ValueError('not a PNG')
    pos, idat, chunks = 8, bytearray(), {}
    while pos < len(data):
        n = struct.unpack_from('>I', data, pos)[0]
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if kind == b'IDAT':
            idat += body
        elif kind == b'tEXt' and body.startswith(b'tim2\0'):
            chunks['tim2'] = body[5:].decode('ascii')
        else:
            chunks[kind] = body
    w, h, depth, ctype, _, _, interlace = struct.unpack('>IIBBBBB', chunks[b'IHDR'])
    if ctype != 3 or depth != 8 or interlace:
        raise ValueError('PNG must be 8-bit indexed, non-interlaced')
    if 'tim2' not in chunks:
        raise ValueError('PNG lacks the tim2 tEXt chunk written by topng')
    bpp, swizzled, alpha_mode, header = chunks['tim2'].split(' ')
    plte = chunks[b'PLTE']
    trns = chunks.get(b'tRNS', b'')
    palette = []
    for i in range(len(plte) // 3):
        a = trns[i] if i < len(trns) else 255
        palette.append(tuple(plte[3 * i:3 * i + 3]) + (alpha_from_png(a) if alpha_mode == 's' else a,))
    indices = _unfilter(zlib.decompress(bytes(idat)), w, h, 1)
    return build(bytes.fromhex(header), w, h, int(bpp), swizzled == '1', palette, indices)


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ('topng', 'totim2'):
        sys.exit(__doc__)
    data = open(sys.argv[2], 'rb').read()
    out = to_png(parse(data)) if sys.argv[1] == 'topng' else from_png(data)
    with open(sys.argv[3], 'wb') as f:
        f.write(out)


if __name__ == '__main__':
    main()
