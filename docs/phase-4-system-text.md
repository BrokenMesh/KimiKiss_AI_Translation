# Phase 4: system text limits

Where each of the 1,193 `route: "system"` strings is drawn and how much room English has. Machine-readable form: `tools/reinsert/limits.json` (`{id: {display, max_px, lines, translate, note}}`, one entry per record; the `note` carries the per-record detail). All numbers come from the SCF disassemblies (`tools/extract/scfdis.py`); nothing here was run in the emulator yet.

English advances are `width[c] * scale` px in the message window and `width[c] * pitch / 24` px in `TextLine`/`TextLineC` (D-013, D-015). Average English glyph is about 12.7 px at scale 1.0.

## Summary

| Group | Records | Translate |
|---|---:|---|
| Debug console (`System.println`/`print`): EventTable, GameMain, GameParam, K2_Script, WadaiReaction, RoomMenu | 470 | no |
| Exception messages, padding constants, dead helper (`K2_Script:81.*`) | 42 | no |
| Name-entry selection grid (`NameEntryList`) | 263 | no |
| `ConfirmDialog` (memory card, save/load, confirmations) | 185 | yes |
| Message window (dialogue lines, speaker names, choice, topic names) | 83 | yes |
| `TextLine` (credits, deck names) | 148 | yes |
| Default player name | 2 | yes |

`System.println`/`print` are native primitives 1 and 0 of `System`. The only native users of `SjisToEuc` (`0x0011ab10`) are three string printers (`0x0011abbc`, `0x0011ae78`, `0x0011af54`) that call a printf-style function (`0x001619c8`, stdout). I did not map each primitive to a specific printer, but nothing on that path draws sprites, and no script draws these strings.

## How each consumer handles text

| Consumer | Line break | Width logic | Notes |
|---|---|---|---|
| `ConfirmDialog` | `\n` (10) and `／` (0x815E) split lines; nothing else does | Box and text width = longest line **in characters** x pitch 18 (plus 18 for lines after the first), see below | one centred `TextLineC` per line |
| `TextWindow` (via `Parson>>message:`) | `／` only; `\n` is dropped (code <= 256) | Per-character wrap at 552 px (patched `putChar:` uses the width table) | 3 lines, 44 px apart |
| `TextLine` / `TextLineC` | none: code 10 would be drawn as a glyph | none; positions from `xOf:` (D-015) | one string = one line; `Vector new: 30` for glyphs is growable, no character cap |

### ConfirmDialog geometry

`ConfirmDialog>>initialize` (7 args; the 6-arg form appends frame type 3). Every call site in the game passes `layer 15` (12 in `RoomMenu`), `x 0`, `y 0`, `width nil`, so the dialog is centred on screen.

- Text: `TextLineC` pitch `toInteger(24 * 0.75) = 18`, font scale index 1 (0.75), line height `toInteger(28 * 0.75) + 3 = 24`. English advance = `width * 0.75`.
- Mode (arg 6): 0 = text only, 1 = one OK button, 2 = yes/no. Modes 1 and 2 add two blank lines of height for the buttons (button sprites, not text).
- Height = `(lines [+2]) * 24`, centred on y 0. Nothing checks the screen: 14 lines in mode 1/2 is (14 + 2) x 24 = 384 px plus a 16 px frame, 400 of the 448 px screen.
- Width when `width` is `nil`: first pass counts characters per line (breaks at 10 and 0x815E), `textW = maxChars * 18`. `DialogBox` is a 16 px 9-slice scaled to `textW / 16`, total width `textW + 32`. When a width is passed the engine clamps it itself (`< 128 -> 96`, `> 608 -> 576`, else `-32`), which shows the design limit: **576 px of text, 608 px box on a 640 px screen**. Original maximum is 31 chars (558 px) in `SystemSave:10.4` and 6 lines.
- **ConfirmDialog is patched** (`ConfirmDialog.initialize7.asm`, D-017): with `width` nil the box width is the pixel width of the longest built line (`xOf:`), so `max_px` 576 is right. The character count is still used for wrapping when a width is passed (no call site does).

### Message window

Geometry is in `phase-3-text-engine.md` (552 px line, 3 lines, indent 92 px). Speaker names: `Parson>>message:` puts `dispName`, then `putIndent: 4`, which only sets the indent used by **later** lines. Line 1 therefore is `name + text` with no gap, and lines 2-3 start at 92 px. Wrap budget for a speaker line: first line `552 - width(name)`, continuation lines `460`. Narration (`SYS`, `dispName` nil) has no name and no indent: 552 on every line.

## Groups

`max_px` is the width of one line. "Hard" = taken from code or screen geometry; "orig" = original Japanese width, used where no limit could be found.

### ConfirmDialog (`display: ConfirmDialog`, 185 records)

| Ids | Mode | Lines | max_px | How determined |
|---|---|---:|---:|---|
| `MemoryCard:11.1,2,3,5` (status text) | 1 | 5 | 576 | hard (clamp); also first part of the `MemoryCardCheck` text, see below |
| `MemoryCard:11.4,6` | 1 | 14 | 576 | hard; used by save/succession `displayError` only |
| `MemoryCardCheck:9.19` | 2 | 8 | 576 | hard; text = status + `\n\n` + this string, total <= 14 lines |
| `SaveMenu:44.{7,11}`, `SystemSave:10.7`, `LoadMenu:44.14`, `ConfigSave:0.20`, `SystemSave:10.21` | 2 | 14 | 576 | hard (format / overwrite / load / settings-changed questions) |
| `SaveMenu:44.{8,10,18}`, `SystemSave:10.{8,10}`, `ConfigSave:0.10`, `LoadMenu:44.{15,18}`, `Succession:26.10` | 0 | 14 | 576 | hard ("in progress" notices, no buttons, auto-closed by code) |
| `SaveMenu:44.{9,12,13}`, `SystemSave:10.{9,12,13}`, `ConfigSave:0.{12,13}`, `LoadMenu:44.{16,17}`, `MainMenu:79.22` | 1 | 14 | 576 | hard (done / failed notices) |
| `Succession:18,46`, `SystemSave:24`, `RoomMenu:75`, `NameEntry:3,4,5` | 2 | 14 | 576 | hard; `RoomMenu` uses layer 12 |
| `Succession:43,44` | 1 | 14 | 576 | hard |
| All other `*:N.k` of the eight memory-card classes | - | 14 | 576 | unreachable duplicates (no code pushes that index); keep identical to the live copy |

Each of `ConfigSave`, `LoadMenu`, `MainMenu`, `MemoryCard`, `MemoryCardCheck`, `SaveMenu`, `Succession`, `SystemSave` carries its own copy of the same 22-message table. Only `MemoryCard`'s indexes 1-6 (the card status messages, chosen by `printStatus`, `printStatusForSave`, `...ForLoad`, `...ForSucceed` through lookup arrays such as `{0,1,0,0,2,3,5}`) and a few per-class indexes are ever shown; the rest are dead. Translate the table once and copy it.

### Message window (`display: TextWindow`, 83 records)

| Ids | Drawn by | max_px | Lines | How determined |
|---|---|---:|---:|---|
| `GameMain:135,137,172,176`, `K2_Script:191,192` | `PLY :` / heroine `:` | 552 (first line minus name, others 460) | 3 | hard (window geometry) |
| `K2_Script:75,77,78` | `SYS :` in `K2_Script>>scriptMain` (developer test, story classes override it) | 552 | 3 | hard |
| `K2_Script:240`, `WadaiTable:*`, `K2_Script:241` | one `SYS :` line built in `K2_Script>>getWadaiDemo`: `240 + topic name + 241` | sum <= 552; budgets 200 / 250 / 100 | 1 | hard for the sum; split is a suggestion |
| `MainMenu:45.1` | `SYS :` with Array `{2, text}`: `TextWindow>>select:` | 552 per choice (selector bar 560) | exactly 2 | hard |
| `K2_Script:13,19,22,...,58` (21 speaker labels) | `Parson>>message:` `dispName` | 92 | 1 | hard (indent 4 x 23); JP is 3 cells = 69 px |

- The topic text is one runtime-concatenated string, so you cannot insert `／` after the fact, and the engine wraps per character (mid-word). Keep it on one line.
- Speaker slots: 13 PLY, 19 YUM, 22 NAR, 24 MAO, 26 ASU, 28 ERI, 30 MIT, 32 NAN, 34 AKI, 36 TOM, 38 MEG, 40 GUN, 42 KAO, 44 MAN, 46 MIC, 48 KEI, 50 EX1, 52 EX2, 54 ETB (boy), 56 ETG (girl), 58 ETC (`？？？`). Names are stored verbatim by the constructor and are not truncated. They also appear in the backlog. `PLY`'s label is replaced by the player's surname as soon as it is set (`GameParam>>setMyouji` -> `Parson>>setDispName:`, which keeps the **first 3 characters**).
- `Parson>>setName:` (alternate speaker label) also keeps 3 characters.

### TextLine (`display: TextLine`)

| Ids | Layout | max_px | Lines | How determined |
|---|---|---:|---:|---|
| `StaffRoll:*` (146) | `StaffRoll>>run`: `TextLine` layer 9, pitch 24, scale 1.0, first glyph centred at x -256 (left edge -268), scrolls up from y 240; 18 reusable lines | 560 | 1 | screen edge 320 -> 588 hard, 28 px safety margin; orig 19 chars = 456 px |
| `WadaiParam:10` | prefix of `WadaiParam class>>init` default deck names: prefix + two full-width digits (`話題袋０１`..`話題袋２０`) | 96 | 1 | orig: 6-cell name (144 px) minus the 2 digits |
| `WadaiParam:28.0` | name of the first deck, same display | 144 | 1 | orig 6-cell name |
| `GameParam:166,167` | default surname / given name | 72 | 1 | `NameEntryEdit` has 3 + 3 cells of 24 px |

- `StaffRoll:23` is `"　　and　"`, then `getMyouji`, `StaffRoll:25`, `getNamae`: the player's name is credited at run time. `StaffRoll:20` replaces row 182 only after the game is cleared.
- Deck names appear in three places: `DeckListItem` (`TextLine`, pitch 24, name begins 160 px left of the row centre; the first counter sprite sits at the centre in edit mode, so about 160 px), `DeckView>>setName` (`FontChar` positions from `xOf:` at pitch 26, cut at 156 px = 6 Japanese characters, D-017) and the `NameEntryList` deck page. `NameEntry` holds 6 cells, so decks cannot exceed 6 characters.
- Leading `U+3000` pairs in credits are 48 px indents. English can keep them (0x8140 still advances 24 px).

### Not translated

| Ids | Why |
|---|---|
| `EventTable:*` (377) | element 31 of each row; only used in `println("..発生：" + title)` |
| `GameMain`, `GameParam`, `K2_Script` (155-227), `RoomMenu:48`, `WadaiReaction` | console output / error text |
| `K2_Script:81.*` | event category names for `getEvCtgName:`, which nothing calls |
| `SerializeData:31`, `StringStream:3`, `StringInputStream:3`, `TextWindow:129`, `Vector:10` | `Exception` messages; no script draws exception text (a native uncaught handler might print it to the console, not checked) |
| `NameEntryEdit:32`, `Parson:202,203` | `U+3000` padding; `NameEntryEdit>>getStrH` compares cells against 0x8140 |
| `NameEntryList:*` (263) | the selectable characters of the name-entry grid (`TextLine`, pitch 24) and the `【` `】` page-header brackets (`NameEntryList:68,70`). Changing them changes what can be typed; this is a name-entry redesign |

## Surprises

1. **ConfirmDialog sizes its box from a character count** (x 18 px), not from pixels, and is the only consumer that understands `\n`. Insert `\n` yourself; it will not wrap.
2. **`\n` is wrong in the message window** (dropped) and in `TextLine`/`TextLineC` (drawn as a glyph). Only `ConfirmDialog` strings use it. Use `／` in the message window.
3. **Runtime concatenations** (measure the sum):
   - `MemoryCardCheck>>displayError`: `MemoryCard>>printStatus` + `"\n\n"` + `MemoryCardCheck:9.19`;
   - `K2_Script>>getWadaiDemo`: `240` + `WadaiParam getName:` + `241`;
   - `WadaiParam class>>init`: `話題袋` + two full-width digits;
   - `StaffRoll`: `"　　and　"` + surname + `"　"` + given name;
   - `Parson>>message:`: `dispName` + text.
4. **Eight copies of one 22-string table**, with only `MemoryCard` indexes 1-6 and 27 other (class, index) pairs live.
5. **Fixed sizes**: player name 3 + 3 cells (`NameEntryEdit`), speaker `dispName` set from the name keeps 3 characters, `Parson>>setName:` 3 characters, deck names 6 characters (hard cut in `DeckView`). `en_text.NAME_PX` is `13 * 12 = 156` as a placeholder; 3 characters need at most 3 x 23 = 69 px per name part when typed from the Japanese grid (full-width Latin and kana both advance 23 px in the message window).
6. **No text for topic cards.** Only `DeckView` and `DeckListItem` draw deck names; `Wadai*`, `Topic*` and the menu classes use `Sprite` only, so topic icon and menu labels are in the graphics (`GRAPH0.PAC`), not in these strings.
7. **Dead code in text**: `K2_Script:75,77,78` are the body of a test script, and `K2_Script:81.*` is unused. They are cheap to translate or skip.
8. **Not verified**: how `ShioriData` stores the player name (save-slot size), and whether a native handler displays exception messages. Both would only tighten the limits above.
