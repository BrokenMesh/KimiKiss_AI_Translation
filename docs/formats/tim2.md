# TIM2 textures

All 2,138 TIM2 files on the disc share one shape:

- One picture, no mipmaps, a 48-byte picture header and no user data.
- Image type 5 (8bpp, 256-color CLUT) for 2,137 textures. Image type 4 (4bpp) only for the font sheet.
- CLUT type 3: 32-bit RGBA. 8bpp CLUTs are stored in CSM1 order, which swaps entries 8–15 and 16–23 in every block of 32.
- Pixel data is linear (not GS-swizzled).

Header offsets used by the tools: picture header at byte 16 (total size, CLUT size, image size, header size, CLUT colors, ..., width at 36, height at 38). `GsTex0` is at byte 40.

## PNG mapping

`tools/extract/tim2.py topng|totim2` converts to an 8-bit indexed PNG and back, losslessly:

- The palette is the de-swizzled CLUT. Pixel indices are kept exactly.
- Alpha goes to `tRNS`. When every entry is ≤ 0x80 (PS2 full opacity), alpha is scaled to 0–255; otherwise it is copied raw. Some GRAPH1 palettes use 0xFF.
- A `tim2` tEXt chunk stores the bpp, CLUT order, alpha mode and the original 64 header bytes.

Edited PNGs must stay 8-bit indexed. Any filter type and palette are accepted on import.

## Verification

`tools/qa/test_texture_roundtrip.py` passes for every texture: TIM2 → PNG → TIM2 is byte-identical, and all four ARCs repack byte-identical.
