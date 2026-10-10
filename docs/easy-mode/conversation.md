> Research notes written before the Easy Mode patches (D-038, [../easy-mode.md](../easy-mode.md)). Placeholder sends such as `Cheat noLoss` became `GameParam easy: bit`; helper scripts and draft patches named below (`research/...`, `scratchpad/...`) were session scratch files and are not in the repository. Disassemble with `python3 tools/extract/scfdis.py build/work/script_orig/<Class>.scf`.

# KimiKiss: relationship losses, conversation outcomes, note and route logic, easy-mode patch points

Sources: the original scripts in `build/work/script_orig/*.scf`, read through the disassemblies in `scratchpad/dis/*.dis`. All offsets are bytecode offsets inside the named method. "class>>" marks a class-side method (table `methods2`). The `mwhere.py` helper credits class-side methods to the last instance method in the file (for example `Parson.setDeai` or `GameParam.clrEvent`). `research/mw2.py` fixes this and was used for the caller lists below.

Integer `rnd: n` is assumed to return 0..n-1. This was not checked in the VM primitive.

## 0. Data model recap (Favor / Parson)

| ivar | meaning | range / writers |
|---|---|---|
| interest (11) | interest; drives the encounter roll | 0..9, init 3; `addInterest:` clamps |
| fInter (12) | "interest was raised since last night" | set by `addInterest:` with v>0, cleared by `downInterest` |
| tension (17) | mood; only used inside conversations | 1..128 (`setTension:` clamps); init 0 |
| panic (18) | ドキドキ (flustered) level | 0..4 (`addPanic:` clamps) |
| feelings (9), countO (4), countH (5) | notes of the current level; 0 = plain note (♪, countO), 1 = heart (●, countH) | reset at every level-up (`initFeel`) |
| len (3) | cumulative note capacity per stage: len[0]=g0, len[1]=g0+g1, len[2]=g0+g1+g2 | from `CharParam 感情ゲージの幅` = level 0 {5,0,0}; levels 1,2,4 {4,4,3}; level 3 {4,4,3,6} |
| stage (7) | 0..2 within a level; raised by story events (`stageUpReq` in *_SEV_A/B) | reset to 0 by `initFeel` |
| level (1) | 0..4; `levelUp` needs `kiss[level] ~= 0` (and at level 3 also `date == 1`) | `GameMain.roomManu` calls `levelUp` every night |
| story (10) | 0 = route A (love), 1 = route B (friendship) | set once, see §3 |
| pos (2) | graph position 0..3 | `setPos` at every level-up, see §3 |
| bad (6) | Array(2) of "jealousy" marks (who she saw you with) | `addBad:`; 2 marks = she drops out (§1.8) |
| furare (14) | "turned down your walk-home invite" | only changes which event plays (§2.4) |
| date (16) | holiday-date state: nil none, 0 promised, 1 done, 6/7 missed or cancelled, 2/3 after the phone call | §1.9 |
| gekou (13), kiss (15) | walk-home count and kiss count per level | |

Feel limit (`Favor.getFeelLimit`): `len[stage]`. At level 3 the limit is also capped at 6 until the first walk-home of that level (`checkFeelBlock`). `Parson.addGekou` removes the cap through `delFeelBlock`. Notes beyond the limit are not stored (`Favor.addFeel` 0x0010: `count < getFeelLimit`), and `FavorGauge.run` shows them with `upNG`.

## 1. Every place where the player loses progress

### 1.1 Conversation (K2_Script>>matchingTalk: argc=1, 4055 bytes): per-turn effects

Each reaction sets five temps that are applied after the turn:

| temp | debug label (0x08e1 print) | applied at |
|---|---|---|
| t18 | テンション (tension delta) | 0x0c4a `TensionGauge addTension: t18` → `Favor addTension:` |
| t19 | ドキドキ (panic delta) | 0x0c40 `t19 := TensionGauge addPanic: t19` (returns panicLv >= 4) |
| t20 | 好感度Down (notes lost) | 0x095e–0x09ac: puts t20 × `-1` into the feel queue t24 |
| t22 | 好感度Up♪ (plain notes) | 0x09ad: puts t22 × `0` |
| t21 | 好感度Up● (hearts) | 0x09fd: puts t21 × `1` |

The queue t24 is replayed at 0x0c57–0x0d14 into `FavorGauge addFeel:` (temp13). `FavorGauge.run`, state 3 (0x01a8), turns each value v >= 0 into `favor addFeel: v` and each v < 0 into `favor downFeel` (0x022e). `Favor.downFeel` removes the last note and decrements countO or countH. The -1 entries come first in the queue, so the loss always takes the most recent note (heart or plain), and the new notes are added after it. SE 46 plays for a -1.

Outcomes per turn (player plays topic genre t35, topic number t34; `TopicTarget hitCheck:` looks for t35 in her hand of up to 5 hidden genres; genre 9 always hits slot 0, 0x05f7–0x061d):

| outcome | condition (offset) | t18 tension | t19 panic | t20 notes lost | notes won |
|---|---|---|---|---|---|
| 退屈な反応 (bored) | miss, and `MatchHistory checkLose3` (0x0685): the two previous turns also missed and the turn before them hit (or this is turn 3) | -12 | -1 | **1** | 0 |
| 興味はある反応 | miss, genre is in her whole deck (`TopicTarget hitDeck:` 0x06c8) | -8 | 0 | 0 | 0 |
| 興味もない反応 (not interested) | miss, genre not in her deck (0x0706) | -12 | -1 | 0 | 0 |
| no reaction 「・・・・・・」 | hit, but `WadaiReaction class>>choice:` returns nil (0x0749) | 0 | 0 | 0 | 0 |
| あせり反応 (flustered) | hit, `TensionGauge getTension < reaction[17]` (0x078b) | reaction[21] | reaction[18] | reaction[25] | 0 |
| 同じ話ばかり反応 (same topic again) | hit, `MatchHistory checkTopic3: t34` (same topic number as the two previous turns) and genre ≠ 9 (0x07d3) | **-48** | -1 | **1** | 0 |
| 通常リアクション (normal) | otherwise (0x0811) | reaction[20] | reaction[19] | reaction[24] | reaction[22] ♪, reaction[23] ● |
| ３連続ヒット (combo) | queue t23 of clean positive turns reaches length 3 (0x0a88) | +32 or +16 | | | +2 or +1 of the majority kind |
| ロスタイム (loss time) | t23 length 5 (0x0a4d) | +32 | | | |

The reaction record (`CharParam class>>reactionTable`, per character × 43 topics, 26 fields) is read by `WadaiReaction class>>choice:` (methods2, 511 bytes). Its fields are: [0] id, [1+level] allowed at level, [6] scene code, [7+timezone], [11]/[12] place, [13]/[14] `checkRaFlag:` conditions (event flags, clothes, route 1803/1804, crowd 1806/1807 ...), [15] re-enable class, [16] priority bucket 0..3 (choice picks randomly in the highest non-empty bucket), [17] minimum tension, [18] panic if flustered, [19] panic, [20] tension, [21] tension if flustered, [22] ♪, [23] ●, [24] notes lost, [25] notes lost if flustered. Field [15] meanings: 0 = always available, 1 = disabled after use and re-enabled at the end of the talk (0x0f72), 2 = re-enabled nightly (roomManu), 3 = re-enabled at level-up, 4 = never re-enabled.

Statistics over all 2567 records (`research/rt.py`):
- **399 (15.5 %) are "bad" reactions on a hit**: [24]=1, tension mostly -16 or -32 (up to -64), 0 notes won. Per character: 59/354, 64/422, 83/449, 63/447, 52/384, 42/402, 13/56, 23/53.
- 231 records have a tension requirement ([17] = 32: 100, 64: 128, 96: 3). When the requirement is missed, 177 lose 1 note, 43 lose 2 notes, the tension change is -16/-32/-48, and the panic gain is 1–3.
- Normal tension values: +48 in 1265 records, +56 in 226, +32 in 302.

### 1.2 Conversation: end-of-talk tension settlement (also after an attack)

```
0ee8 ... 0eef: 22 02 push_temp 2 (favor) / 22 19 push_temp 25 / 24 06 push_int 6 / 11 op - / 24 0c push_int 12 / 12 op * / 32 01 da 00 send 1 #addTension
```

t25 is the running score `t25 + t21 + t22 - t20` (0x0be5). Every conversation therefore ends with **tension += (score − 6) × 12**: a talk with no hits costs −72, a talk with 3 single-note hits costs −36, and the result is positive only from a score of 7. This settlement is the main "failed conversation" cost. Interest is **never** changed by matchingTalk.

### 1.3 Ending the conversation

Checked in this order after each turn (0x0d4f …):
1. **どきどき別れ** (0x0d4f): `TensionGauge addPanic:` returned true, i.e. panic ≥ 4. Event MED 25. Panic rises only through reactions with [18]/[19] > 0 (intimate topics, flustered reactions). It decays by −1 per time slot (`Parson downTension`) and −2 per night (`downInterest`).
2. **つまらない別れ** (she gets bored) (0x0d68): `MatchHistory checkLose4`, i.e. the last 4 turns all missed (`hitPos[t-1..t-4] == nil`, tCount ≥ 4). Event MED 20.
3. **時間切れ別れ 高/低** (0x0d86): `MatchHistory addTopic:with:` returned `tCount >= maxTurn(4)`, i.e. this was the 5th topic. Score t25 ≥ 4 gives 高 (event 35+x), otherwise 低 (30+x); x = 0 before timezone 3, 1 after. Also when her hand is empty (`TopicTarget isEmpty`, 0x0dd3).
4. **主人公から別れ 高/低** (0x0e25): the player's hand is empty, or the player chose to leave (pad 0x4000 then confirm, 0x04ec–0x058b). Threshold t25 ≥ 4. Events 40 / 45.

None of these endings has a cost beyond §1.2. The cost of an early end is the lost turns, so a lower score and a larger settlement penalty.

### 1.4 Attack (walk-home invitation / kiss), 0x01f5–0x048f

Pad 0x1000 (attack) with `GameParam useAttack` (stock `atkMax` = 1 per day, 2 after a clear; refilled by `initAttack` every morning):

```
0289: favor getFeelings length > favor getCount      ; level gauge not full -> invitation, full -> kiss
029e: GameParam gekouOK: cnum                         -> 下校デート誘い確認 (already arranged), event MAT 10*L+7
02c4: (p getStage == 0) | (TensionGauge getTension < 100)   ; 0x02cc identical / 0x02d6 op < / 0x02d7 0d OR
      -> 下校デート誘い失敗: event MAT 10*L+5, p setFurare (02f6)
02fe: else 下校デート誘い成功: event 10*L+4 (10*L+6 if furare already set), GameParam setGekouDate: cnum
0346: kiss: (TensionGauge getTension >= 100) & (t7 == 1)
      t7 = const119[char][level*2+story-1][cloth*2+crowd] (location/clothes/crowd table)
      -> キス成功: addKiss, KIS_A/KIS_B (story) event, setHoliday at level 3
0455: else キス失敗: event MAT 10*L + (cloth≠0) + 2*(crowd≠0)
```

The earlier note "fail when stage==0 and tension<100" is wrong: the condition is an **OR**. Stage 0 always fails, and stage ≥ 1 also needs tension ≥ 100. Both "tension" reads use the conversation's `TensionGauge` copy (temp14), not Favor.

Cost of a failure: the day's attack is used up, the talk ends at once (score so far, often 0, so −72 tension through §1.2), and on an invitation failure `furare := true`. `furare` is read only at 0x031a, to pick the "re-invitation" event variant, and is cleared at level-up. A kiss failure changes no stats beyond that.

### 1.5 Encounter refusal (not part of matchingTalk): Parson>>checkInterest argc=0

```
0009: r := Integer rnd: 20.  interest > r  -> ^2   (she comes to you: MST *_FROM_G)
001d: r := Integer rnd: 10.  interest > r  -> ^0   (OK: she accepts)
0031: ^1                                           (NG: she refuses, no conversation)
```

Used by `GameMain>>kounai:` at 0x015e and 0x03c0. The event `execEvent: cnum ctg: 13 (MST) code: level*10 + roll*3 + cloth` returns the player's answer. kounai then does:
- 0x0181: roll==2 and answer==1 ("ごめん、今ダメなんだ", decline her) → **addInterest: -1** (also −24 tension through Favor.addInterest).
- 0x019a: answer==0 → addInterest: +1 (+8 tension).
- 0x01d0: matchingTalk only if answer==0 and roll≠1.

| interest | she approaches | OK | refuses |
|---|---|---|---|
| 0 | 0 % | 0 % | 100 % |
| 3 (start) | 15 % | 26 % | 60 % |
| 5 | 25 % | 38 % | 38 % |
| 9 | 45 % | 50 % | 6 % |

### 1.6 Interest losses (every writer)

| where | value | trigger | how often |
|---|---|---|---|
| Favor>>downInterest 0x0015, from Parson class>>downInterest ← GameMain>>roomManu 0x011e | −1 (if `fInter` false and interest > 0) | every night, for every girl not given a positive addInterest since the previous night | daily |
| GameMain>>kounai 0x0193 / 0x03f5 | −1 | declining her when she approaches you | player choice |
| GameParam class>>checkGekouDate 0x0120 | −5 | two girls accepted a walk-home the same day; the one left behind with result 4 | rare |
| GameParam class>>checkGekouDate 0x014e | −9 (and addBad, delHoliday) | same, results 2/3/5; chance `rnd(10) < 4+level` gives 2/5, else 3/4 | rare |
| GameParam class>>checkKissBad 0x014e | −9 (and addBad, delHoliday) | a girl of level ≥ 2 who "encounters" the scene sees you kiss someone (called from kounai 0x01f2/0x042e after a successful kiss) | per kiss |

Favor>>addInterest with v < 0 also adds **24·v** tension (0x001a), and `addInterest:` with v > 0 adds 8·v tension and sets fInter. No event script calls addInterest, addTension, downInterest or addBad.

### 1.7 Tension losses (every writer)

- Per-turn reaction deltas (§1.1) and the end-of-talk settlement (§1.2); both are failure-driven.
- `Parson>>downTension` (tension × 3/4, panic −1), via the class side, after **each of the 4 school time slots** (GameMain>>mainLoop 0x0049/0x0067/0x0085/0x00a3).
- `Favor>>downInterest` (tension / 2, panic −2) every night.
- addInterest with a negative value (−24 per point, §1.6).

### 1.8 addBad, the jealousy marks

`Favor>>addBad: x` shifts bad[0] to bad[1] and stores x in bad[0]. x = 8 + the index of the girl you were seen with (checkGekouDate 0x016e; checkKissBad 0x00de uses the index without +8). `Parson>>addBad:` at 0x0019: if bad[1] ~= nil, `GameParam setMob: cnum` (a counter only).

**Effect:** `Parson>>isMob` = `bad[1] notNil`, and `Parson>>isEnable` = `deai & isMob not`. After the **second mark the girl drops out**: no encounters, events, story or ending (kounai 0x003b/0x0109, choiceEvent 0x0083, ALL_KOK/PLY_KOK_A *Mob, badTel). The marks are never cleared, so this is the most severe loss in the game. getBad is also read by FavorGraph (display), RoomMenu.nanaMenu and `GameParam class>>checkEvFlag` (flag 1843 needs nobody to be mob).

### 1.9 Notes removed outside conversations

`Parson addFeel: -1` (event choices; SE 46, then `FavorGauge downFeel`) at 17 sites: ASU_FEV10 0x0238; ERI_FEV_09 0x02d8, 0x033e; ERI_GKD_A31 0x04e9; MAO_FEV09 0x0305; MEG_FEV_01 0x026a; MEG_SEV_A SEV_A_005 0x02c9, SEV_A_002 0x02e8, 0x04d2; MIT_GKD_A21 0x04f5, MIT_GKD_A11 0x02b0; MIT_GKD_B11 0x0336; NAR_FEV19 0x05ee; YUM_GKD_B GKD_B_31 0x0577; YUM_SEV_A SEVA05 0x03bc, 0x04fa, 0x06e2. Notes are also wiped by `initFeel` at each level-up, which is normal progression.

### 1.10 Dates missed

Kissing at level 3 calls `addKiss` → `setDate` (date := 0, promised) and `GameParam setHoliday:`. On the holiday (GameMain>>holiday 0x0059–0x006c) she gets addInterest 3 and `setDateEnd` (date := 1), and every other girl with date==0 gets `setDateBadA` (date := 6, stood up). `GameParam>>delHoliday:` (from the jealousy cases above) sets `setDateBadB` (date := 7, cancelled). `GameMain>>badTel` plays the phone event (TEL) and `clrDateBad` (6 → 2 すっぽかし, 7 → 3 断られ). `Favor>>levelUp` 0x001b refuses level 3 → 4 unless date == 1. To recover you have to kiss her again at level 3 (re-invite events at matchingTalk 0x036b: +18 for date 3, +12 for date 2). The cost is time, not stats.

## 2. Why conversations end badly: decision logic in one place

1. **She refuses to talk**: checkInterest, §1.5 (pure interest roll).
2. **Bad reactions**: §1.1. A miss costs −8 or −12 tension. The 3rd consecutive miss is 退屈 (−12 tension, −1 note). A hit can still be あせり if gauge tension < reaction[17], 同じ話ばかり on a 3rd identical topic (−48, −1 note), or one of the 15.5 % "bad" normal reactions (table-driven: the record is chosen at random within the highest priority bucket among records matching level, timezone, place and flags).
3. **つまらない別れ**: 4 consecutive misses (checkLose4). **時間切れ別れ 低**: 5 topics played (maxTurn 4 → 5 turns) or her hand empty, with score < 4. **どきどき別れ**: panic reaches 4.
4. **Walk-home invitation failure**: stage == 0 OR gauge tension < 100 → setFurare (§1.4).
5. **Kiss failure**: gauge tension < 100, or the location/clothes/crowd table says no (§1.4).
6. All of these pay the end settlement (score − 6) × 12.

## 3. Notes, routes, and what endings read

- Which notes a turn gives: reaction fields [22] (♪ → `addFeel: 0`, countO) and [23] (● → `addFeel: 1`, countH), plus the combo bonus. A combo of 3 clean ♪ turns gives +2 ♪, of 3 ● turns +2 ●, otherwise +1 of the majority. Notes past `getFeelLimit` are discarded.
- **Route (story)** is decided **once**, by `Parson>>levelUp` 0x0018–0x002e: when `favor levelUp` returns 1 (level 0 → 1) and 0 < cnum < 7, `Favor>>setStory` sets story := 1 (route B, friendship) iff **countH < countO** of the level-0 gauge (5 notes). Ties and heart majorities stay story 0 (route A, love). NAN (7) and MEG (10) are always A. Removing a note through downFeel can flip this.
- **pos** (`Favor>>setPos`, every level-up, before `initFeel`): at level 1, H<O gives 3 if 2H<O else 2; H>2O gives 0; otherwise 1. Later levels: 0→2 if H<O; 1→3 if H<O else 0; 2→0 if H>O else 3; 3→1 if H>O. pos is read by `GameParam class>>choiceEvent` (record field [27+pos]) and choiceGuideEvent, so the heart/plain balance at each level-up selects which free and guide events can trigger. It is also shown in FavorGraph and DeckEdit.
- Event eligibility (`GameParam class>>choiceEvent`): fields [20+level], [18+story], [27+pos], [25] ≤ stage, [26] ≤ note count (`getFavorCnt` = countO+countH), not mob.
- Level gating: kiss needs a full level gauge (count == len[2]) and tension ≥ 100. Walk-home invitations need stage ≥ 1. Stages advance only by story events (SEV stageUpReq).
- **Endings** (`PLY_KOK_A>>KOK_HANTEI`): a girl qualifies when **level == 4 and getKiss (kiss[4]) > 0**, and **getStory** picks the A or B ending. `Ending>>preLoad` also branches on getStory. Interest, tension, countH/countO and stage are **not** read by the ending checks; they only gate the path. Readers by value:
  - getStory: matchingTalk (kiss table, KIS_A/B), GameMain gekou (GKD_A/B) and holiday (DAT_A/B), *_MAT, *_MW1_A, *_KIS ALB_FLAG, WadaiReaction checkRaFlag (1803/1804), choiceEvent, ALL_FEV/ALL_GKE FLAG_GET, Ending, PLY_KOK_A, Parson getClear.
  - getStage: matchingTalk 0x02c4, FavorGauge, Parson setDeck (her topic deck is TopicDeckT[char][level][stage]), choiceEvent, HintBar, ASU_FEV20, ASU_MW1_A.
  - getCountH/getCountO: only FavorGraph.setup (display); internally setStory/setPos.
  - getInterest: only Parson checkInterest.
  - getTension: only matchingTalk via TensionGauge (+ the decay methods).

## 4. Easy-mode patch points

Placeholders: `Cheat noLoss`, `Cheat fewerRejections` (class-side booleans; the class must exist, or the send must be renamed to wherever the flag ends up). Each patch adds two constants (class, selector) to its class pool. Sketches that assemble with `tools/reinsert/scfasm.py` against the original pools are in `research/asm/` (verified in memory only; nothing was written to the repo).

### 4a. "No losses" (removes decreases only; neither route is forced)

| # | method (table) | original | change | new size | other callers / risk |
|---|---|---|---|---|---|
| A1 | `Favor addTension argc=1` (methods) | 16 B, sha1 69463fbb06add445050aa805b6c802ae9bec7874 | if arg < 0 and `Cheat noLoss` → `^tension` unchanged | 35 B | Covers the end settlement (§1.2) and the −24·v tension of negative addInterest. Callers: TensionGauge.addTension, matchingTalk 0x0efa, Favor.addInterest (self). The decay paths use setTension directly and are not affected. |
| A2 | `TensionGauge addTension argc=1` (methods) | 22 B, sha1 207c3fe90c83d25daedf483b049557f39768de73 | if arg < 0 and noLoss → `^self` (no favor change, no gauge animation) | 39 B | Only caller is matchingTalk 0x0c4a. Needed as well as A1 because the gauge keeps its own `tension` classvar, which the walk-home, kiss and あせり checks read. |
| A3 | `Favor downFeel argc=0` (methods) | 69 B, sha1 80f7ea5e1a48b7e4c9737e7e04617a4e0f74584b | prefix `noLoss ifTrue: [^-1]`; −1 makes FavorGauge.run skip the icon (`0 <= idx` test at 0x0235) | 80 B | Only caller is FavorGauge.run, but that also replays the **17 story-event `addFeel: -1` choices** (§1.9). With the cheat on, those wrong answers no longer cost a note. For conversation-only scope, also require `TensionGauge curInstance ~~ nil` (`push_classvar class:TensionGauge 4`). The TensionGauge exists from matchingTalk 0x00fc to its destruct at 0x0f5a, and the event at 0x0f84 runs after that (untested). The SE 46 "lost" sound still plays (matchingTalk 0x0cfb). |

With A1–A3, a failed conversation costs no tension and no notes. Interest is not touched by conversations at all. Notes are only added, as ♪ or ● exactly as the reaction table says, so the countH < countO route test and pos still work: route A and route B both stay reachable. Not removed (not conversation losses): the slot decay ×3/4, the nightly ×1/2 and −1 interest, and the 8·v tension of positive addInterest.

Optional extensions, if "no losses" should be global:
- A4 `Favor addInterest argc=1` (71 B, sha1 6da1038c…): return early for v < 0. Covers the −1 decline and the −5/−9 jealousy cases.
- A5 `Favor addBad argc=1` (35 B, sha1 202c1113…): no-op. This **prevents girls dropping out** (§1.8), but the KBE witness event still plays and checkEvFlag 1843 stays satisfied.
- A6 `Favor downInterest argc=0` (48 B): skip the interest −1 (keep the tension and panic decay).
- Dates: leave alone (story logic).

### 4b. "Fewer rejections" (less likely, never forced)

| # | method | original | change | new size | risk |
|---|---|---|---|---|---|
| B1 | `Parson checkInterest argc=0` (methods) | 53 B, sha1 36d0a8ddff9d4f6de71fb80ad2936e29022125de | use `interest + 3` for both rolls (stored interest unchanged) | 68 B | Callers: GameMain kounai ×2 and Parson class>>checkInterest. Refusal drops from 60 % to 28 % at interest 3 and from 100 % to 60 % at interest 0 (table in §1.5; 0 % from interest 7). |
| B2 | `TensionGauge getTension argc=0` (methods) | 7 B, sha1 e24b1e407a8a612abf240be619b82d348993de47 | return `tension + 32` when the cheat is on | 22 B | The only readers are matchingTalk 0x02cd (walk-home ≥ 100 → real ≥ 68), 0x0346 (kiss ≥ 100 → ≥ 68) and 0x078b (あせり: thresholds 32/64/96 become 0/32/64). The gauge picture and Favor are unchanged. One patch eases three checks; the walk-home `stage == 0` gate is kept on purpose (stage 0 is before the level's first story event, and GKD/setEvent unlocks key off walk-home counts). |
| B3 | `MatchHistory checkLose4 argc=0` (70 B, sha1 b3fa13e0…) | | prefix `fewerRejections ifTrue: [^false]` (or test 5 misses instead of 4) | ~80 B | Only matchingTalk 0x0d6a. She no longer leaves out of boredom; 4–5 misses end as 時間切れ別れ 低 instead. |
| B4 | `MatchHistory checkLose3 argc=0` (73 B, sha1 1102b669…) | | same prefix | ~83 B | Only matchingTalk 0x0688. 退屈 becomes an ordinary 興味はある/興味もない miss (no note lost). |
| B5 (opt.) | `MatchHistory checkTopic3 argc=1` (46 B, sha1 e554fc91…) | | same prefix | ~56 B | Removes 同じ話ばかり (the player can avoid it anyway). |
| B6 (opt., larger) | `WadaiReaction class>>choice argc=4` (methods2, 511 B, sha1 e4099ffd…) | | in the filter at 0x00a3–0x0105, also reject records with [24] > 0 while the cheat is on | ~530 B | Removes the 15.5 % "bad" hit reactions. If only bad records match, the result is nil ("no reaction", 0 effect). The reaction table is shared by all 8 heroines; this is the only patch that changes which scene plays. |

Avoid replacing `K2_Script matchingTalk` itself (4055 B, 44 temps). Every change above sits in small leaf methods that matchingTalk calls.

### Uncertain / not verified

- `Integer rnd:` range is assumed to be 0..n-1.
- The meaning of the MST answer values (0 = talk, 1 = decline, 2 = leave) was read from NAR_MST only.
- The `checkLose4` / `addTopic` order relies on the MatchHistory thread having incremented tCount (sleep 32 plus the gauge wait); this was not timed.
- Events 25/20/30/35 (MED) were not read for hidden side effects. A grep found no stat-changing sends in any *_MAT/*_MED/*_MKI/*_MST/*_KBE script.
- The sketches were assembled, not run in `tools/qa/scfvm.py`. The `Cheat` class does not exist yet; a send to a missing class would raise UndefinedClassException.
