# Patches

## `scripts/` — SCF bytecode patches

One file per replaced method, in the assembler syntax of `tools/reinsert/scfasm.py`. Every file has a header:

- `; target: <Class> <method> argc=<n> table=<methods|methods2>`: the method that is replaced;
- `; original-sha1:`: the SHA-1 of the original bytecode, so a patch is never applied to the wrong input;
- `; reason:`: why the method is replaced.

A file headed `; add: <Class> <method> argc=<n> table=...` adds a new method instead and has no `original-sha1`.

`tools/reinsert/apply_script_patches.py <script_dir> patches/scripts` applies them during the build. `@EN_WIDTHS` expands to the width table from `tools/font/en_widths.json`. Original bytecode can be listed with `tools/extract/scfdis.py <Class>.scf <method>`; the new bytecode is the assembled patch.

| Patch | Original | New | Reason |
|---|---|---|---|
| `TextWindow.putChar.asm` | 96 bytes | 125 bytes | Variable-width English in the message window (D-011–D-013) |
| `LogLine.putChar.asm` | 104 bytes | 131 bytes | Same, in the backlog |
| `TextLine.xOf1.asm` | new | 81 bytes | x offset of character i: sum of advances, English by the width table (D-015) |
| `TextLine.setText1.asm` | 260 bytes | 266 bytes | Menu text: positions from `xOf:`; stores `text` first and repositions reused glyphs |
| `TextLine.setPos0.asm`, `restart0`, `move4` | 64 / 88 / 82 bytes | 63 / 87 / 81 bytes | Positions from `xOf:` |
| `TextLineC.setText1.asm` | 116 bytes | 120 bytes | Centred menu text: positions from `xOf:`; stores `text` first |
| `TextLineC.setPos0.asm`, `restart0`, `move4` | 76 / 100 / 94 bytes | same sizes | Positions from `xOf:` |
| `ConfirmDialog.initialize7.asm` | 672 bytes | 736 bytes | Box width from the pixel width of the longest line (`line xOf: text length` on the built `TextLineC` lines) instead of characters x 18; Japanese box unchanged (D-017) |
| `DeckView.setName0.asm` | 115 bytes | 171 bytes | Deck name on the deck screen: glyph x from a measuring `TextLineC` (`xOf:`), 6-character cut becomes a 156 px cut; Japanese unchanged (D-017) |

## ELF

None so far (D-011).
