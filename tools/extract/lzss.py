"""LZSS codec used by the engine (QuickBMS parameters "11 5 2 2 0").

Stream layout: u32 LE decompressed size, then Okumura-style LZSS.
Window 2048 bytes, initialised to 0, write cursor starts at 2014.
Flag byte LSB first: 1 = literal byte, 0 = 2-byte reference
(offset = b0 | (b1 >> 5) << 8, length = (b1 & 0x1F) + 3).
"""
import struct

N = 2048
F = 32
THRESHOLD = 2
R_START = N - F - THRESHOLD


def decompress(src):
    size = struct.unpack_from('<I', src, 0)[0]
    win = bytearray(N)
    r = R_START
    out = bytearray()
    pos = 4
    end = len(src)
    flags = 0
    while len(out) < size and pos < end:
        flags >>= 1
        if not flags & 0x100:
            flags = src[pos] | 0xFF00
            pos += 1
            if pos >= end:
                break
        if flags & 1:
            c = src[pos]
            pos += 1
            out.append(c)
            win[r] = c
            r = (r + 1) & (N - 1)
        else:
            if pos + 1 >= end:
                break
            b0, b1 = src[pos], src[pos + 1]
            pos += 2
            off = b0 | ((b1 >> 5) << 8)
            length = (b1 & 0x1F) + THRESHOLD + 1
            for k in range(length):
                c = win[(off + k) & (N - 1)]
                out.append(c)
                win[r] = c
                r = (r + 1) & (N - 1)
    if len(out) != size:
        raise ValueError(f'decompressed {len(out)} bytes, header says {size}')
    return bytes(out), pos
