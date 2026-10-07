# Phase 4: name entry

How the player's name is entered, stored, saved and drawn, and the smallest script change that lets players type Latin names. Facts come from the disassembly of `NameEntry`, `NameEntryEdit`, `NameEntryList`, `GameParam`, `ShioriData`, `SerializeData`, `Parson`, `K2_Script`, `LogLine`, `ShioriListItem`, `StaffRoll` and `MainMenu`/`DeckEdit` (callers). Offsets are bytecode offsets inside the named method (`tools/extract/scfdis.py`). "Inferred" marks anything not seen directly in bytecode and not yet tested in the emulator.

## Summary

- The name is two `String`s of 16-bit codes: surname (`{Nm}`, `GameParam getMyouji`) and given name (`{Nn}`, `getNamae`). Defaults: `"相原"` and `"光一"`, constants 166/167 of `GameParam >> initialize` (0x0015, 0x001c).
- "3 characters" is not one constant. It is 3 slots per name inside a 6-slot layout (`nameStr`/`nameChar`/`waku` arrays of 6, slot table of 8 x-positions, cursor range 0..7), repeated as literals in about 60 operands across `NameEntryEdit` and `NameEntry`. Dialogue, backlog and credits print any length. Only the name plate (`Parson >> setDispName:`) and the save list (`ShioriListItem >> initialize:`) cap at 3.
- The save header has a hard 256-byte stride per slot. It holds both names. Fixed content is 200 bytes plus 3 bytes for each non-nil `bad` entry of the 8 `FavorBase` records (0 to 16 entries, so 200 to 248 bytes; measured in D-016, this section first assumed 216), leaving `56 - 3k` bytes for the two names. With 8 + 8 characters (32 bytes) it fits for k <= 8; the implementation (D-016) shortens the header copy of the names when it does not.
- The grid is plain text: six pages of `String` rows stored as constants of `NameEntryList >> openPage:`. `英数記号` is full-width (`０-９`, `Ａ-Ｚ`, `ａ-ｚ`, symbols), so English codes can be produced by mapping on input. The grid itself needs no change.
- No validation exists. An empty name keeps the previous one. `履歴` is the list of names in the 20 save slots, not a typing history.
- Correction to `docs/phase-3-text-engine.md`: `K2_Script >> zenkaku:` has nothing to do with name entry. It builds event class names (`getEvCode:`, A-Z to `0x8260+`, `_` to `0x8151`). The name is full-width only because the grid is.

## 1. Storage and the 3-character limit

### Where the names live

| What | Where |
|---|---|
| Current names | `GameParam` instance ivars 0 `myouji`, 1 `namae` (String). Class-side `getMyouji`/`getNamae`/`setMyouji:`/`setNamae:` forward to the singleton in classvar 7 `curInstance` (`GameParam >> initialize` 0x0011). |
| Setters | `setNamae:` plain store (0x0004). `setMyouji:` stores, then `Parson getObj: 0` `setDispName:` (0x0006-0x0014): the protagonist's name plate follows the surname. |
| Defaults | constants 166 `"相原"`, 167 `"光一"` (system strings, `byte_budget` 4). Plate default: `K2_Script >> setup` constant 13 `"相　原"` (0x0036). |
| Save header (per slot) | `ShioriData` ivars 1 `myouji`, 2 `namae`, copied in `set` (0x002d-0x0037), serialized in `serialize` (0x0013-0x0021), restored in `restore` (0x0022-0x002e). |
| Save body | `GameParam >> makeShioriBody` puts `myouji`, `namae` at array indices 0 and 1 (0x000f-0x0019). `restoreShioriBody` reads them back (0x000c-0x001f). |
| System data | does not contain the names. |

### Serialization and size

> Correction (D-016): the table below counts four ints per girl in `lastFavor` and gives 216 bytes. Running the real serializer gives `200 + 3k + 2 (chars Nm + chars Nn)` with k = 0..16 non-nil `bad` entries; the slot writer copies exactly 256 bytes from the header buffer (`MemoryCard` primitive 6, handler `0x0010ae00`), so a longer header is cut. `toByteArray` and `newFromByteArray` round-trip 0x85xx codes as two bytes.

`SerializeData >> serialize:` writes each element as 1 type byte plus data, and ends the array with a 0 byte. Types: nil `N` (+1 byte), Boolean `B` (+1), Integer `I` (+4), Float `F` (+4), String `S` (+4-byte length, then `toByteArray`, 0x00d2-0x0162), array `A` (recursive). Strings are variable length. A double-byte code is 2 bytes (inferred from `Integer >> asChar`, native `0x00119358`, which builds a 1- or 2-byte C string from the code).

The header is the `ShioriData >> serialize` array `[update(4 ints), myouji, namae, today, lastFavor(8 x 4 ints)]`:

| Part | Bytes |
|---|---|
| `update` array | 22 |
| `today` | 5 |
| `lastFavor` | 178 |
| two String headers | 10 |
| terminator | 1 |
| **fixed total** | **216** |
| names | `2 x (chars(Nm) + chars(Nn))` |

- `ShioriData class >> load:` (0x000f, 0x0024, 0x0032-0x0049) reads 5120 bytes and slices 20 headers of **256 bytes**. So `216 + 2·chars ≤ 256`, that is **at most 20 characters in total**. Today the maximum is 6 characters (228 bytes).
- With 8 + 8 characters the header is 248 bytes. With 10 + 10 it is exactly 256, with no margin.
- What `MemoryCard >> writeAllData:` (native primitive 6) does with a header longer than 256 bytes was not read. `ShioriData >> restore:` turns a header with fewer than 5 elements into a blank slot (0x000c-0x0019). Treat overflow as slot corruption.
- The body has no fixed names field. It holds the whole 1800-int `event` array and more, so 16 characters are noise there. Whether the native body writer has a fixed maximum size was not checked.

### The 3-slot limit in the UI

`NameEntryEdit` (ivars: 0 mode, 1 base, 2 waku, 3-7 text0-4, 8-9 arrowL/R, 10 cursor, 11 curX, 12 lay, 13 nameChar, 14 nameStr, 15 state, 16 stateNext, 17 exec). `mode` 0 = player name, 1 = deck name (`DeckEdit >> nameEntry`, 6 characters, `WadaiParam`). `curX`: 0 = 戻る, 1-3 surname slots, 4-6 given name slots, 7 = 決定.

| Method | Offsets with the literal | Meaning |
|---|---|---|
| `initialize` argc 4 | 0x0007, 0x0016 (surname: `3`, `<= 2`), 0x0031, 0x0040 (given) | pad each name to 3 with `"　"` (`0x8140`), then call argc 3 with `surname + given` |
| `initialize` argc 3 | 0x0127, 0x0133-0x0135, 0x0142, 0x015a, 0x0167, 0x0183, 0x0190 | `Array new: 6` x3 (`waku`, `nameStr`, `nameChar`), pad to 6, loops `<= 5` |
| | 0x0117-0x011e, 0x01a8-0x01b3, 0x01d5-0x01df | slot x from const 28 `{{-100,-32,-8,16,48,72,96,168},{-100,-28,-4,20,44,68,92,168}}[mode][i]` (index 0 = 戻る, 7 = 決定) |
| `setChar:` | 0x0009 (`curX < 7`), 0x0031 (`< 4`), 0x0063, 0x00c1 (`< 3`), 0x009b, 0x00a9, 0x00cb, 0x00d6 (`+ 3`), 0x0086 (`4`), 0x00ea, 0x0142 (`7`), 0x011f (`< 6`) | integer arg: `nameStr[curX-1] = code`, `nameChar[curX-1] setCode:`, `moveCursorR` (0x014b-0x0168). String arg (history): copy up to `length` codes, pad with blank, jump to slot 4 or 7. No bound on `length`: more than 3 would overwrite the other name |
| `moveCursor:` | 0x0014, 0x001a, 0x0039 | clamp 0..7, cursor x from const 28 (0x0020-0x0027), zoom for 0 and 7 |
| `clrChar` | 0x000c | `7` special case |
| `getStrH` / `getStrL` | whole method | read `nameStr[0..2]` / `[3..5]`; skip leading blanks; keep an inner blank only if both neighbours are filled; empty gives `GameParam getMyouji` (0x0068-0x006d) / `getNamae` (0x0068) |
| `getStr` (deck) | 0x000c, 0x0029 | same trimming over 6 slots |
| `nameFade` 0x0008, `destruct` 0x0055 | `<= 5` | per-slot loops |

`NameEntry` (ivars: 6-8 button guides, 9 mode, 10 edit, 11 list, 12 menu, 13 curX, 14 curY, 15-16 voice0/1):

- `curX == 7` (confirm): `selectChar` 0x020e. `moveCursor: 7`: `selectChar` 0x0026, `scriptMain` 0x0166, 0x0342.
- `curX < 4` (surname field, selects `voice0`/`voice1` clips): `selectChar` 0x024e, `scriptMain` 0x038e.
- Entry: `scriptMain` 0x0049-0x005f `NameEntryEdit new: 10, 0, GameParam getMyouji, GameParam getNamae`. Callers: `MainMenu` 0x0170 (`NameEntry new scriptMain: 0`, true = confirmed), `DeckEdit >> nameEntry` (mode 1).
- Controls (`ControlPad trig`/`rapid` masks): 32 select, 64 back, 128 delete (`clrChar`), 2048 jump to 決定, d-pad 0x1000/0x4000/0x8000/0x2000, 5/10 move cursor along the name.

## 2. Grid: cursor to character code

All in `NameEntryList` (ivars: 0 base, 1 line (10 x 4 `TextLine`), 2 pageHead, 3 cursor, 4 curX, 5 curY, 6-7 tmpCurX/Y per page, 8 curList, 9 linePos, 10 mode, 11 nextMode, 12 subPage).

- `getChar` (0x0000-0x0016) is `curList[linePos + curY][curX]`. `curList` is an Array of Strings and `String at:` gives the 16-bit code. There is no code table: the glyph on screen is the code.
- Page table: constant 64 of `openPage:` argc 2 (0x0004), six pages, row counts `{5,10,10,7,10,10}` (const 30):

| Page | Tab (sprite 115, frames 0-4) | Content |
|---|---|---|
| 0 | 漢字 | 5 rows of kana heads, `ろよもほのとそこお`... Choosing a head opens a kanji sub-list (const 65, 209 rows in `text/NameEntryList.json`, index map const 66, base `0x82A0` = const 67, header `【あ】` from const 68/70) |
| 1, 2 | ひらがな, カタカナ | 10 rows of 10 |
| 3 | 英数記号 | 7 rows, below |
| 4 | 履歴 | `ShioriData class >> getNameList` (10 rows x 4: surname, given, surname, given of save slots 2i, 2i+1) |
| 5 | (deck mode only) | `WadaiParam getDeckNameList` |

- Menu row to page: `NameEntry >> scriptMain` 0x02a5 `{{0,1,2,3,4},{0,1,2,3,5}}[mode][curY]`. The tabs themselves are graphics (`CommandMenu` items `{{115,0}..{115,4}}`), so English tab names need a texture edit.
- The 263 strings of `text/NameEntryList.json` are 52 grid rows (ids `64.p.r`) + 209 kanji rows (`65.*`) + `【` + `】`.
- **英数記号 (page 3, id `64.3.r`)**, each row 26 bytes: `０１２３４５６７８９　　　`, `ＡＢＣＤＥＦＧＨＩＪＫＬＭ`, `ＮＯＰＱＲＳＴＵＶＷＸＹＺ`, `ａｂｃｄｅｆｇｈｉｊｋｌｍ`, `ｎｏｐｑｒｓｔｕｖｗｘｙｚ`, `⊂⊃∀＃♭♪？！＾～…（）`, `＋－×÷∞♂♀＠☆★＿￣゜`. Codes: digits `0x824F-0x8258`, `Ａ-Ｚ 0x8260-0x8279`, `ａ-ｚ 0x8281-0x829A`, symbols 0x81xx. A blank cell is `0x8140`, which is also the "empty slot" marker.
- Layout: 24 px cells. Rows are `TextLine new: layer+2, -124f, -86+28i, pitch 24, clut 3, scale idx 2` (`initialize` 0x0044). Page 0/3 rows are centred by `setList3` (0x0016-0x0032): `x = -124 + 12·(16 - length)`. Cursor x is the same formula plus `24·curX` (`moveCursor:` 0x0057-0x0083), y `-90 + 28·curY`. Pages 4 and 5 use fixed columns: history x = `-100, -16, 80, 164` (single-use consts 44-47), cursor `{-76,8,104,188}` (const 58); deck `{-34,146}` (const 59).
- Page change restores per-page cursor (tmpCurX/Y); default column `{9,9,9,0,0,0}` (const 71). The first page opened is 0: `NameEntryList >> run` 0x0047-0x004a `openPage: 0`.

## 3. How the name is drawn

- **Entry screen** (`NameEntryEdit >> initialize` argc 3): box `DialogBox new: 1, 20f, 2f` at (24, -160) (slides in from y = -288), about 350 px wide (x -151..199). Six `FontChar new: code, clut 3, layer lay+2, x = const28[mode][i+1], y = -160, 1f, 1f` (0x019a-0x01be), one per slot, starting at alpha 0. `FontChar >> setCode:` (native prim 6) changes the glyph, `setPos:` moves it. Six underline `Sprite` (image 142, y = -144, 0x01c7-0x01ea). A highlight `Sprite` `cursor` (image 0, tex rect 25 x 29, light 0.3/0.6/1.0) at x = const28[mode][curX], pulsed by `vibAlpha` in `run`. Label sprites `text0`-`text4` (images 133/135: ◇, 戻る, ◇ at -56/-52, ◇ at 136, 決定 at 168) and `arrowL/R`.
- Free width: the ◇ markers at x = -56 and 136 leave **-44..128, about 172 px**, for both names, with an 8 px gap between the two 3-slot groups (slots 24 px wide, surname -44..28, given 36..108). A name cannot grow to the left or right: the box artwork (L/R tabs) is fixed.
- **Dialogue** (`Parson >> message:`): plate `messWin put:` of `tempName` or `dispName` (0x002f-0x005a), then `putIndent: 4` (0x0061-0x006a, `push_int 4` at 0x0064), then `LogPage putLine:` (0x006b). `inlineComN` (offsets 0x003a-0x0048, 0x004d-0x005a): `m` -> `GameParam getMyouji`, `n` -> `getNamae`, printed with `messWin put:` (0x006e-0x0078, 0x0080-0x008a). Any length. Backlog `LogLine` has the same `m`/`n` code (0x0032-0x004d) and prints via `putStr:`.
- **Name plate**: `Parson` ivar 13 `dispName`, set from `K2_Script >> setup` constants (`"相　原"`, ...: every plate is 3 cells). For the protagonist `setDispName:` (0x0000-0x008d) re-pads the surname: length 0 gives `"　　　"`, 1 gives `"　c　"`, 2 gives `"c　c"`, 3 or more gives the first 3 characters. The first line prints the plate and the text right after it (command 7 only stores `indent`), and continuation lines indent 4 x 23 = 92 px.
- **Save list** (`ShioriListItem >> initialize:` argc 2): two `TextLine`s, `name0` at x -64, `name1` at `{-70,-34,-10,14}[min(length, 3)]` (const 13, 0x006d-0x0072); positioned in `setPos` 0x0011-0x002d. The row box is 9f x 2f, about 157 px.
- **Credits** (`StaffRoll` 0x0065-0x0076): `"　　ａｎｄ　" + surname + "　" + given` in one `TextLine`.
- **Usage in text**: 2133 lines contain a name token (2157 tokens, max 2 per line, only 8 lines use both). All are dialogue (`Parson`) or backlog. Frequent forms: `{Nm}さん` (261), `{Nm}君」` (218), `{Nm}{W..` (177), `{Nn}」` (110).

## 4. Validation and 履歴

- **Empty name**: `getStrH` returns `GameParam getMyouji` and `getStrL` returns `getNamae` when the trimmed string is empty (0x0068-0x006d). So an empty field restores the current value, which is the default on a fresh game. The screen is also pre-filled from them (`scriptMain` 0x0049-0x005f).
- **No other check**: no forbidden names, no minimum length, no duplicate check, no reset-to-default button. A blank (`0x8140`) is selectable from the blank cells of the grid. Leading and trailing blanks are trimmed. An inner blank stays as a full-width space.
- **Confirm**: `confirm:` (0x0017-0x004a) shows `ConfirmDialog` with `NameEntry:3` "この名前に決定しますか？" (the original text has no name in it). 戻る / × asks `NameEntry:4`/`:5` (abort to main menu / deck selection). On yes, `scriptMain` 0x03f4-0x0412 stores with `setMyouji: edit getStrH`, `setNamae: edit getStrL`.
- **履歴** is not typed-name history. It lists the surname/given-name strings of the 20 save slots (`ShioriData class >> getNameList`: `lastFavor[2i]`, `[2i+1]` as `getMyouji`, `getNamae`; empty slots are `""`). Selecting one calls `setChar: <String>`: a surname goes to slots 1-3 and moves to slot 4, a given name goes to slots 4-6 and moves to 決定. In deck mode page 5 does the same with deck names.

## 5. Proposal

### Constraints (English, widths from `tools/font/en_widths.json`)

| Limit | Value | Source |
|---|---|---|
| Widest / typical glyph | W 22, M, m 20, w 18, most lowercase 12-14, i, l, j 6 | width table |
| `Kouichi`, `Aihara` | 79 px, 70 px | default names (glossary D2) |
| Sample of 112 first / 62 last names | median 71-73 px, 90th percentile 100-113 px | |
| Entry screen, both names | about 172 px, unscaled | section 3 |
| Plate / continuation indent | 92 px (4 cells) | `putIndent: 4` |
| Save list row | about 150 px | `ShioriListItem` |
| History column | 96 px (4 columns over the 384 px grid) | `NameEntryList` |
| Save header | at most 20 characters in total, 8 + 8 leaves 8 bytes | section 1 |

**Choose N = 8 characters per name, and a pixel cap of 96 px per name (at scale 1.0).** The pixel cap is the real limit. 8 characters is the save-header limit, and 96 px equals 4 cells, which fits the history columns and bounds the dialogue worst case. The cap is a constant; 96 to 112 px are all workable if the entry scale below is lowered accordingly.

- Draw the entry screen at **scale 0.75** (`FontChar` sclW/sclH). A 96 px name becomes 72 px, exactly the three 24 px cells of today's field, so both fields and the 8 px gap (152 px) keep their current geometry inside the 172 px. The save list also prints names at 0.75 (150 px). The dialogue and backlog stay at 1.0.
- **Wrap budget for the text reinserter (D-013): reserve 96 px for each `{Nm}` and `{Nn}`**, instead of the true worst case of 8 x 22 = 176 px. The median name is about 70 px, so the average waste is under 30 px of a 552 px line. A line holding both tokens reserves 192 px.
- The plate for the protagonist is the surname, so up to 96 px. Others (translated speaker names in `K2_Script >> setup`) are chosen by the translators; keep them at most 92 px or raise `putIndent:` for everyone (`Parson >> message:` 0x0064, one operand byte).

### (a) Allow N English characters

Keep the slot model and the `curX` logic. Replace the literals with N-derived values. Slot count is `slots = {16, 6}[mode]` so deck names keep working (a new one-line method). Positions are no longer from the const 28 table: slot x is computed from glyph widths, because English glyphs are left-aligned and narrow.

New methods (all on `NameEntryEdit`):

| Method | ~Bytes | Purpose |
|---|---|---|
| `slots` | 8 | `{16,6}[mode]` (2N slots, or 6 for the deck name) |
| `widthOf: code` | 60 | width table (`@EN_WIDTHS`) for `0x8540-0x859F`; 12 for blank/empty; 24 otherwise |
| `slotX: i` | 120 | x of slot i: the left edge of its field (surname -44, given name 36, as today) plus the widths of the preceding slots at scale 0.75; a field is 72 px wide (the original 3 cells), so the given name field does not move while typing |
| `layout` | 180 | `setPos:` of all `nameChar` and `waku` (empty slots get a short underline, filled slots none), called from `initialize`, `setChar:`, `clrChar`; also sets scale 0.75 |
| `fits: code` | 70 | rejects a character if the name would exceed 96 px or N characters (plays the existing error SE 21) |
| `getStr: from to` | 120 | generalised `getStr` (first/last non-blank, inner blanks kept; inner `0x8140` becomes the English space `0x8540`) |

Replaced methods:

| Method | Original | New | Change |
|---|---|---|---|
| `initialize` argc 4 | 101 B | about 101 B | operands only: pad to `N` instead of 3 |
| `initialize` argc 3 | 521 B | about 520 B | arrays of `slots`, loop bounds, `FontChar` scale, positions by `layout` (drops the three const 28 lookups, adds a call) |
| `setChar:` | 365 B | about 300 B | one generic loop for String history entries, bounded by N and by `fits:`; integer branch calls `toEnglish:` (see b) then `layout` |
| `getStrH` / `getStrL` | 115 B each | about 12 B each | `self getStr: 0 to: N` / `N to: 2N` (empty still restores the default) |
| `getStr` (deck) | 110 B | about 12 B | `self getStr: 0 to: 6` |
| `moveCursor:`, `clrChar`, `nameFade`, `destruct` | 99, 82, 54, 119 B | same size | operands: clamp `2N+1`, `7` becomes `2N+1`, loops `<= 2N-1`; cursor x from `slotX:` |

Other classes:

| Class / method | Change | Bytes |
|---|---|---|
| `NameEntry >> selectChar` (0x0026, 0x020e, 0x024e), `scriptMain` (0x0166, 0x0342, 0x038e) | `7` becomes 17 (2N+1), `4` becomes 9 (N+1) | 6 operands, 0 |
| `NameEntryList` consts 44-47, 58 | history column x `-124, -28, 68, 164` (left edges -136, -40, 56, 152), cursor `{-88, 8, 104, 200}` | 5 constants, 0 |
| `Parson >> setDispName:` | plate = the surname unchanged (empty: `"???"`), no 3-cell padding | 143 to about 35 B |
| `ShioriListItem >> initialize:` argc 2 | name font scale 0.75, `name1X = -64 + 0.75·width(surname) + 8` instead of the `{...}[min(len,3)]` table | about +40 B |
| `GameParam` consts 166/167, `K2_Script` const 13 | default names (c) | 3 constants |
| `ShioriData >> set` (optional) | truncate copies to N characters as a safety net for the 256-byte header | about +30 B |

Net: about +350 B of bytecode in `NameEntryEdit`, about 0 elsewhere (the plate patch shrinks it); 6 new + 8 replaced methods + about 80 literal operands. The decompressed `SCRIPT.IMG` grows by under 1 KB, negligible next to the translation text; the image is relocated anyway (D-014).

### (b) Enter English codes

Smallest change: **keep the 英数記号 page and map on input.** The page keeps showing the original full-width glyphs at 24 px (D-012 keeps them), so the cursor and the 24 px grid code stay as they are. New method `NameEntryEdit >> toEnglish: code` (about 110 B) is called from the integer branch of `setChar:` (0x014b-0x0168) before the store:

| Input | Output |
|---|---|
| `Ａ-Ｚ 0x8260-0x8279` | `0x8561-0x857A` (`code + 0x301`) |
| `ａ-ｚ 0x8281-0x829A` | `0x8582-0x859B` (`code + 0x301`) |
| `０-９ 0x824F-0x8258` | `0x8550-0x8559` (`code + 0x301`) |
| `！ 0x8149`, `？ 0x8148`, `－ 0x817C`, `＿ 0x8151`, `．` | `0x8541`, `0x855F`, `0x854D`, `0x8580`, `0x854E` |

Codes outside the table pass through unchanged. English codes are not in these ranges, so it is idempotent for history strings. All three ranges map with the same `+ 0x301` (checked against `tools/font/encoding.py`: `A` 0x8561, `Z` 0x857A, `a` 0x8582, `z` 0x859B, `0` 0x8550), so the method is three range tests and one addition.

Page 3's last row can be reworded in `text/NameEntryList.json` (`64.3.6`, 26 bytes) to hold the punctuation names need (`．` `’` `－` `＿`), mapping `’` (0x8166) to `'` `0x8547`. A real space is the blank `0x8140`; `getStr:to:` converts inner blanks to `0x8540`.

Optional polish (not needed for the first pass): put English codes into rows `64.3.1-64.3.4` (13 characters x 2 bytes = 26 fits the budget). Then `TextLine >> setText:` (D-015) draws them proportionally and the cursor must follow: `setList3` 0x0016-0x0032 and `moveCursor:` 0x0057-0x0083 use `line xOf: curX` instead of `24·curX`, rows left-aligned. About +60 B in two methods.

Also change the first page to 英数記号, because kanji is useless to English players: `NameEntryList >> run` 0x0048 (`openPage: 0` to `3`), `NameEntry >> scriptMain` 0x0089 (`CommandMenu` third argument `0` to `3`, inferred as the initial row) and 0x014b (`curY = 0` to `3`). Three operand bytes. The tab and button-guide labels are sprites (image 115, 133, 135, button guides) and belong to the graphics work.

### (c) Default name in English

`GameParam` constants 166 and 167 become `Aihara` and `Kouichi` (`byte_budget` 4 is irrelevant: strings are referenced by index), `K2_Script` constant 13 becomes `Aihara`. `setMyouji:` rewrites the plate on every new game and every load (`restoreShioriBody` calls it), so the plate follows. The entry screen shows the existing names, so the defaults appear pre-filled (6 and 7 characters, within N = 8).

### Risks

| Risk | Detail / mitigation |
|---|---|
| Save header overflow | 16 characters give 248 of 256 bytes, with assumptions: Integer = 4 bytes, `lastFavor` = 8 entries, Strings 2 bytes/char. Not tested. Test: save with `iiiiiiii` / `llllllll` (16 narrow characters, passes the pixel cap), read slot 1 back and check the 20-slot list. Safety net: truncate in `ShioriData >> set`. |
| Save compatibility | Old Japanese saves (at most 3 characters, 2-byte codes) load unchanged. The format has no version field, so an English-name save loaded in the Japanese build would just show full-width garbage; irrelevant for the release. |
| `Integer >> asChar` and `String toByteArray` with `0x85xx` | `asChar` (native 0x119358) emits the lead and trail bytes with no range check, then a native string constructor (`0x116170`) builds the String. Text constants already use these codes, but the `asChar` path (`getStrH`, `getStr`) and serialization have not been run with them. Test in the emulator with `Aihara`. |
| Blank marker | `0x8140` is both the grid's empty cell and the unused slot. Inner spaces need the `0x8140` to `0x8540` conversion in `getStr:to:`. Selecting a blank cell mid-name types a space. |
| Deck names | Mode 1 shares `NameEntryEdit` (6 slots, `getStr`, 24 px cells). Keep it at 6 slots, or give it the same proportional layout; separate decision, owner of the deck-name text. |
| Other screens that print the name | Dialogue and backlog work unchanged (width table via `putChar`). Credits use `TextLine` (proportional via D-015). Save list and plate need the two patches above. Calendars and the topic deck do not print it. |
| Layout verification | `FontChar` is left-aligned in a 24 px cell. At scale 0.75 the sprite centre is `left + 9`, not `+ 12`. `layout` and `slotX:` must use that. The `waku` underline (image 142) needs `Sprite >> setScale:` for width; verify in the emulator. |
| Voices | `voice0/voice1` clips (const 56/58 in `scriptMain`) are Japanese recordings of the heroine saying the name; they play when the cursor leaves a name. Unchanged and unrelated to the typed letters. |

Verification plan (emulator, `tools/qa/emu.sh`): new game, enter `Aihara` / `Kouichi`, then 8 + 8 of `W`/`i` to check the cap and the layout; confirm; check the first line (plate), a `{Nm}` line, the backlog and the credits; save, load and open 履歴; compare a Japanese save loaded in the patched build.
