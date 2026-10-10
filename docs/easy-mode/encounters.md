> Research notes written before the Easy Mode patches (D-038, [../easy-mode.md](../easy-mode.md)). Placeholder sends such as `Cheat noLoss` became `GameParam easy: bit`; helper scripts and draft patches named below (`research/...`, `scratchpad/...`) were session scratch files and are not in the repository. Disassemble with `python3 tools/extract/scfdis.py build/work/script_orig/<Class>.scf`.

# KimiKiss: encounters, first meetings, Attack stock, and easy-mode patch points

Read-only research based on `build/work/script_orig/*.scf` and the `dis/*.dis` listings. Offsets are method-relative bytecode offsets, as `scfdis.py` prints them. `[unsure]` marks inferences.

Helper output used below: `research/cmp.py <Class> [regex] [i|c]` prints a compact listing and resolves class-side ivar names correctly. Draft patch listings are in `research/drafts/`. They assemble, but they have not been run.

## 0. Two traps in the existing listings

1. **Class-side ivar names in `dis/*.dis` are wrong.** In `methods` (class-side) bodies, `scfdis.py` resolves `push_ivar n` against the *instance* field table. The correct names come from "fields 2":
   - GameParam: 4 = eventTable, 5 = encountTable, 6 = available, 7 = curInstance, 8 = evList, 9 = tmpEvFlag, 10 = tmpDeai, 11 = evFlag, 12 = alFlag, 13 = clFlag.
   - Parson: 9 = list.
   - TopicPlayer: 6 = curDeck, 7 = deckPtr.

   For example, `GameParam class>>checkEncount` shows `push_ivar 5 ; toukou`, but slot 5 is really `encountTable`.
2. **`mwhere.py` misattributes class-side methods.** It only recognises `method ` lines, so a hit inside a `methods X` body is credited to the last instance method in the file. That is why "GameParam.clrEvent" and "Parson.setDeai" show up as callers.
   - Event priority is really handled by **`GameParam class>>checkEvent:`** together with `choiceEvent:` and `choiceGuideEvent:`.
   - Instance `clrEvent:` (argc 1) only resets a guide event's wait counter to 0.
   - `research/mw.py` is a fixed copy that labels class-side methods `class>>`.

Glyph-mangled selectors in GameMain decode as follows:
- `#�G���J�E���g�w�i` = `エンカウント背景`
- `#�G���J�E���g���u` = `エンカウントモブ`

GameParam forwards both to EncountTable `背景` and `モブ`. The persons table is `EncountTable 人物`, and clothing is `EncountTable 服装`.

Parson ids, from `K2_Script.setup`: 0 PLY, 1 YUM, 2 NAR, 3 MAO, 4 ASU, 5 ERI, 6 MIT, 7 NAN, 8 AKI, 9 TOM, 10 MEG. The heroines are `{1,2,3,4,5,6,7,10}`, and their favor index is `{nil,0,1,2,3,4,5,6,nil,nil,7}[id]`.

Places (`moveEria`, 0-based, from the debug strings in `checkEvent:`): 0 一年, 1 二年, 2 三年, 3 図書, 4 保健, 5 理科, 6 家庭, 7 音楽, 8 屋上, 9 体育, 10 食堂, 11 校庭, 12 花壇.

Time zones (`timeZone` 0..3) are the four map moves: 休み１, 休み２, 昼休み, 放課後. Event slots (`evList` index) are 0 登校時, 1 休み１, 2 休み２, 3 昼休み, 4 放課後, 5 放課後２, 6 下校時, 7 菜々, 8 寝る, 9 休日.

## 1. Day structure (`GameMain mainLoop` argc 0)

```
0006 roomManu                                   ; evening/home (see §3)
000b getDate % 7 == 0 -> date > 33 ? ending : holiday
002e toukou
0033 SelectMap new scriptMain -> temp0          ; player picks 4 places; returns 4 events
003d self kounai: temp0[0] ; Parson downTension ; SelectMap passage: temp0[1]
005b self kounai: temp0[1] ; ... kounai: temp0[2] ; ... kounai: temp0[3]
00a7 houkago ; 00ac gekou
```

That gives **4 moves per weekday**, and each move runs `kounai:` once. `Parson downTension` multiplies every girl's tension by 3/4 after each move. In `roomManu`, `Parson downInterest` halves tension, and interest drops by 1 unless it was raised that day.

### 1a. Map selection and events (`SelectMap scriptMain` argc 0, `GameParam class>>decEvent:`)

- `0045 GameParam checkGuideEvent -> temp1`. For each slot 1..4 and each place, `choiceGuideEvent:` returns one of three things:
  - an event row: a guide event, i.e. a story event with `e[16]==1`. All 106 of these are SEV_A/SEV_B at priority C.
  - `true`: some heroine's non-guide event with priority B, C or E could fire here.
  - `nil`.
- `EriaIcon setGuide:` draws what it got:
  - an event row: that girl's GirlIcon on the place;
  - `true`: the generic `GirlIcon 0`;
  - `nil`: nothing.
- `0206` stores `temp17[tz] := temp1[tz][place]` when the player confirms a place.
- `066e GameParam decEvent: temp17`. For each time zone, it runs `checkEvent: tz+1` at the chosen place and keeps that result if the map entry was not a guide event **or** the checked event has priority A. So priority A beats a guide event, and a guide event beats B..E. Non-arrays become `nil`. It also sets `tmpEvFlag[id]` and `tmpDeai[girl]` for the rest of the day.
- The resulting 4 entries are what `kounai:` receives as its argument.

`GameParam class>>checkEvent: slot` (argc 1) is the priority picker:

```
0059 evList[slot] (slots 1..4: [curInstance getMoveEria: slot-1])
009a self choiceEvent: list into: temp1           ; buckets A..E
00a3 A non-empty -> first A  ("警告　優先度Ａの候補が複数存在します")
00c6 B non-empty -> random B
00ec C non-empty -> random C
0112 D non-empty and (Integer rnd: 5)==0 -> random D        ; 1/5 chance
0143 E non-empty -> k := Integer rnd: E.len+1; k>0 -> E[k-1] ; len/(len+1) chance
```

`choiceEvent:into:` (class, argc 2) accepts an event row `e` only when all of these hold:
- `curInstance getEvent: e[0]` is not `true` (not done) and `tmpEvFlag[e[0]]` is not `true`.
- `e[16]==0` (not a guide event).
- The priority rule passes: `prio==0` OR (`prio==1` and the girl is **not** met) OR (`prio>=2` and the girl is met). "Met" means `getDeai ~~ false` or `tmpDeai[girl]==true`.
- `girl isMob == false`.
- `e[20+level]==1`, `e[18+story]==1`, `e[27+favorPos]==1`, `e[25] <= stage`, `e[26] <= favorCnt`.
- `GameParam checkEvFlag: e[17]` is true.

**EventTable `発生条件` row layout** (377 rows × 32 fields):

| Field | Meaning |
|---|---|
| 0 | id |
| 1 | girl |
| 2 | type (index into the `findEvent` list: 1 DEA, 2 SEV_A, …, 29 TEL, …) |
| 3 | sub |
| 4 | place (1-based; 0 = every place) |
| 5..14 | slot flags (登校時 … 休日) |
| 15 | priority 0..4 = Ａ..Ｅ |
| 16 | guide flag |
| 17 | flag condition (`checkEvFlag:`) |
| 18..19 | allowed story 0/1 |
| 20..24 | allowed level 0..4 |
| 25 | minimum stage |
| 26 | minimum favorCnt |
| 27..30 | allowed favorPos |
| 31 | debug title |

Event counts:
- A: 14 (JEV 8, SEV 3, JTM, JTG, FEV).
- **B: 33** (DEA 24, KAZ 7, TEL 2).
- C: 136.
- D: 14.
- E: 180.

Guide-event fairness: `GameParam initialize` sets `event[id] := 0` for every guide event. Each time `choiceGuideEvent:` sees a candidate, `addEvent:` increments its counter. It keeps the candidates with the highest counter, picks one at random, and the instance `clrEvent:` resets that one to 0. `setEvent:` (via `endEvent:`) marks the event done (`true`).

## 2. How a girl appears at a place (`GameMain kounai:` argc 1, 1248 bytes)

### 2a. A scheduled event comes first

```
0019 temp3 := event[17]; if 1874<=temp3<=1881 -> temp3 := (Parson getObj: {1..7,10}[temp3-1874]) isMob else false
0046 (Parson getObj: event[1]) isMob == false and temp3 == false ->
005d   "イベント発生：" ; execEvent: event[1] type: event[2] sub: event[3]; endEvent; addInterest: 2 ; return
```

If an event is attached, it runs and the move ends. Random encounters never replace or reorder events.

### 2b. First spot (random)

```
00a1 GameParam checkFirst -> temp4 (person id) ; temp5 := Parson getObj: temp4
00b7 temp10 := timeZone < 3 ? 1 : 2              ; day / evening BG variant
00ca temp11 := (エンカウント背景 at: place) at: 0 ; BG of the first spot
0125 temp4 > 0 and temp5 isEnable -> encounter, else 0261 "（これと言って誰もいないな…）"
```

`GameParam class>>checkFirst` / `checkSecond` (argc 0, 12 bytes each) are `^self checkEncount: 0` and `^self checkEncount: 1`. The roll happens in `class>>checkEncount:` (argc 1, 48 bytes):

```
000f encountTable 人物
0014 at: (curInstance getMoveEria * 2 + slot)     ; slot 0 = first spot, 1 = second spot
0020 at: curInstance getTimeZone
0026 at: (Integer rnd: 20)                         ; uniform 0..19
```

`EncountTable 人物` has 26 rows (13 places × 2 spots) × 4 time zones × 20 person ids. 0 means nobody. There is **no** dependency on interest, level, stage or furare. Only the table and `isEnable` matter.

`Parson isEnable` (instance, argc 0) is `getDeai ~~ false and isMob == false`:
- `deai` starts `false` (`Favor initialize`) and becomes `true` only through `setDeai`.
- `isMob` is `(getBad at: 1) ~~ nil`. `Favor addBad:` shifts `bad[0]` into `bad[1]`, so a **second** bad mark makes the girl a "mob": out of the game, never encountered again.
- Bad marks come from:
  - `GameParam class>>checkGekouDate`: two walk-home dates on one day, so one girl is rejected;
  - `class>>checkKissBad:`: a girl who sees you kiss someone.
- `WadaiReaction` plays no part in availability; it only enables topic reactions.

Encounter body for the first spot, 0x133..0x250:

```
0133 cloth := GameParam encountCloth: id with: 0        ; 服装 table: uniform / gym / swimsuit by rnd 20
015b temp7 := temp5 checkInterest                      ; mood, see below
0164 temp8 := execEvent: id type: 13 (MST) sub: level*10 + temp7*3 + cloth
0181 temp7==2 & temp8==1 -> addInterest -1 ; temp8==0 -> addInterest +1 ; temp8==2 -> end move (return)
01d0 temp8==0 and temp7 ~~ 1 -> matchingTalk: temp5 (conversation) ... checkKissBad ... return
0251 otherwise cutOut and fall through to the second spot
```

`Parson checkInterest` (instance, argc 0, 53 bytes) uses interest I in 0..9 (starts at 3):
- returns **2** ("FROM_G", she comes to you) if `I > rnd 20`, so P = I/20;
- otherwise returns **0** ("OK") if `I > rnd 10`;
- otherwise returns **1** ("NG": she brushes you off, and **no conversation is possible** because of `temp7 ~~ 1`).

At I=3 that is P(NG) ≈ 0.60, P(OK) ≈ 0.25, P(FROM_G) = 0.15.

Inside `*_MST scriptMain` (argc 1), sub%10 selects the scene: 0..2 OK, 3..5 NG, 6..8 FROM_G. The player's choice is in `ans` (0 = talk, 1 = no). At 0x294 (ERI_MST; all 8 are alike), if `TopicPlayer getRemainder <= 0`, `ans ~~ 1` and the scene is not NG, it runs `execEvent: 0 type: 13 sub: girl` (the PLY_MST "nothing to talk about" scene) and returns 2. Then kounai ends the move.

### 2c. Second spot

```
027e (背景 at: place) length < 2 -> fadeOut, return        ; 校庭 (11) has one BG -> no second spot
029d temp14 := first-spot id
02a1 GameParam checkSecond -> temp4
02b3 temp4 == temp14 -> temp4 := 0                          ; same girl again = nobody
02bf BG index temp15: place 9/10 -> rnd 2 + 1; place 1 -> YUM 1, ERI/MIT 2, ASU 3, else rnd 3 + 1; else 1
0387 same encounter body as the first spot (0x0395..0x048c), "セカンド場所エンカウント発生"
04a9 "（これと言って誰もいないな…）"
```

So a move has at most two encounter rolls. A conversation in the first spot ends the move. If the first spot has no conversation (nobody there, NG, or the player declines), the second spot is tried.

### 2d. Why "nobody here" happens (in order of importance)

1. **The roll names a girl you have not met** (`deai == false`). This dominates early in the game, because every row mixes several heroines.
2. The roll names a girl who is **out** (`isMob`: two bad marks).
3. The table entry is 0:

   | Place / spot | Time zone(s) | Zeros |
   |---|---|---|
   | 食堂 A and B | 休み１, 休み２ | 20/20 (always empty) |
   | 三年 B | 休み２, 放課後 | 18/20 |
   | 三年 B | 休み１, 昼休み | 2/20 |
   | 一年 A | 昼休み, 放課後 | 2/20 |
   | 一年 B | 休み２ | 2/20 |

4. Second spot only: the same girl as the first spot (0x2b3).

### 2e. What the player can do to raise the odds

- Go where the target girl has weight in `人物`. The table below lists cells with weight ≥ 5/20 per time zone, as place + spot (A = first, B = second).
- Meet the girl first: she cannot appear before that.
- Keep her from collecting two bad marks.
- Nothing else changes whether she *appears*. Interest only changes the mood roll (NG blocks the talk), and level only selects the MST scene.

| Girl | 休み１ | 休み２ | 昼休み | 放課後 |
|---|---|---|---|---|
| YUM | 屋上A 18, 図書A/保健A/家庭A 10 | 保健B 18, 理科A/音楽A 10 | 図書B/理科B 18, 二年B 10 | 6 in 図書AB, 屋上AB, 花壇AB |
| NAR | 一年B/家庭B 18, 一年A 10 | 音楽B 18, 一年A 10 | 一年B/家庭B 18, 保健A/音楽A 10 | 家庭AB 6 |
| MAO | 三年B/保健B 18, 音楽A 10 | 三年A 18, 保健A/花壇A 10 | 三年B/屋上B 18, 三年A/理科A 10 | 三年A 18 |
| ASU | 屋上B 18, 図書A 10 | 花壇B 18, 二年A/家庭A 10 | 二年A/花壇A 18, 保健A 10 | 体育B 5 only |
| ERI | 二年B/理科B 18, 二年A 10 | 理科B 18, 図書A/保健A 10 | 屋上A/花壇B 18, 理科A/音楽A 10 | 保健AB/理科AB 6 |
| MIT | 音楽B/花壇A 18, 二年A/理科A 10 | 図書B/家庭B 18, 家庭A/音楽A 10 | 図書A 18, 二年B 10 | 音楽AB/食堂AB 6 |
| NAN | 花壇B 18, 一年A/理科A/音楽A 10 | 一年B/屋上A 18, 一年A/図書A 10 | 保健B 18, 三年A 10 | 一年B 18 |
| MEG | 三年A/図書B 18, 保健A/家庭A 10 | 二年B/屋上B 18, 二年A/理科A/花壇A 10 | 音楽B 18 | 一年A 18 |

Rows 体育 and 校庭 (and 食堂 at 昼休み/放課後) are mixed rows that give every girl 2..6 of 20.

### 2f. Morning, after school, walk home, holiday

- **`toukou`** (argc 0, 684 bytes):
  - `checkEvent: 0` (登校時) has priority.
  - A follow-up (`getFollow`, from a rejected walk-home date) runs TFO with chance 1/2.
  - Otherwise two raw rolls happen, `Integer rnd: 20` at 0x158 (校門) and 0x226 (下駄箱). The rolled number is used **directly as a Parson id** and accepted only if `getDeai == true` and not a mob. The scene is `execEvent: id type: 30 (TEN) sub: level*10 + rnd 10`, plus 100 at the shoe lockers. Then `addInterest: 1`.
  - At most 8 of the 20 numbers are heroines, so each roll succeeds at most 40%, and only for girls already met.
- **`houkago`** (argc 0): only `checkEvent: 5` (放課後２). This is where the forced first meetings fire (below).
- **`gekou`** (argc 0):
  - A promised walk-home date (`checkGekouDate`) runs GKE and then GKD_A or GKD_B.
  - Otherwise `checkEvent: 6` (下校時).
  - If two dates are promised, one girl is picked with `rnd 2`; the other loses interest (-5 or -9) and may get a bad mark.
- **`holiday`** (argc 0, Sundays): a promised date (DAT_A/B) or `checkEvent: 9`.

## 3. First meeting (DEA)

Every `*_DEA scriptMain:` calls `setDeai` near its start. ERI_DEA does it at 0x000e, unconditionally; MEG_DEA does it conditionally at 0x00d4. `PLY_TFO scriptMain:` also sets **ASU**'s deai.

DEA events are ordinary, non-guide EventTable rows with priority **B**. That has three consequences:
- `choiceEvent:` accepts them only while the girl is unmet.
- In the map preview they show as the generic icon (`true` from `choiceGuideEvent:`).
- `decEvent:` picks them for that move unless an A event exists there. B is chosen deterministically over C/D/E, at random only among several B candidates.

They need level 0. Flag conditions come from `checkEvFlag:`:
- 1801–1806: always true.
- 1807–1810: `GameParam getClear: girl > 0` (a replay variant after clearing her).
- 1813–1818: `getDate > 7` (forced meeting after day 7).
- 1812 (MEG): all of YUM..MIT met and `getClearSum > 0`.
- 1891 (NAN): `getClearMain`.

| id | girl | sub | place | slots | flag | note |
|---|---|---|---|---|---|---|
| 201 | YUM | 1 | 図書 | 休み１,休み２,昼休み | 1801 | |
| 202 | YUM | 2 | 図書 | 昼休み,放課後 | 1807 | after YUM clear |
| 203 | YUM | 3 | any | 放課後２ | 1813 | forced, day > 7 |
| 204 | YUM | 4 | 二年 | 昼休み,放課後 | 1801 | |
| 401 | NAR | 1 | 家庭 | 昼休み,放課後 | 1802 | |
| 402 | NAR | 2 | 二年 | 昼休み | 1808 | after NAR clear |
| 403 | NAR | 3 | any | 放課後２ | 1814 | forced |
| 404 | NAR | 4 | 一年 | 休み１,休み２ | 1802 | |
| 601 | MAO | 1 | 食堂 | 昼休み | 1803 | |
| 602 | MAO | 2 | 三年 | 昼休み | 1809 | after MAO clear |
| 603 | MAO | 3 | any | 下校時 | 1815 | forced (gekou) |
| 604/605 | MAO | 4/5 | 花壇/屋上 | none | 1803 | dead rows (no slot flag) |
| 801 | ASU | 1 | 体育 | 休み１,休み２,昼休み | 1804 | |
| 802 | ASU | 2 | 校庭 | 休み１,休み２ | 1810 | after ASU clear |
| 803 | ASU | 3 | any | 放課後２ | 1816 | forced |
| 1001 | ERI | 1 | 花壇 | 放課後 | 1805 | |
| 1002 | ERI | 3 | any | 放課後２ | 1817 | forced |
| 1003 | ERI | 4 | 食堂 | 放課後 | 1805 | |
| 1201 | MIT | 1 | 音楽 | 休み１,放課後 | 1806 | |
| 1202 | MIT | 3 | any | 放課後２ | 1818 | forced |
| 1203 | MIT | 4 | 理科 | none | 1806 | dead row |
| 1601 | MEG | 1 | any | 登校時 | 1812 | replay only |
| 1401 | NAN | 1 | 二年 | 昼休み | 1891 | after main clear |

So the player meets a girl by moving to her DEA place in one of the listed slots; the map shows a generic icon there. If she is still unmet after day 7, the forced variant runs at 放課後２ (MAO: 下校時). Random encounters never trigger DEA.

## 4. Attack stock and other per-day limits

### 4a. Storage and refill

- `atkStock` and `atkMax` are GameParam **instance** ivars 16 and 15. They are not in the save body (`makeShioriBody` does not touch them).
- `GameParam initialize` sets `atkMax := 1; atkStock := atkMax`.
- `GameParam restoreSystemData:` (instance, at 0x006f) sets `atkMax := 1` if `GameParam getClearSum == 0`, else `atkMax := 2`; then `atkStock := atkMax`. So the stock is 1 per day on a first playthrough and **2 after any ending has been cleared**. It is applied when system data is restored (boot, and `K2_Script setup:` after an ending).
- Refill happens every evening in `GameMain roomManu` (argc 0) at `02d9 GameParam initAttack`. The instance `initAttack` (10 bytes) is `atkStock := atkMax`.
- Level-ups play no part.

### 4b. Use (`K2_Script matchingTalk:` argc 1)

```
013b temp17 := GameParam getAttack          ; snapshot at conversation start
0144 temp17 > 0 -> GekouIcon #1 shown; 015e temp17 > 1 -> GekouIcon #2 shown   (display caps at 2)
01e6 ControlPad data & 4096 (held; the direction the map uses for "up") and temp17 > 0 ->
022b   TopicPlayer attack (card shown) ; loop while held:
0247   ControlPad trig & 32 (confirm) -> GameParam useAttack -> true -> SE 47, temp27 := true
027d   TopicPlayer action, then resolve:
0289   feelings length > count (favor gauge NOT full) -> walk-home invitation:
         gekouOK: girl (already promised)  -> MAT sub level*10+7
         stage == 0 or tension < 100        -> MAT sub level*10+5, setFurare  ("下校デート誘い失敗")
         else                               -> MAT sub level*10+(furare?6:4), setGekouDate: girl ("成功")
0346   gauge full and tension >= 100 and kiss-allowed table -> kiss (type 8 KIS_A / 9 KIS_B),
         addKiss, level 3 -> setHoliday: girl (Sunday date)
0455   else -> "キス失敗" MAT sub level*10 + (stage==0?0:1) + (mob?2:0)
048f jump 0ee8                              ; an attack always ENDS the conversation
```

The instance `useAttack` (22 bytes) is `atkStock > 0 ifTrue: [atkStock := atkStock - 1. ^true]. ^false`.

So an "attack" is the one-shot move that ends a conversation with either a walk-home invitation or a kiss. The stock limits it to 1 (or 2) per day across all conversations.

The pad-bit-to-button mapping is `[unsure]`: 4096, 16384, 32768 and 8192 are the four directions in `SelectMap`, and 32 is confirm. Holding the 16384 direction plus confirm is "escape" (the player leaves).

### 4c. Other per-day limits

1. **4 moves per weekday**, fixed in `mainLoop`, with up to 2 encounter rolls each. A conversation (or an MST result of 2) ends the move.
2. **The topic deck** is the real "talk budget".
   - `roomManu 02d3 TopicPlayer setDeck` clones the player's deck (`WadaiParam getDeck`) every day and sets `deckPtr := 0`. A default deck has 16 cards (`WadaiTable defPlayerDeck`).
   - A conversation's hand draws up to 5 cards. `TopicPlayer destruct` puts unplayed cards back (deckPtr-1), so only **played** cards are used up.
   - When `TopicPlayer class>>getRemainder` (non-zero cards from deckPtr on) is 0, every `*_MST` returns 2 ("no topics"), which means no conversation for the rest of the day.
   - In `matchingTalk` at 0x0094..0x00ad, `TopicPlayer new == nil` causes `setDeck` and a retry. `[unsure]` whether `new` can return nil in this VM.
3. Tension: ×3/4 after each move and ×1/2 nightly. Interest: -1 nightly unless raised that day.

## 5. Easy-mode patch proposals

The flag sends `Cheat easyMeet` / `Cheat moreTalks` are placeholders, as requested. There is no `Cheat` class. A real implementation needs either a new SCF member, or added class-side methods on an existing class such as `GameParam easyMeet` (`; add: … table=methods2`) plus storage for the flag.

Storage is the open question, because the tools cannot add class variables. A workable route is an extra entry in the system-data array: `makeSystemData` builds 13 entries, and `restoreSystemData:` already tolerates arrays of any length by `length >=` checks. A `ConfigDialog` toggle would also be needed. `[design, not verified]`

The drafts in `research/drafts/` are complete `.asm` files with `; target:` headers and correct `original-sha1` values. All of them assemble with `scfasm.assemble`. Sizes are measured.

### 5a. Easier meetings (main patch): replace `GameParam class>>checkFirst` and `class>>checkSecond`

| Method | table | argc | original | new | sha1 |
|---|---|---|---|---|---|
| checkFirst | methods2 | 0 | 12 B | 75 B | 3c44276696e38ba599d93febbe7fb62444e05867 |
| checkSecond | methods2 | 0 | 12 B | 75 B | be2185d9cc9246987ab9444a9b84bd32374115eb |

Change: roll as before. If `Cheat easyMeet`, re-roll up to 8 more times while the result is 0 or `(Parson isEnable: id)` is false. Without the flag the behaviour is identical (one roll).

```
push_nils 2
push_const class:GameParam / push_int 0 / send 1 #checkEncount / store_temp 0
push_const class:Cheat / send 0 #easyMeet / jump_if_false done
push_int 0 / store_temp 1
loop: push_temp 1 / push_int 8 / op < / jump_if_false done
  push_temp 0 / push_int 0 / op > / jump_if_false retry
  push_const class:Parson / push_temp 0 / send 1 #isEnable / jump_if_false retry   ; nil also counts as false
  jump done
retry: GameParam checkEncount: 0 -> temp0 ; temp1 += 1 ; jump loop
done: push_temp 0 / return_top
```

`checkSecond` is the same with `push_int 1`.

Effect: "nobody here" happens only when no available girl is in that row. For a row with 50% weight for the only met girl, the chance rises from 50% to about 99.8%. The relative weights between available girls stay as the table has them, so girls keep showing up only where the designers placed them.

Callers: only `GameMain kounai:` (0x00a4 and 0x02a4). `checkEncount:` itself is **not** changed, because `checkKissBad:` (0x00a2) also rolls it to pick a kiss witness. Patching `checkEncount:` would raise the chance of a kiss-bad witness and of bad marks.

Story safety:
- Events are resolved before the random path (§2a, and `decEvent:` on the map), so this path never runs when an event is attached.
- `isEnable` still needs `deai`, so a girl never appears before her DEA.
- Priorities and guide counters are untouched.

Side effects:
- More MST scenes mean more +1/-1 interest swings, faster progress, and more kisses, each with the original witness chance. The day's 16 topic cards run out sooner.
- `Integer rnd` is called more often, so the RNG sequence shifts. This is harmless.

Known gap: the second spot still yields "nobody" when it re-rolls the first-spot girl (kounai 0x2b3). Fixing that means changing `kounai:` itself:
1. Add `GameParam class>>checkSecondNot: firstId`, which re-rolls also while `id == firstId`.
2. Replace `02a1 GameParam checkSecond` with `push_temp 14; send 1 #checkSecondNot`.

That needs the whole 1248-byte `kounai:` as a round-trip listing (`scfdis` output with `.s/.l/.w` forms) with about 3 lines changed (sha1 4229e6b13d26d8605f24b25cebc5ef811f9b46ed). It is optional.

### 5b. Easier meetings (optional add-on): `Parson checkInterest` (instance, methods, argc 0)

- Original 53 B, new 64 B, sha1 36d0a8ddff9d4f6de71fb80ad2936e29022125de.
- Change: after the `> rnd 20` test (which returns 2), `Cheat easyMeet` returns 0 instead of rolling the NG/OK split. With the flag on, an encounter is never NG, so it always allows a conversation unless the player declines or has no cards.
- Only caller: `kounai:` (0x015e, 0x03c0).
- Risk: NG scenes (MST sub 3..5) are never seen with the flag on. The interest -1 at 0x0181 still happens through the FROM_G-declined path.
- This is a stronger difficulty change than 5a; offer it as a separate sub-option if wanted.

### 5c. More conversation attempts (Attack): `GameParam useAttack` (instance, methods, argc 0)

- Original 22 B, new 32 B, sha1 6d2326a870a1e324f4dacd4b20c76a16c0b775a4.
- Change: the prefix `push_const class:Cheat; send 0 #moreTalks; jump_if_false orig; push_true; return_top`. With the flag on, an attack succeeds without using up stock.
- Only caller: `K2_Script matchingTalk:` 0x0257, through `GameParam class>>useAttack`.
- Because `atkStock` never drops, the `getAttack > 0` snapshot at 0x013b stays true, so every conversation can attack.
- Limits and risks:
  - If the flag is switched on after the day's stock is already 0, attacks unlock only after the nightly `initAttack`. Patching instance `getAttack` too (`moreTalks` → `^atkStock max: 1`) closes that gap.
  - More attempts mean more failed invitations (`setFurare`) and, with a full gauge, more kisses and therefore more witness rolls. That is the player's choice.
- Alternative: instance `initAttack` (10 B, sha1 213f968b1d2b03fcf75557b9a2a5ae6e5b8de206) could set `atkStock := atkMax + 2` when the flag is on. The display shows at most 2 icons, though.

### 5d. More conversation attempts (topics): `TopicPlayer class>>getRemainder` (methods2, argc 0)

- Original 65 B, new 100 B, sha1 b18ba87235518b00ba9964efcb34741ac2be3506.
- Change: the counting loop is unchanged. At the end, if the count is 0, `deckPtr > 0` and `Cheat moreTalks`, it runs `self setDeck` and returns `self getRemainder`. After `setDeck`, deckPtr is 0, which stops further recursion even for an all-zero deck.
- Callers: only the 8 `*_MST scriptMain:` methods.
- Effect: the day's 16-card budget no longer blocks conversations; the deck is re-dealt once it is empty. It is never re-dealt while cards remain, so the same 5 cards do not repeat and the "同じ話ばかり" (same topic) reaction does not trigger.
- Risk: low. `roomManu` still re-deals every morning.

### Not recommended

- Editing `EncountTable` data: it cannot be switched at runtime and it moves girls.
- Changing the 4-move day: the structure is spread over `mainLoop`, `SelectMap` and the 4-column tables.
- Patching `checkEncount:`: it affects kiss witnesses (above).
- Touching `checkEvent:` / `choiceEvent:` / `decEvent:`: these control story priorities.
- Patching `toukou`: possible (replace the two `Integer rnd: 20` rolls at 0x158/0x226), but it is a 684-byte method and gives little benefit.
