> Research notes written before the Easy Mode patches (D-038, [../easy-mode.md](../easy-mode.md)). Placeholder sends such as `Cheat noLoss` became `GameParam easy: bit`; helper scripts and draft patches named below (`research/...`, `scratchpad/...`) were session scratch files and are not in the repository. Disassemble with `python3 tools/extract/scfdis.py build/work/script_orig/<Class>.scf`.

# Easy mode: where to store 4 flags and how to let the player switch them

Read-only research on the original classes (`build/work/script_orig`), disassembled with
`tools/extract/scfdis.py`. Offsets are bytecode offsets inside the named method. "Class side" =
`methods2` table; on the class side `push_ivar n` / `store_ivar n` address **class variable n**
(fields2 id). The disassembler then prints the *instance* ivar name of the same number, which is
wrong (e.g. `store_ivar 20` in `GameParam class >> setActuator:` is `actuator`, not `ivar 20`).
"Unverified" marks things not checked in the emulator or the ELF.

## Summary

- **Storage: use GameParam class variable 18 `autoSkip`.** It is a dead setting. `GameParam class >> init`
  sets it to `false` (0x03f6) and it is saved and restored in the config sub-array of the
  system data. No script reads it anywhere else: the only `GameParam .autoSkip` references are in
  GameParam's save/restore methods. `TextWindow`'s own `autoSkip` is a different variable. Store an
  Integer bitmask there (bit 0 no losses, 1 fewer rejections, 2 easier meetings, 3 more attempts).
  `makeSystemData`, `makeConfigData:` and `restoreSystemData:` already copy it, so **no save/load
  code changes** are needed. The serializer is self-describing (type-tagged), so an Integer in a
  slot that used to hold a Boolean is legal. Old saves restore `false`, which reads as 0. The
  unpatched game ignores the value. The system data grows by 3 bytes. The unused texture
  `menu_set1` "自動文字送り / Auto Advance" shows this was a cut auto-advance setting.
- **Read from anywhere:** add class-side `GameParam easyFlags` / `easy: bit` / `setEasyFlags:` (about 15–40 bytes each).
  Any class can call `GameParam easy: 1`. Without a method, `push_classvar class:GameParam 18` also works,
  but it needs a nil/Boolean guard.
- **Menu: recommended is a new "Easy Mode" item on the title main menu that opens a small modal
  panel drawn with `DialogBox` + `TextLine`/`TextLineC` (the text system).** An unused texture is
  already in GRAPH0 and preloaded: `sysgraph/menu_main4` "オプション" (sprite 114, n = 4, 112 x 32).
  Only its English in `translation/textures.toml` changes ("Options" → "Easy Mode"). On exit it reuses the
  existing "Settings changed. Save?" flow (`ConfigSave new scriptMain`).
- Adding 4 rows to `ConfigDialog` is possible: it has 2 unused ivars, and the cursor wrap follows the
  row-table length. But it means replacing about 12 methods (initialize 700 B, run 907 B, enable/disable,
  fade, …), resizing the panel, moving every row, and keeping about 70 glyph sprites alive for the whole
  game. See §2.5.
- Tooling gap: patch strings are encoded as cp932 (`scfasm.Pool.parse`). English needs the 0x85xx
  codes of D-012, so `scfasm` needs an `en:"…"` constant (a few lines using
  `tools/reinsert/en_text.encode_translation`, plus a tokenizer fix). Optionally it also needs an
  array-constant syntax.

---

## 1. How settings are stored and saved

### 1.1 Where the values live

The settings are **class variables of `GameParam`**, not instance variables. The `GameParam` instance
(class variable 7 `curInstance`) holds per-playthrough state that goes into the slot save body.

`GameParam` fields2 (class variables), id → name: 4 eventTable, 5 encountTable, 6 available,
7 curInstance, 8 evList, 9 tmpEvFlag, 10 tmpDeai, 11 evFlag, 12 alFlag, 13 clFlag, 14 lastClear,
15 lastStory, 16 wallPaper, 17 whFlag, **18 autoSkip**, 19 messSpeed, 20 actuator, 21 musicVolume,
22 soundVolume, 23 voiceVolume, 24 voiceSwitch. Ids start at 4; 0–3 are not declared. Instance fields
0–19 run from myouji to figure.

Defaults are set in `GameParam class >> init` (argc 0, 1115 B):
```
03f5: 29        push_false
03f6: 21 12     store_ivar 18        ; autoSkip := false
03f8..03fe      self setMessSpeed: 0
03ff..0404      self setActuator: true
0405..040b      self setMusicVolume: 4
040c: 24 04 / 040e: 21 16             ; soundVolume := 4
0410..0416      self setVoiceVolume: 5
0417..043a      voiceSwitch := Array new: 10, all true   (store_ivar 24, loop 0..9)
```
Also from `init`: evFlag (11) = `Array new: 1800` (0x0333), alFlag (12) = `Array new: 250` (0x033c),
clFlag (13) = Array 8 of Array 3.

Class-side accessors (all `methods2`): `getActuator` = `push_ivar 20; return_top`; `setActuator:` =
`store_ivar 20` with no clamping (7 B); `setMessSpeed:` clamps 0..3 into 19; `setMusicVolume:` and
`setVoiceVolume:` clamp 0..5 and call `Sound setVolume` / `setVoiceVolume`; `setWallPaper:` stores 0..8
into 16. There are **no** accessors for 18 autoSkip, 22 soundVolume or 24 voiceSwitch.

Reset to Default is `ConfigDialog >> setDefault` (argc 0, 87 B). It sets messSpeed 0, actuator true,
music 4, voice 5 and wallpaper 0 through the dialog and the GameParam setters. It does not touch
autoSkip, soundVolume or voiceSwitch.

### 1.2 Serialization format

`SerializeData >> serialize:` (argc 1, 554 B) turns an Array into a self-describing byte stream:
each element is one type byte and its data, and a 0 byte ends the array.

| tag | type | bytes |
|---|---|---|
| `N` 78 | nil | 1 + 1 (`ByteArray new: 1`, 0x0030–0x0041) |
| `B` 66 | Boolean | 1 + 1 (0x0048–0x0085) |
| `I` 73 | Integer | 1 + 4 (0x0088–0x00a5) |
| `F` 70 | Float | 1 + 4 |
| `S` 83 | String | 1 + 4-byte length + bytes |
| `A` 65 | ArrayedCollection | 1 + recursive (0x0165–0x0183) |

`streamRestor:` (247 B) reads it back into an **Array of whatever length was stored**: a Vector is
filled until the 0 terminator, then copied to `Array new: n` (0x00c1–0x00f3). An unknown tag throws
`SaveDataFormatErrorException`. **There is no fixed layout and no schema.** Arrays may grow, and any
slot may change type.

### 1.3 System data (global settings, shared by all save slots)

`GameParam class >> makeSystemData` → instance `makeSystemData` (argc 0, 212 B) builds
`Array new: 13` (0x0002):

| idx | content |
|---|---|
| 0 | config `Array new: 6` (0x000b): `[0] autoSkip, [1] actuator, [2] musicVolume, [3] soundVolume, [4] voiceVolume, [5] voiceSwitch` (0x0014–0x0049) |
| 1, 2, 3 | evFlag, alFlag, clFlag |
| 4, 5, 6 | `WadaiParam getCollection`, `getDeckAll`, `getCurDeckNum` |
| 7 | `ShioriData getNum` |
| 8, 9 | lastClear, lastStory |
| 10 | wallPaper |
| 11 | whFlag |
| 12 | messSpeed |

`restoreSystemData:` (argc 1, 451 B) reads it back and is **already version-tolerant**:
```
0011: ... at 0 at 0   0014: 0a 13 12  store_classvar 19, 18   ; autoSkip := cfg[0]   (no type check)
0021: send #setActuator  (cfg[1])     002f: #setMusicVolume (cfg[2])
003b: store_classvar .soundVolume (cfg[3])   0048: #setVoiceVolume (cfg[4])
0054: store_classvar .voiceSwitch (cfg[5])
00b9: length >= 9  -> lastClear ; 00d3: length >= 10 -> lastStory ; 00ed: length >= 11 -> wallPaper
0131: length >= 12 -> whFlag (else rebuilt) ; 01a7: length >= 13 -> messSpeed (else 0)
```
The developers already appended indexes 8–12 in later versions behind `length >=` checks. A 14th
element would be the "official" way to add data. It is not needed if autoSkip is reused.

`makeConfigData:` (argc 1, 180 B, used by `ConfigSave >> saveSysData` at 0x0070) takes the bytes
read from the card, restores them, copies them into a fresh `Array new: 13` (0x0004, `copyFrom`),
overwrites `cfg[0..5]` (0x0019–0x0060), [10] wallPaper and [12] messSpeed, and re-serializes.

When system data is written:
- At the title: `Configuration >> scriptMain:` with arg 0 (`MainMenu scriptMain` 0x0447) ends with
  `GameParam checkConfig: snapshot` (0x0299). If anything changed, it runs `ConfigSave new scriptMain`
  (0x02a1). That shows the "設定が変更されました。セーブしますか？" prompt and then runs `saveSysData`:
  read 10240 B, `makeConfigData:`, `writeSystemData`.
- On every slot save: `SaveMenu >> selectShiori` 0x01d0 `GameParam makeSystemData`, then
  `writeAllData` (header, body, system).
- At the ending: `GameMain scriptMain` 0x0052 `SystemSave new scriptMain` (`makeSystemData` 0x0050).
- `Succession >> execution` (carry over from the first KimiKiss) restores the old system data
  (0x0094) and writes it again (0x00a0).
- Load: `MainMenu >> memCardCheck` 0x003a–0x0060 (`ByteArray new: 10240`, `readSystemData`,
  `restoreSystemData:`). After a `RestartException`, `K2_Script >> setup:` 0x020b restores the
  array that GameMain kept.

Size: every reader allocates `ByteArray new: 10240` (MainMenu 0x003c, ConfigSave 0x0054). The native
memory-card code (`0x0010ad00`/`0x0010ae00`) seeks within the save file with 0x2800 (= 10240) and
0x32000 constants, so the system block is probably a fixed 10240-byte area (unverified). Not
measured: the current serialized size. A pessimistic estimate is about 8.5 KB (evFlag 1800 × 2 B,
alFlag up to 250 × 5 B, whFlag 8 × 3 × 8 ints, topic collection and decks unknown). +3 bytes is
noise, but measure it once in the emulator if Design B (adding many values) is chosen.

The per-slot save (`makeShioriBody`/`restoreShioriBody`, instance) is another place. Flags there
would be per playthrough. The system data is the right place for a setting.

### 1.4 Spare places (no format change)

| place | saved? | read by game? | fits 4 flags | notes |
|---|---|---|---|---|
| **classvar 18 `autoSkip`** (cfg[0]) | yes (system data) | **no** (only make/restore/init) | Integer bitmask | default `false`; +3 bytes when an Integer; old data and the old-KimiKiss carry-over give Boolean → treat a non-Integer as 0. **Recommended.** |
| classvar 24 `voiceSwitch` (cfg[5]) | yes | **no** | 10 Booleans, all `true` by default | 0 bytes extra, but old saves hold `true` → "cheat on" would have to be `false` (inverted), or an extra "initialised" marker would be needed |
| classvar 22 `soundVolume` (cfg[3]) | yes | **no** (stored at 0x040e, never read) | Integer | default 4 → needs an offset encoding (e.g. value ≥ 16 means flags = value − 16); ugly |
| new system-data index 13 | yes | n/a | anything | needs `Array new: 14` in `makeSystemData` and `makeConfigData:` (both replaced) and a `length >= 14` branch in `restoreSystemData:`; the old game ignores the extra element. `makeConfigData:`'s `Array new: 13` + `copyFrom` of a 14-element restore would probably overflow if the 13 were not changed (unverified `copyFrom` semantics) |
| new class variable | — | — | — | fields2 cannot be added by the patch tools; how the VM sizes class-variable storage is not verified. Not needed |

Verification command used: `grep -h "GameParam \.[a-zA-Z]*" -o dis/*.dis | sort | uniq -c`. All
`.autoSkip`, `.soundVolume` and `.voiceSwitch` hits are in `GameParam.dis`. Class-side uses of ivar
18/22/24 are only in `init` (0x03f6, 0x040e, 0x041e/0x042c).

### 1.5 Cheap access from game code (sketch, scfasm syntax)

```
; add: GameParam easyFlags argc=0 table=methods2
; reason: easy-mode bits in class variable 18 (autoSkip: saved in system data cfg[0], never read)
push_nils 1
push_ivar 18                 ; class side: class variable autoSkip
store_temp 0
push_temp 0
push_nil
identical
jump_if_false L1             ; nil (init not run): 0. Needed: Nil >> isKindOf: throws (qa-scfvm.md assumption 4)
push_int 0
return_top
L1: push_temp 0
push_const class:Integer
send 1 #isKindOf
jump_if_false L2             ; false/true from old saves or carry-over: 0
push_temp 0
return_top
L2: push_int 0
return_top

; add: GameParam easy argc=1 table=methods2        ; GameParam easy: 4  -> Boolean
push_nils 0
push_self
send 0 #easyFlags
push_temp 0
op &
push_int 0
op <>
return_top

; add: GameParam setEasyFlags argc=1 table=methods2
push_nils 0
push_temp 0
store_ivar 18
return_self
```
Call site anywhere: `push_const class:GameParam; push_int 2; send 1 #easy; jump_if_false …`.
`and`/`or` do not short-circuit (`docs/qa-scfvm.md`, assumption 4), so keep the nil guard as a
jump.

---

## 2. ConfigDialog

### 2.1 Objects

`ConfigDialog` (superclass Object) has 22 ivars: 0 base, 1 messSpdT, 2 messSpdV, 3 padAct, 4 padActSw,
5 musicT, 6 musicV, 7 voiceT, 8 voiceV, 9 themeT, 10 themeV0, 11 themeV1, 12 default,
**13 arrowL, 14 arrowR (never read or written in any ConfigDialog method: spare)**, 15 cursor,
16 curY, 17 nextCurY, 18 state, 19 stateNext, 20 exec, 21 avail.

One instance lives for the whole game: `K2_Script >> setup:` 0x022b `ConfigDialog new` →
`store_classvar 0, 4` (K2_Script class variable `CONFIG`). `initialize` argc 0 → `initialize: 12`
(the layer).

`initialize:` (argc 1, 700 B). The sprite ids are records of the executable sprite table:

| ivar | `Sprite new: id, n, layer` | texture (English) | closed pos | open pos (run state 1) |
|---|---|---|---|---|
| base | `DialogBox new: 3, 16f, 12f, L` (0x000c), setPos 504,-8, alpha 0.8, restart | 9-slice | 504,-8 | 24,-8 |
| messSpdT | 147 | menu_set9 "Text Speed" (80x32, enlarged to 120x32 by D-035) | 432,-96 | -48,-96 |
| messSpdV[0..3] | 76 (idou/cursor_l) | gauge marks | x {536,552,568,584}, -96 | {56,72,88,104} |
| padAct | 121 | menu_set2 "Rumble" (40x32 → 120x32) | 412,-64 | -68,-64 |
| padActSw[0] / [1] | 144 / 145 | menu_set6 "Yes" / menu_set7 "None" (40x32 → 64x32) | 560,-64 | 80,-64 |
| musicT | 123 | menu_set4 "BGM" | 412,-32 | -68,-32 |
| musicV[i][0/1] | 17 / 12+(i&6) | gauge notes | {512..608},-32 | {32..128} |
| voiceT | 122 | menu_set3 "Voice" | 412,0 | -68,0 |
| voiceV | 17 / 12+(i&6) | gauge | | |
| themeT | 146 | menu_set8 "Wallpaper" | 412,32 | -68,32 |
| themeV0/V1 | 145, then `setTex: 106, n` (sysgraph/sd%1d0 thumbnails) | | 560,32 | 80,32 |
| default | 143 | menu_set5 "Reset to Default" (144x32) | 460,80 | -20,80 |
| cursor | 98 n 0, layer L+2 | sysgraph/cs | | x -104/-100 (blink), y = row table |

Row table: constant 53 `{-96f, -64f, -32f, 0f, 32f, 80f}`. Rows are 0 Text Speed, 1 Rumble, 2 BGM,
3 Voice, 4 Wallpaper, 5 Reset (48 px gap before Reset).

Panel geometry: `DialogBox >> setScale:` sets `ofsX = 8*sclW + 8`, `ofsY = 8*sclH + 8`, and the 9
pieces sit at ±ofs. With 16 x 12 the half extents are 136 x 104 around (24,-8), so x is about
-112..160 and y about -112..96 (plus the corner pieces).

### 2.2 Driving

- `ConfigDialog >> run` (907 B) runs on its own Thread (`initialize:` 0x02b0). It is a state machine
  on `stateNext`: 1 = open (moves every sprite in, 9 frames), 2 = close (moves out, then `hide`),
  3 = cursor move to `nextCurY` (0x0308–0x032f), 4 = cursor blink (0x033a–0x0382).
- `moveCursorD`/`moveCursorU` (31/37 B): `(curY ± 1) % (const53 length)` → nextCurY, `stateNext := 3`,
  SE 12. **The wrap follows the length of the row table.**
- `selectValueL`/`selectValueR` (102 B each): branch on curY 0..4 to `del*/add*`. curY 1 →
  `toglePadAct` in both directions. Returns SE 12 if handled.
- `enable:`/`disable:` (262/252 B): `avail`, `fadeLight` 1.0 or 0.75 on every sprite, refresh every
  value from GameParam, cursor setPos/fade.
- `fade:t:m:` (295 B), `show:`/`hide:` (→ fade), `destruct` (224 B).
- **Input is not in ConfigDialog but in `Configuration >> scriptMain:` (argc 1, 683 B)**, a K2_Script
  subclass. It snapshots `GameParam getConfig` (0x0002), creates ButtonGuides, `CONFIG enable`,
  then loops:
  - trig 32 (○): curY 5 → `setDefault` (0x0093–0x00a4); curY 1 → rumble test
    (`ControlPad actuator: 255, 1`, 30 frames); curY 3 → voice sample; curY 4 → SE.
  - trig 64 (×): restore the wallpaper preview, exit.
  - rapid 4096/16384 (up/down): `moveCursorU`/`D` + `changeInfoO` (button hints for curY 5 / 4 /
    3 or 1).
  - rapid 32768/8192 (left/right): `selectValueL`/`R`.
  - On exit (0x028d): if `temp0 == 0` (title) and `GameParam checkConfig: snapshot` is false →
    `ConfigSave new scriptMain`.
- `getConfig` (class side, 55 B) = `Array new: 5` of [actuator 20, music 21, voiceVol 23,
  wallPaper 16, messSpeed 19]. `checkConfig:` (62 B) compares them with `==` and ANDs the results.
  **autoSkip is not in the snapshot.** If toggles were added to ConfigDialog, both methods would
  need element [5] = classvar 18, or the title would never offer to save.
- Callers of `Configuration`: `MainMenu scriptMain` 0x0442 (`scriptMain: 0`, save prompt);
  `RoomMenu scriptMain` 0x01dd and `SelectMap scriptMain` 0x02a9/0x0515 (`scriptMain` → arg 1, no
  prompt; saved with the next slot save).

### 2.3 The Rumble Yes/None toggle, end to end

1. `initialize:` 0x0082–0x00e1: label `Sprite 121` and two value sprites (`144` "Yes", `145`
   "None") at the same spot, both alpha 0.
2. Open (`run` state 1, 0x0078–0x00a7): label to (-68,-64), both values to (80,-64).
3. `enable:` 0x0037: `self setPadAct: GameParam getActuator` → `setPadAct:t:` (73 B): if true,
   `padActSw[0] fade: 1` and `[1] fade: 0`, else the reverse (crossfade, 3 frames).
4. Left/right on curY 1 → `selectValueL/R` → `toglePadAct` (30 B):
   ```
   0002: GameParam getActuator  ; 000b: not ; 000e: self setPadAct: v ; 0015: GameParam setActuator: v
   ```
5. ○ on curY 1 → rumble test in `Configuration` (0x00ab–0x00da).
6. Exit → `checkConfig:` (actuator is snapshot element 0) → `ConfigSave` → `makeConfigData:` cfg[1].

### 2.4 Labels: textures vs text system

- **Unused label textures already in GRAPH0** (no new archive entries needed):
  - `sysgraph/menu_main4` (GRAPH0 entry 340, 112x32, "オプション" / currently "Options"). Sprite
    record 114 with n = 4. `MainMenu` const 91 uses `{114,0},{114,1},{114,5},{114,2},{114,3},{119,0}`,
    so n = 4 is never shown, but `GameMain >> loadSysTex0` 0x009d–0x00ba preloads 114 n 0..4, so it
    is in memory. Ideal for a main-menu "Easy Mode" item (also usable in RoomMenu).
  - `sysgraph/menu_set1` (entry 342, 144x32, "自動文字送り" / "Auto Advance"). Sprite record 120.
    No script pushes 120 as a Sprite id (searched every `Sprite` construction; ids are mostly
    literal, a computed id cannot be fully excluded). It is the label of the cut autoSkip option.
    Usable as an "Easy Mode" header or row label in the settings panel.
  - Everything else in `menu_set0..9` is used. Sprite ids 119 and 120 appear nowhere as literal
    `Sprite new:` ids except 119 in the menu tables.
  - New label textures for 4 rows would need new GRAPH0 entries plus sprite-table records (or `%1d`
    variants that do not exist yet). `apply_graph0.py` repacking new names is not verified. Avoid.
- **Text system (preferred, no textures):** `TextLine new: layer, x, y, pitch, clut, scaleIdx` (argc 6,
  scale table `{0.5,0.75,1,1.25,1.5}`), `TextLineC` (centred). API: `setText:`, `setAlpha:`,
  `fade:t:m:` (3), `move:y:m:t:` (4, same as Sprite), `fadeLight:t:m:` (**3 args; Sprite's is 5**),
  `restart`/`dormant`/`destruct`. Each character is one `FontChar` sprite. English layout already works
  through the patched `setText`/`xOf:` (D-015; `TextLine.setText1.asm`, `TextLineC.setText1.asm`,
  `xOf1`). Working example: `ConfirmDialog >> initialize` argc 7 0x01b1–0x01d4:
  ```
  mess put: ((TextLineC new: layer+1, x, y, pitch, 0, 1) setAlpha: 0f; setText: line)   ; shown later with fade: 1f, 1, t
  ```
  Other users are `DeckListItem`, `NameEntryList`, `ShioriListItem` and `StaffRoll`.
  **Blocker: English strings in patches.** `scfasm.Pool.parse` encodes `"…"` as cp932, but English
  must use the D-012 codes 0x8540–0x859F, which cp932 cannot express. Fix: in `scfasm.py`, add an
  `en:"…"` operand → `(5, en_text.encode_translation(s))`, and change `tokenize` so a quoted string
  with spaces or commas survives. Today `tokenize` replaces every `,` with a space and `\S+` splits
  `en:"Easy Mode"`. The text pipeline does not see patch-added constants, so these labels are
  maintained in the .asm.

### 2.5 What 4 more toggle rows in ConfigDialog would take (Design B, not recommended)

- Storage for the new objects: ivars 13 `arrowL` and 14 `arrowR` are free, for example one Array of
  4 label TextLines and one of 4 value TextLines. ConfigDialog's field list does not need to grow.
- Methods to replace (round trip with `scfasm.listing()`, then edit): `initialize:` (700 B: build
  rows, change `DialogBox new: 3, 16f, 12f` to a larger `sclH`, move every existing row's y),
  `run` (907 B: open/close moves for new objects and new y values for old ones; states 3/4 use
  const 53), `moveCursorD`/`U` (use 10 instead of `const53 length`), `enable:`/`disable:` (fadeLight
  with 3 args for TextLines, value refresh), `fade:t:m:`, `destruct`, `selectValueL/R` (curY 5..8 →
  toggle), `setDefault` (also clear the flags?). Plus `Configuration >> scriptMain:` and `changeInfoO`
  if Reset moves from index 5 to 9 (`push_int 5` at 0x0093 and changeInfoO 0x000c), and
  `GameParam class >> getConfig`/`checkConfig:` (element [5] = autoSkip). The row table const 53
  cannot be rewritten (patches only append constants, and scfasm has no array literal), so it needs a
  helper `rowY:` or a new array constant via a tool extension.
- Layout: 9 rows at 32 px + 48 px gap is about 304 px. That needs `sclH` ≈ 20 (half height 168) and
  every row moved up about 64 px. The box top then reaches about y -188, next to the ButtonGuides at
  (224,-182)/(208,-156) and the main-menu header. Tight; emulator check required.
- About 70 extra FontChar sprites stay allocated for the whole game (CONFIG never dies). The sprite
  pool limit is unknown.
- Estimate: about 2.5–3 KB of replaced or added bytecode in 12–15 methods, with the highest
  regression risk of all options, because it touches the threaded state machine of a shared panel.

---

## 3. Title main menu

Classes: `TitleLogo` (press start), then `MainMenu` (K2_Script; ivars 0 mcState, 1 cursor, 2 menu,
3 menuCom), which uses `CommandMenu` (generic vertical list).

- `MainMenu >> makeMenu` (argc 0, 169 B): `menuCom := Vector new: 6` (0x0014). Command ids are
  `put:` in order: 0 (0x001d), 1, 2, then 3 if `Album new checkAlbumAll > 0` (0x0035), 4 if
  `GameParam numOfClear > 0` (0x004b), then 5 (0x005e). Sprites come from const 91
  `{{114,0},{114,1},{114,5},{114,2},{114,3},{119,0}}` indexed by **command id** (0x0088):
  0 New Game (menu_main0), 1 Continue (main1), 2 Carry Over (main5), 3 Album (main2),
  4 Extras (main3), 5 Settings (menu_set0). The result is
  `CommandMenu new: table, -88f, cursor` (0x009b; `CommandMenu >> initialize` argc 3: x -220, pitch 32,
  `Sprite new: id, n, 10` per item, cursor Sprite 98). Seven items reach y = -88 + 6·32 = 104, which
  fits.
- `MainMenu >> scriptMain` (1432 B) is the input loop (0x00f1). On ○ (0x0101) it closes the two
  ButtonGuides (temp2/temp3), reads `temp6 := menuCom at: cursor` and branches: 0 New Game
  (0x0122), 1 LoadMenu (0x0216), 2 Succession (0x0297), 3 Album (0x0318), 4 Omake (0x03bd),
  5 Settings (0x042c–0x045d: SE 35, `menu disable`, `Configuration new scriptMain: 0`, wallpaper
  re-read, `menu enable`, sleep 3). All branches join at 0x0461, which reopens the guides. Cursor moves
  (0x04b3–0x0519) open or close the CONFIG preview only when the item is command 5.
- **Adding "Easy Mode" (command 6) is feasible:**
  - `makeMenu`: `menuCom put: 6` before `put: 5`. Table entry 6 is out of range of const 91, so build
    `{114,4}` at run time (`Array new: 2`, at_put 114, 4) or add an array-constant syntax to scfasm.
    About 169 → 210 B.
  - `scriptMain`: one more branch `temp6 == 6` copied from the Settings branch, but calling the new
    dialog (`Configuration new easyMode: 0`), then joining 0x0461. A full-method replacement made
    from the listing round trip; about 1432 → 1470 B.
  - `textures.toml`: `sysgraph/menu_main4` english "Options" → "Easy Mode" (112x32, same style as
    the other items).
- **Dialog to reuse:** no existing class is an interactive multi-row toggle list besides ConfigDialog.
  - `ConfirmDialog` (`new: layer, x, y, width|nil, text, mode`; mode 0 none, 1 ○, 2 ○/×; lines split
    on `／`, built from `DialogBox` + `TextLineC`) is a message box, good for "Easy mode changes
    saved" style notices but not for rows.
  - The building blocks to reuse are `DialogBox` (`new: color 1..4, sclW, sclH, layer`; `setPos:`,
    `setAlpha:`, `restart`, `fade:`, `move:`, `destruct`), `TextLine`/`TextLineC`, Sprite 98 (the
    cursor used by ConfigDialog and CommandMenu), and `ButtonGuide new: layer, x, y, button(0 ○,
    1 ×, 2 △, 3 □), textFrame`. The panel's input loop is modelled on `Configuration >> scriptMain:`.
  - The text-window choice (`SYS : {n, "・a／・b"}` → `Parson >> :` → `TextWindow select:`; MainMenu
    0x0191) also works on the title, but it is limited to the 3-row message window. It only works as a
    two-page fallback.
- Night `RoomMenu` (`scriptMain` 1315 B) uses `CommandMenu new: const12 {{117,0},{116,0},{116,1},{116,2},{119,0}}`
  (Save, Girls, Sleep, Topic Bag, Settings) and dispatches on **cursor position** (temp2). The same
  `{114,4}` "Easy Mode" item and the same dialog method could be appended as a 6th entry later. That
  needs a runtime-built table and a branch in the 1315-B method.

---

## 4. Recommendation (Design A)

**Storage:** an Integer bitmask in `GameParam` class variable 18 (`autoSkip`, system data cfg[0]).
Add `GameParam class >> easyFlags` / `easy:` / `setEasyFlags:` (§1.5).

| bit | cheat |
|---|---|
| 1 | no losses |
| 2 | fewer rejections |
| 4 | easier meetings |
| 8 | more conversation attempts |

The save, load, restart and carry-over code stays unchanged.

**Menu:** a new title main-menu item "Easy Mode" (texture `menu_main4`, relabelled) opens a modal
panel implemented as **one new method `Configuration >> easyMode:`** (argc 1: 0 = title, which
prompts to save; 1 = in game, which does not, mirroring `scriptMain:`). Configuration is a K2_Script,
so `sleep:` is available, and the method can later also be called from RoomMenu or SelectMap without
touching ConfigDialog. All objects are temps, so no ivars are needed.

Sketch of `easyMode:` (≈ 800–1100 B; temps: mode, box, title, labels[4], values[4], cursor, cur, flags0, guideO, guideX, i):
1. `flags0 := GameParam easyFlags`.
2. `box := (DialogBox new: 3, 18f, 10f, 14) setPos: 0f, -8f; setAlpha: 0f; restart`. Half extents
   are 152 x 88, so 4 rows plus a title fit at 32 px.
3. Title `TextLineC new: 15, 0f, -72f, 24, 0, 2` with `setText: en"Easy Mode"`. Labels
   `TextLine new: 15, -136f, y, 24, 0, 2` with en"No Losses", en"Fewer Rejections",
   en"Easier Meetings" and en"More Conversation Tries" (wording is the caller's choice; check the
   width against 304 px with `xOf:`). Values `TextLine` at x ≈ 96 with en"On"/en"Off". Every object
   gets `setAlpha: 0` and then `fade: 1f, 1, 9`.
4. Cursor `Sprite new: 98, 0, 16` at x -156 and the row's y. ButtonGuides: copy the ones of
   `Configuration` (`ButtonGuide new: 13, 208f, -156f, 1, 2` for ×/back, and a ○ guide).
5. Loop with `self sleep: 1`:
   - `ControlPad trig & 32` (○), or `rapid & 32768`/`8192` (left/right): flags ^= (1 << cur)
     (`{1,2,4,8} at: cur`), `GameParam setEasyFlags:`, `values[cur] setText: (On|Off)`,
     `Sound playSE: 12`.
   - `rapid & 4096`/`16384` (up/down): `cur := (cur ± 1 + 4) % 4`, cursor `setPos:`, SE 12.
   - `trig & 64` (×): SE 23, leave the loop.
6. Fade everything to 0 (`fade: 0f, 1, 6`), `sleep: 6`, `destruct` each object.
7. If `mode == 0` and `GameParam easyFlags ~~ flags0`, run `ConfigSave new scriptMain`. That reuses
   the existing "Settings changed. Save?" prompt; `makeConfigData:` copies cfg[0] = autoSkip.

### Patches and tool changes

| item | kind | size (rough) |
|---|---|---|
| `GameParam easyFlags` / `easy:` / `setEasyFlags:` | `; add:` table=methods2 | 25 / 12 / 7 B |
| `Configuration easyMode:` (+ optional `easyValue:` helper returning en"On"/en"Off") | `; add:` table=methods | 800–1100 B |
| `MainMenu makeMenu` | `; target:` 169 B | ≈ 210 B |
| `MainMenu scriptMain` | `; target:` 1432 B | ≈ 1470 B |
| `translation/textures.toml` | `menu_main4` english → "Easy Mode" | text only |
| `tools/reinsert/scfasm.py` | `en:"…"` constant + tokenizer that keeps quoted spaces and commas; optional `arr:{…}` | ~15 lines |
| `tools/qa/test_patches_jp.py` scenarios | oracles for the `add` methods (`easyFlags` on nil/false/true/int, toggling); lint for the rest | — |
| later, optional | RoomMenu 6th item (const-12 table at run time + branch) to reach the panel in game | ≈ +60 B in a 1315 B method |

### Risks and unknowns

- English constants need the scfasm extension. Without it, labels would have to be built from integer
  codes at run time.
- Layout and layering (layers 14–16 above the main menu at 10, CONFIG at 12–14, ButtonGuides 12–13)
  and the box size are unverified; an emulator screenshot is needed. Seven main-menu items is a
  computed fit only (CommandMenu is generic, 32 px pitch from -88).
- `TextLine available`/`restart` handling: copy the ConfirmDialog pattern (`setAlpha: 0`, `setText:`,
  then `fade:`). Labels are destroyed on exit, so the glyph sprites are only allocated while the panel
  is open.
- The system-data size margin is not measured (+3 bytes here). The fixed 10240-byte system block is
  inferred from the buffer sizes and native constants.
- `and`/`or` evaluate both sides; `Nil >> isKindOf:` throws. Keep guards as jumps.
- The flags are global (system data), not per save slot. Changing them in game (if wired later) is
  persisted only by the next slot save, the same as the existing settings.
- Reset to Default does not touch the flags (by design; change `setDefault` if wanted).
- The Japanese regression test (`test_patches_jp.py`) must still pass. The new main-menu item would
  also appear in a Japanese build with the English texture.

### Why not the alternatives

- ConfigDialog rows (§2.5) reach the panel from title, room and map. But they need 12–15 method
  replacements in a threaded, always-alive panel, a re-layout of every row, and a permanent glyph cost.
- One ConfigDialog row that opens a sub-panel still needs the panel to grow by one row (new y values in
  `initialize:`/`run`, `sclH`), plus input changes in `Configuration`. With Design A, the same
  `easyMode:` can be called from `Configuration >> scriptMain:` later (for example on □/△ with a
  ButtonGuide hint) if in-game access from Settings is wanted.
- The text-window choice is limited to 3 rows and looks like dialogue, not a settings screen.
