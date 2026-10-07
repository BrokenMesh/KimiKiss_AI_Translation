# Phase 4: hard-coded strings in the executable and IOP modules

Question: does `SLPS_258.50` (or any `.IRX` under `build/orig/MODULES/`) hold Japanese text the player sees? Addresses are EE addresses. Function names are working names from the private Ghidra project and the capstone disassembly.

## Result

- The ELF holds **one** Japanese string. It is the PS2 memory-card browser title of the save data, not in-game text.
- No IOP module holds Japanese text. No native code produces text for the script VM to display.
- The ELF does **not need text patches for the translation to be playable**. One optional cosmetic patch exists (below).

## Method

1. **Scan.** A regex over the whole file found runs of valid cp932 (double-byte lead `81-9F`/`E0-FC` with a legal trail, plus `20-7E`, plus half-width kana) with at least one double-byte character. That gives 19,559 raw runs, of which 17,904 are in `.text` (opcode bytes that happen to decode).
2. **Filter.** Kept runs bounded by NUL, outside `.text`, then required all double-byte characters to be kana, full-width symbols or JIS level 1 kanji. Then looked at every survivor by hand. 56 passed the level-1 test without the NUL rule. 55 are code or float/table bytes (`姑-拭`, `潯`, `猜`, ...). One is text.
3. **Cross-checks.** Searched for pure hiragana/katakana runs (`82 9F-F1` / `83 40-96`), runs of 3+ half-width kana bytes, UTF-8 and UTF-16 kana. Only the same one string turned up. The half-width kana runs are IEEE float constants.
4. **ASCII inventory.** About 2,100 NUL-delimited ASCII strings of 4+ chars exist in `.data`/`.rodata`/`.sdata`. All are CRI/Sony library messages and version banners (`ADXT/PS2EE Ver.9.98a ...`, `E9040801:...`), file and texture paths (`GRAPH\GRAPH0.ARC`, `kaiwa/waku`), VM class and selector names, C++ RTTI names, or VM error text. None is player-facing. No "Now Loading", menu or dialog English exists.
5. **References.** Located by `lui`/`addiu` pairs in `elf.asm`.
6. **Modules.** Same scan over `MODULES/*.IRX`, `IOPRP310.IMG`, `FCACHE.TXT`, `SYSTEM.CNF`. All candidates are MIPS opcode noise, none are NUL-bounded text. These are stock Sony/CRI modules.

## Counts (Japanese strings)

| Class | Count |
|---|---|
| DISPLAYED | 1 |
| UNSURE | 0 |
| DEBUG | 0 |
| FILENAME / PATH | 0 |
| DATA (tables, unknown) | 0 |
| false positives (code, floats) | 55 of the 56 that survive the kana/level-1 filter |

## DISPLAYED and UNSURE strings

| Address (file offset) | Bytes available | Text | Referenced by | Translation note |
|---|---|---|---|---|
| `0x002b26c8` (`0x1b36c8`) | 40 (36 text, then NUL padding up to the pointer table at `0x002b26f0`) | `キミキスＰＬＵＳ` followed by ten `　` (U+3000) | `MC_BuildIconSys` `0x0010a388` at `0x0010a460`: `strcpy(&iconsys_buf[0xc0], str)`. | Save-data title in the PS2 browser. See below. |

Why DISPLAYED:

- `MC_BuildIconSys` (`0x0010a388`) fills a 964-byte `sceMcIconSys` at `0x001e30c0`. It writes `0x18` to offset 6 (`nlOffset`, at `0x0010a468`), copies the background colours, light data and ambient colour from `.data`, and **`strcpy`s this string into the title field at +0xC0**. It copies `kimikiss.ico` (`0x002b26b8`) into the `view`, `copy` and `del` fields.
- `MC_WriteIconSys` (`0x0010b308`) builds `/BISLPS-25850/icon.sys` from `0x002b2678` and `0x002b2738`, opens it with `sceMcOpen` (`0x203`) and writes the 964 bytes with `sceMcWrite`. A second function at `0x0010b3d0` builds the same path for another card operation (not examined further).
- The memory-card browser (the console's own UI, not the game) shows `titleName`. `nlOffset = 0x18` puts the line break after 12 full-width characters, so the second line is blank spaces and the browser shows one line: `キミキスＰＬＵＳ`.

## Native strings that reach the script VM

- **No primitive returns display text.** The native classes with primitives are `ControlPad`, `MemoryCard`, `TopicIcon`, `TensionPicture`, `ClockHands`, `FontChar`, `FontCharEx`, `BG_Picture`, `EventPicture`, `ParsonPicture` and `K2_Script`. Their tables are at `0x1e2f20`–`0x1e3070`; `K2_Script` has two primitives. No primitive body calls the string constructor.
- **The string constructor** is `VM_NewStringFromCStr` (`0x00116030`). It has 56 callers, all inside the VM core (`0x113d38`–`0x11ce08`). They build VM error text: `Integer:+ right value was not Number`, `String:new argument was not Integer`, `Array:[] index was not Integer`, and the ` Class <X> in Line N: argCount` trace pieces. These are debug text. The script side of `createStackTrace` is empty and `Throwable >> toString` only concatenates the class name and message. `System >> print`/`println` (primitives 0/1) are TTY output. I found no script that draws an exception message (`GameMain` only tests `isKindOf RestartException`); this was checked by grep over the class disassemblies, not exhaustively.
- **Memory-card messages are script strings.** `MemoryCard`, `MemoryCardCheck`, `SystemSave` and the save/load menus carry the Japanese messages (for example `ＭＥＭＯＲＹ　ＣＡＲＤ差込口１に...`) as `SCRIPT.IMG` constants shown through `ConfirmDialog`. `MemoryCard` primitives return integer status codes, or raise `IllegalArgument`. They are already in the extracted text.
- **No native text drawing.** `Sprite_CreateFontChar` (`0x00109540`) has two callers, the `FontChar` and `FontCharEx` initialize primitives, and the glyph code comes from the script. `SjisToGlyphIndex` has one caller, the glyph cache. `SjisToEuc` feeds debug printers only. No native code draws a string literal.
- **System dialogs from the IOP.** The IOP modules are stock (`PADMAN`, `MCMAN`, `MCSERV`, `LIBSD`, `CDVDSTM`, CRI ADX, `EZMIDI`). They contain no Japanese. Disc-error and format-card screens belong to the console BIOS, not to the game.

## Does the ELF need text patches?

No for in-game text. Everything the player reads during play is in `SCRIPT.IMG`.

Optional: the save-data title. One string, fits in place.

- **Space.** 40 bytes including the NUL. A replacement of up to 39 bytes needs no relocation.
- **Encoding.** Do **not** use the project's row 9/10 codes (D-012). The browser draws the title with the console's built-in font, not the game's font texture, so those codes would show as junk. Use real Shift-JIS. Full-width Latin is the safe choice: `Ｋｉｍｉ`... is `82 6A 82 89 ...`. Plain ASCII bytes are not a problem for this field (no VM control codes apply, it is a native `strcpy`), but I did not test how the browser renders them, so full-width is the conservative option.
- **Proposed text.** `ＫｉｍｉＫｉｓｓＰＬＵＳ` is 12 characters, 24 bytes, exactly `nlOffset`, so it shows on one line and no instruction changes. If a space is wanted (`ＫｉｍｉＫｉｓｓ　ＰＬＵＳ`, 26 bytes), also change the `addiu $t7,$zero,0x18` at `0x0010a468` (file offset `0xb468`, bytes `18 00 0f 24`) to `0x10`, or the line breaks inside `ＰＬＵＳ`.
- **Risk.** Low. The title is rewritten with `icon.sys` on every save and does not affect the save directory name (`/BISLPS-25850`). Existing saves keep the old title until saved again.
- **Not needed for the game to work.** `KimiKiss` is already a romanisation, so leaving the katakana is acceptable.
