# LZSS

Used by `SCRIPT.IMG` and `GRAPH/GRAPH0.PAC`. Same parameters as Amagami (QuickBMS `comtype lzss "11 5 2 2 0"`).

## Layout

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | Decompressed size, u32 LE |
| 4 | … | Okumura LZSS stream |

- Ring buffer of 2048 bytes, filled with `0x00`. The write cursor starts at 2014 (`N - F`, F = 34).
- Each flag byte is read LSB first: bit 1 means a literal byte, bit 0 means a 2-byte reference.
- Reference: `b0, b1`. Offset = `b0 | (b1 >> 5) << 8` (11 bits, absolute ring position). Length = `(b1 & 0x1F) + 3`, so 3 to 34 bytes.

## Encoder

`tools/lzss/lzss_enc.c` is Haruhiko Okumura's 1989 `LZSS.C` binary-tree encoder with N = 2048, F = 34, THRESHOLD = 2 and a zero-filled window. It reproduces both compressed files on the disc byte for byte, so the original tool was this encoder.

- Decoder: `tools/extract/lzss.py`.
- Encoder build: `img_pack.py` compiles it on demand to `build/bin/lzss_enc` with gcc.

## Instances

| File | Compressed | Decompressed | Content |
|---|---|---|---|
| `SCRIPT.IMG` | 1,855,749 | 4,204,839 | IMG archive of 386 SCF scripts ([img.md](img.md)) |
| `GRAPH/GRAPH0.PAC` | 1,825,235 | 5,573,460 | Byte-identical copy of `GRAPH/GRAPH0.ARC` |
