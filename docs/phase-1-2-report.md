# Phases 1 and 2: recon and text pipeline

Source image: SLPS-25850 (eb!Kore+ re-release), SHA-1 `40a70c43ef4c57b8bcdfeab3814437c3eaf4821c`. Phase 0 was done after Phases 1 and 2, because the user asked to start at Phase 1. Gates G0 and G1 have since passed ([phase-0-status.md](phase-0-status.md)).

## Gate G2: do the Amagami tools parse KimiKiss? **Pass**

- `SCRIPT.IMG` has exactly the Amagami IMG layout: LZSS `11 5 2 2 0`, then a name/offset table archive.
- The unmodified `scf/parser_scf.py` runs on all 386 scripts and produces readable Shift-JIS dialogue.
- One defect found: it reads constants until EOF and misses type-8 arrays. Our parser (`tools/extract/scf.py`) handles arrays and the header flag byte, and reproduces every member byte for byte. Details are in [formats/scf.md](formats/scf.md).
- The Amagami `tm2/bmp2tm2.py` font tool does not apply: the KimiKiss font is a 4bpp sheet with one 24 × 28 glyph per row ([formats/font.md](formats/font.md)).

## Gate G3: byte-identical round trip. **Pass**

| Check | Result |
|---|---|
| `tools/qa/test_text_roundtrip.py build/orig/SCRIPT.IMG`: unpack → JSON (36,172 records) → reinsert → pack → LZSS | SCRIPT.IMG byte-identical |
| Same pipeline with one line lengthened from 65 to 105 bytes | Only that constant changes; archive decompresses and parses |
| `tools/qa/test_texture_roundtrip.py`: all ARCs, every TIM2 → PNG → TIM2 | 2,138 textures and 4 archives byte-identical |
| LZSS encoder vs. GRAPH0.PAC | byte-identical |

## What was learned

- 24 files on the disc: [formats/iso.md](formats/iso.md). Only SCRIPT.IMG, the ELF, GRAPH0.ARC/PAC and possibly some GRAPH1/2 textures need changes.
- The text is 36,172 records and 1.58 MB of Shift-JIS across 226 scripts. Speakers are recovered from bytecode for 95.5% of records.
- Strings are referenced by constant index, so line length is not limited by the script format.
- The engine treats ASCII inside text as control codes. English needs a different encoding: Phase 3 design.
- The font has full-width glyphs only and probably a fixed 24 px advance. Variable-width English needs a width table and changes to the draw code.
- Space: SCRIPT.IMG has 1,787 bytes of slack in place and must be relocated once it grows ([size-budget.md](size-budget.md)).

## Blockers

None. The Ghidra download block was resolved by the user supplying the tools through Google Drive ([phase-0-status.md](phase-0-status.md)).

## Next concrete steps

1. Phase 3: find how the ELF opens SCRIPT.IMG (by name or by LBA), the text-code parser (`V`, `W`, `N`, ...), the glyph lookup (Shift-JIS → glyph index) and the advance width.
2. First lead: every data file is named in the ELF (`SCRIPT.IMG` at `0x002B16E0`, referenced from `0x0010359C`), and the ELF contains `sceCdSearchFile` error strings, so files are probably located through the ISO directory. That would make relocating SCRIPT.IMG straightforward.
