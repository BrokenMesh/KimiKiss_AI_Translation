# Phase 3: text engine

How dialogue text gets from `SCRIPT.IMG` to the screen, and what that means for English. Addresses are EE addresses in `SLPS_258.50`. Function names are the ones applied in the (private) Ghidra project.

## Summary

- The engine is a Smalltalk-like VM. Almost the whole text path is **script bytecode** inside `SCRIPT.IMG`, not native code. That covers the control-code parser, the text queue, layout, line wrap and advance width.
- Native code only (a) runs the VM, (b) turns a character code into a glyph index, and (c) copies that glyph into a VRAM cache and draws it.
- The native glyph lookup already handles every Shift-JIS lead byte, including the unused rows 9–12. New glyphs drawn there render with **no ELF change**.
- So the font patch is a script patch (new `TextWindow`/`TextLine`/`LogLine` methods and constants) plus a new font texture. See D-011–D-013 in `decisions.md`.

## File access

- `main` (`0x00103540`) opens `SCRIPT.IMG` through `open_file_stream` (`0x001014d8`). The I/O layer is CRI "dvCi". `dvCiGetFileSize` (`0x001318d0`) and `dvCiOpen` (`0x00131ff8`) resolve names with `sceCdSearchFile`, so the game takes position and size from the ISO9660 directory. A grown `SCRIPT.IMG` can be relocated once its directory record is updated; this is still to be confirmed in emulation.
- `LoadGraph0` (`0x00104410`) loads `GRAPH\GRAPH0.ARC` (directory) and `GRAPH\GRAPH0.PAC` (LZSS data). `InitGraphicsResources` (`0x00104bd8`) then creates the glyph cache.

## The VM

- `VM_InterpretBytecode` (`0x00115458`) is the bytecode loop. The full opcode table is in `docs/formats/scf.md`; `tools/extract/scfdis.py` disassembles any method.
- Values are tagged 32-bit words: small integer `n` is `(n << 1) | 1`, nil = 0, false = 2, true = 4.
- Binary operators are opcodes `0x10`–`0x1F` (`+ - * / % & | ^ = > < >= <= <> -U ~U`). Integer pairs take a fast path. Anything else is sent as a message using the selector names at `0x002bf983` (`VM_BinopSelectorNames`, copied at run time to `VM_SpecialSelectors`, `0x003cc808`).
- `34 nn` calls native primitive `nn` of the receiver's class (`VM_CallPrimitive`, `0x00115280`). A class's table is `{u32 last_index, ptr table}`. `FontChar`'s table is at `0x002bf728` and `FontCharEx`'s at `0x002bf730`, both registered by `RegisterFontCharPrimitives` (`0x0010e1d8`).
- None of the text classes (`TextWindow`, `TextLine`, `TextLineC`, `LogLine`, `LogPage`, `Parson`, `NameEntryEdit`, `DeckView`, `StringStream`) uses primitives. They are pure script and can be rewritten.

## Dialogue path

1. **Scene script.** A line is `push_classvar K2_Script.<SPEAKER>`, `push_const "<text>"`, `send ':'`. Speaker slots are `K2_Script` class variables (`docs/formats/scf.md`).
2. **`Parson >> :`.** Shows the speaker, calls `message:`, waits for input. An `Array` argument is a choice: `message:` with element 1, then `select:`.
3. **`Parson >> message:`** is the control-code parser:
   - It sets the default font colour (`tempColor`/`fontColor`), then prints the speaker's `dispName` followed by `putIndent: 4`, and logs the line with `LogPage putLine:`.
   - It then reads the text char by char through a `StringStream`. Elements are 16-bit codes: Shift-JIS double-byte as `lead<<8 | trail`, ASCII as the byte value.
   - **`59 <= c < 256` is a control code.** Dispatch: `W V T F B S E M P A N R` → `inlineComW` … `inlineComR`. Any other value in that range is silently dropped, so **no ASCII letter, `;`–`@`, `[`–`` ` ``, `{`–`~` or half-width kana can be printed**.
   - `c < 59` (space, digits, `!`–`:`) and `c >= 256` are passed to `messWin put:`. The window then drops `c <= 256` (below), so in practice only double-byte codes print.
   - Special double-byte codes: `0x8162` `｜` → `putInter`, `0x815E` `／` → `putCrlf` (line break). `0x8176` `」` and `0x816A` `）` reset the speed before being printed.
   - Arguments of control codes are parsed by `parseNum` from ASCII digits.
   - `inlineComN`: `Nm` prints `GameParam getMyouji` (surname), `Nn` prints `getNamae` (given name).
   - `inlineComR`: `R<n><reading>` attaches ruby to the last `n` characters; `R` alone starts the ruby base.
4. **`TextWindow`** (one instance, `Parson.messWin`). `put:` queues codes in `putQueue`/`actQueue`, and `output` drains one entry per tick:
   - code `> 256` → `putChar:`;
   - small integers are commands: 0 font scale, 1 CLUT, 2 put-wait, 3 fade, 5 CRLF, 6 wait, 7 indent, 8 defaults, 10 inter, 12 ruby start, 13 ruby.
5. **`TextWindow >> putChar:`** does layout and wrapping:
   - **Wrap:** if `curX + fontW*fontSclW > posX + width - marginX`, call `crlf` first. This is a per-character overflow wrap; there is no word logic.
   - **Draw:** create `FontChar new: code clut: layer x: curX + fontW*fontSclW/2 y: curY sclW: sclH:`. The sprite is centred on the cell.
   - **Advance:** `curX += fontW*fontSclW + pitchX`, a fixed advance.
6. **`TextWindow >> crlf`:** `curX = posX + marginX + indent*(fontW + pitchX)`, `curY += pitchY`. Nothing checks the line count, so a 4th line would overflow the box.
7. **`FontChar` primitive 0** (`FontChar_prim_initialize`, `0x0010e218`) → `Sprite_CreateFontChar` (`0x00109540`) → `FontSprite_ctor` (`0x00185260`) → `GlyphCache_Acquire` (`0x00105068`).

## Message window geometry

From `TextWindow >> initialize` (no arguments) and the defaults in `initialize:` (7 arguments). Coordinates have the origin at screen centre.

| Field | Value |
|---|---|
| layer | 8 |
| posX, posY | −293, 44 |
| width, height | 586, 156 |
| fontW, fontH | 24, 28 |
| marginX, marginY | 17, 18 |
| pitchX, pitchY | −1, 44 |
| font scale | 1.0 (table `0.5/0.75/1/1.25/1.5`, selected by command 0) |

- The usable line width is `586 − 2·17 = 552` px. At the 23 px advance that is 24 full-width characters.
- Lines are 44 px apart, and 3 lines fit in the box.
- After the speaker name, `putIndent: 4` indents continuation lines by `4·23 = 92` px.

## Glyph lookup and cache

- `GlyphCache_ctor` (`0x0017ef18`) reads the font config at `0x002b1958`: texture `sysgraph/K2_font28_24`, cell 24.0 × 28.0, 208 cache slots. It builds a 208-slot glyph cache (`g_GlyphCache`, `0x002bd714`; vtable `0x002a8528`).
- `GlyphCache_Find` (`0x0017f1e0`) and `GlyphCache_Alloc` (`0x0017f308`) keep refcounted slots keyed by code.
- `GlyphCache_Upload` (`0x0017f558`) copies `24·28/2` bytes (4bpp) from the font texture at `base + 0x40 + glyph·336` into the slot. A slot sits in a 16-column grid: column `slot % 16`, row `slot / 16`.
- `SjisToGlyphIndex` (`0x0017f750`):
  - lead `0x81`–`0x9F`: base `(lead − 0x81)·188`;
  - lead `>= 0xE0`: base `(lead − 0xC1)·188`;
  - trail `0x40`–`0x7E`: `+ trail − 0x40`;
  - trail `0x80`–`0xFC`: `+ trail − 0x41`.
  
  That is linear Shift-JIS order, the same order as the texture's 4,384 glyph rows (`docs/formats/font.md`). Codes in rows 9–12 (`0x8540`–`0x86FC`) map to glyphs 752–1127, which exist in the texture and hold placeholders.
- The cache holds 208 distinct glyphs at once. An English font needs about 95, so a screen of English plus a few Japanese glyphs fits.

## Other text renderers

These draw `FontChar` sprites with their own fixed-pitch layout and need the same width-table treatment:

| Class | Where | Layout |
|---|---|---|
| `TextLine >> setText:` | menus, choices, labels | glyph `i` at `posX + i*pitch`; no code filtering |
| `TextLineC >> setText:` | centred variant | same |
| `LogLine` | backlog | own layout (not yet read) |
| `NameEntryEdit` | name entry | own layout (not yet read) |
| `DeckView`, `FontCharEx` users | topic cards | not yet read |

`K2_Script >> zenkaku:` converts name-entry ASCII to full-width: `A`–`Z` → `0x8260`+, `_` → `0x8151`. The player's name is stored and printed as full-width Shift-JIS.

## Debug helpers

`SjisToEuc` (`0x0011ab10`) is called only by three debug string printers (`0x0011abbc`, `0x0011ae78`, `0x0011af54`). It is not on the render path.

## Still unknown

- Exact `LogLine`, `NameEntryEdit` and `DeckView` layout code.
- Whether any hard-coded strings in the ELF are drawn through a separate native path (Phase 4).
- Whether the type-5 text constant loader treats single bytes `>= 0x80` (half-width kana) specially. English does not need them.

## Gate: English test lines in the emulator — pass

Build: `tools/qa/make_en_test_text.py text build/test/text`, then `tools/build/build.sh <clean.iso> build/test/kimikiss_en_test.iso build/test/text`. Played in PCSX2 via `tools/qa/emu.sh`: New Game → default name → prologue. Screenshots are in `qa/` (gitignored).

- **Boot:** the patched image boots. `GRAPH0.PAC` was relocated to LBA 608695, and the font and UI load from it. This confirms that files can be relocated through the ISO9660 directory.
- **Rendering:** English glyphs are legible, spaced by the width table, sit on the Japanese baseline, and mix correctly with Japanese (`「キス」？`).
- **Wrapping:**
  - The word-wrapped line breaks at the inserted `／` and fits in 3 lines.
  - The unbroken over-long word is broken by the patched per-character overflow test at the right edge.
  - All 95 printable ASCII glyphs render across three lines.
- **Backlog:** `LogLine` shows the same lines with variable width and the same wrap behaviour, and scrolls.

Not yet covered: menus and choices (`TextLine`/`TextLineC`), name entry, `DeckView` (Phase 4), and the UDF bridge records (D-014).
