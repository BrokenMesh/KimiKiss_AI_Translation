# Dialogue font

`GRAPH/GRAPH0.ARC` entry 77, hash `0xffc76f47`. TIM2, 4bpp, nominally 672 × 4384.

## Layout

- The 672 × 4384 dimensions are only a container. Each 672-pixel row is one glyph of **24 × 28** pixels, stored row-major (24 × 28 = 672).
- That gives **4,384 glyphs** in JIS X 0208 order: glyph `g` is row `g // 94 + 1`, cell `g % 94 + 1`, which is Shift-JIS order starting at `0x8140`.
- Coverage: rows 1–8 (symbols, full-width digits and Latin, kana, Greek, Cyrillic, part of box drawing), row 13 (NEC specials: ①–⑳, Roman numerals, unit symbols), and rows 16–47 (Level 1 kanji, up to 腕 `0x9872`). No Level 2 kanji. Unassigned codepoints hold a `・` placeholder.
- Game-specific substitution: `0x8159` (〆) holds **澤**, presumably for a character's name.
- Pixel values are a 16-level coverage ramp (0 = empty, 15 = solid).
- The 64-entry CLUT is 4 palettes × 16, all with the same alpha ramp 0..0x80. The colors are white `(255,255,255)`, blue `(200,200,255)`, pink `(255,190,255)` and dark grey `(63,63,63)`, probably used for text styles or speaker colors.
- `GsTex0` declares PSMT4 1024 × 1024. Together with the glyph-per-row layout, this suggests the engine copies glyphs on demand into a VRAM glyph cache (to verify in Phase 3).
- Digits and Latin letters exist only as full-width glyphs (`０`–`９`, `Ａ`–`Ｚ`, `ａ`–`ｚ`, row 3), drawn in 24-pixel cells.

## Tools

`tools/extract/font.py <GRAPH0.ARC> <out.png> [first] [count]` renders glyphs in a 94-column grid, one JIS row per line. `font.sjis_of(g)` maps a glyph index to its Shift-JIS code.

## Implications for Phase 3

- There are no half-width glyphs and no width table in the texture. The advance is probably a fixed 24 px (to confirm in the ELF).
- English needs new narrow glyphs plus per-glyph advance widths. The plain route is to redraw full-width `Ａ`–`ｚ` and punctuation as proportional glyphs inside their 24 × 28 cells, encode English as those Shift-JIS codepoints, and patch the advance logic to use a width table.
- Rows 9–12 (`0x8540`–`0x86FC`) and 14–15 (`0x879F`–`0x889E`) hold only placeholders: 564 free cells for extra glyphs such as ligatures or italics. Row 13 is in use.
