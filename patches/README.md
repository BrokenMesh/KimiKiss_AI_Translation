# Patches

## `scripts/` — SCF bytecode patches

One file per replaced method, in the assembler syntax of `tools/reinsert/scfasm.py`. Every file has a header:

- `; target: <Class> <method> argc=<n> table=<methods|methods2>`: the method that is replaced;
- `; original-sha1:`: the SHA-1 of the original bytecode, so a patch is never applied to the wrong input;
- `; reason:`: why the method is replaced.

A file headed `; add: <Class> <method> argc=<n> table=...` adds a new method instead and has no `original-sha1`.

`tools/reinsert/apply_script_patches.py <script_dir> patches/scripts` applies them during the build. `push_const en:"..."` is an English string in the D-012 codes (`tools/reinsert/en_text.py`). `@EN_WIDTHS` expands to the width table from `tools/font/en_widths.json`; `@EN_SYMBOLS` to the int table that maps full-width symbols 0x8140-0x819E to English codes (name entry, D-016). Original bytecode can be listed with `tools/extract/scfdis.py <Class>.scf <method>`; the new bytecode is the assembled patch.

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
| `NameEntryEdit.initialize3.asm`, `initialize4` | 521 / 101 bytes | 461 / 59 bytes | Name entry screen: 2 x 8 slots (6 for the deck name), padded to 8 characters; slot positions come from `layout` instead of the const-28 table (D-016) |
| `NameEntryEdit.layout0.asm` | new | 352 bytes | Places every slot by glyph width and shrinks the glyphs (one scale for both fields) so 8 letters, 8 Ws or 8 full-width characters fit the 82 px fields; moves the cursor (D-016) |
| `NameEntryEdit.slots0.asm`, `fieldN0`, `fieldW0`, `fieldL1`, `emptyW0` | new | 12 / 12 / 12 / 18 / 12 bytes | Geometry of the two modes: 16 slots in fields of 8 (player), 6 in one field of 6 (deck) (D-016) |
| `NameEntryEdit.adv1.asm` | new | 42 bytes | Advance of a slot's code: English width table, 13 px for an empty slot, 24 for everything else (D-016) |
| `NameEntryEdit.toEnglish1.asm` | new | 101 bytes | Typed full-width digits and letters become English codes (`+0x301`), full-width symbols with an ASCII twin go through `@EN_SYMBOLS` (D-016) |
| `NameEntryEdit.setChar1.asm` | 365 bytes | 220 bytes | Slot range 1..slots; typed codes through `toEnglish:`; history strings fill a whole 8 (or 6) slot field (D-016) |
| `NameEntryEdit.moveCursor1.asm`, `clrChar0`, `nameFade3`, `destruct0` | 99 / 82 / 54 / 119 bytes | 126 / 94 / 57 / 122 bytes | 7 becomes `slots + 1`, loops run over `slots`; moving the cursor re-runs `layout` (D-016) |
| `NameEntryEdit.getStr2.asm`, `getStrH0`, `getStrL0`, `getStr0` | new / 115 / 115 / 110 bytes | 190 / 36 / 38 / 14 bytes | Name = slots `from..to-1` trimmed, inner blank = English space; the three old copies of the loop call it (D-016) |
| `NameEntry.selectChar1.asm`, `scriptMain1` | 695 / 1160 bytes | 713 / 1178 bytes | Confirm index `7` becomes `edit slots + 1`, voice boundary `4` becomes `edit fieldN + 1`; the screen opens on the 英数記号 page (menu row and `curY` 3) (D-016) |
| `NameEntryList.run0.asm` | 170 bytes | 174 bytes | First page 3 (英数記号) instead of 0 (kanji) (D-016) |
| `NameEntryList.setList41.asm`, `moveCursor1` | 225 / 328 bytes | 225 / 331 bytes | History page: four 96 px columns (x -124, -28, 68, 164) and a 96 px cursor (D-016) |
| `Parson.setDispName1.asm` | 142 bytes | 40 bytes | Name plate = the whole surname (was padded to 3 cells and cut at 3) (D-016) |
| `ShioriListItem.initialize2.asm` | 184 bytes | 296 bytes | Save list: names measured with `xOf:`, text scale 1 / 0.75 / 0.5 by total width, second name placed after the first (was a table for 0-3 characters) (D-016) |
| `ShioriData.serialize0.asm`, `cut1` | 112 bytes, new | 203, 51 bytes | Slot header must stay within 256 bytes: while it is longer, the longer name of the header copy loses its last character (D-016) |
| `Parson.message1.asm` | 518 bytes | 528 bytes | Indent after a speaker plate 5 cells (115 px) instead of 4 (92 px), so English surname plates fit (glossary D9, D-023); first calls `messWin pageFor:` (D-024) |
| `TextWindow.pageFor1.asm` | new | 97 bytes | Clears the window first when the message's rows (`／` + 1) do not fit the rows left on the page; scene scripts stack short messages on one 3-row page (D-024) |
| `TextWindow.output0.asm` | 231 bytes | 288 bytes | The indent command also moves the pen: line 1 of a spoken line starts at the indent column like lines 2-3, or 6 px after a wider plate (D-023) |
| `GameParam.easyFlags0.asm`, `easy1`, `setEasyFlags1` (class side) | new | 39 / 14 / 6 bytes | Easy Mode switches: an Integer bitmask in class variable 18 (`autoSkip`, saved in the system data, never read by the game); nil or a Boolean reads as 0 (D-038) |
| `Favor.addTension1`, `addInterest1`, `downFeel0`, `downInterest0`, `addBad1`; `TensionGauge.addTension1` | 16 / 71 / 69 / 48 / 35; 22 bytes | + about 15 each | Easy Mode "No Losses" (bit 1): a flag test in front of the original method drops decreases (D-038) |
| `Parson.checkInterest0`; `MatchHistory.checkLose3`, `checkLose4`; `TensionGauge.getTension0` | 53; 73 / 70; 7 bytes | 68; +12 each; 24 bytes | Easy Mode "Fewer Rejections" (bit 2): roll with interest + 3, no bored/leave endings, tension tests see +32 (D-038) |
| `GameParam.checkFirst0`, `checkSecond0` (class side) | 12 bytes each | about 75 bytes | Easy Mode "Easier Meetings" (bit 4): re-roll the encounter table up to 8 times until a met girl (D-038) |
| `GameParam.useAttack0`, `getAttack0`; `TopicPlayer.getRemainder0` (class side) | 22 / 6; 65 bytes | +12 each; 102 bytes | Easy Mode "More Tries" (bit 8): the Attack is not used up, an empty topic deck is dealt again (D-038) |
| `MainMenu.makeMenu0`, `scriptMain0`, `menuTex1` | 169 / 1432 bytes, new | 179 / 1481 / 45 bytes | Title menu command 6 "Easy Mode" after Settings (sprite 114 n 4, `menu_main4`), opens the panel (D-038) |
| `Configuration.easyMode1`, `easyRowY1`, `easyShow3` | new | 902 / 15 / 96 bytes | The Easy Mode panel: DialogBox, TextLine labels, On/Off cross-fade, pad loop, save prompt through ConfigSave (D-038) |

## Textures

Not bytecode and not data in the repo: `tools/texture/` redraws the Japanese UI text of 216 `GRAPH0` textures into English at build time (D-019). `translation/textures.toml` holds the English labels, their text boxes and background rules, and the sprites that are drawn larger (D-035). The redrawn TIM2 files keep the original palette and size (except textures of larger sprites, which are padded and the archive repacked); `apply_graph0.py` writes them together with the font into `GRAPH0.ARC` and the LZSS `GRAPH0.PAC`. Method and review list: `docs/phase-4-textures.md`.

Hand-edited textures are not in the repo either: PNGs named `GRAPH0_0453.png` / `GRAPH1_0058.png` / `GRAPH2_NNNN.png` in `$KIMIKISS_OVERRIDES` (default `../kimikiss-private/texture_overrides`) replace those entries at build time, GRAPH0 through `apply_graph0.py` (ARC and PAC), GRAPH1/2 through `apply_graph12.py` (raw TIM2 inside the ARC, no PAC) (D-020). Without the directory the build is unchanged. How to make them: `docs/phase-4-textures.md`, "Hand-edited textures".

## ELF

None so far (D-011).
