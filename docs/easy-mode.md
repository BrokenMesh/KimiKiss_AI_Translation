# Easy Mode

An optional set of four switches in the title menu (D-038). All are off by default; with all off the
game plays exactly as the original. They exist because KimiKiss is unforgiving: a girl refuses to talk
most of the time at the start, a bad conversation costs her mood, and two "jealousy" marks remove a
girl from the game for good.

Title menu → **Easy Mode** → up/down picks a row, circle or left/right switches it, cross closes. If a
switch changed, the game asks "Settings have been changed. Do you want to save?" (the same prompt as
after Settings), which writes them to the memory card's system data. The switches apply to every save.

| Switch | Bit | What changes |
|---|---|---|
| No Losses | 1 | Nothing she thinks of you goes down: no tension loss in conversations (bad reactions, the end-of-talk settlement), no notes taken off her gauge (also in story-event choices), no interest loss (overnight, declining her, jealousy), no jealousy marks (so no girl drops out). Gains are unchanged. |
| Fewer Rejections | 2 | When you meet her, the "talk or not" roll counts her interest as 3 higher (refusal at the start: 60 % → 28 %). She no longer gets bored after 3 misses (退屈) or leaves after 4 misses in a row (つまらない別れ). Inviting her home and kissing need conversation tension 68 instead of 100; the "flustered" reactions start 32 lower. |
| Easier Meetings | 4 | Each map spot rolls the encounter table up to 9 times instead of once, until the roll names a girl you have already met who is still in the game. Girls still only appear where and when the game places them; story events are not affected. |
| More Tries | 8 | The daily Attack (walk-home invitation or kiss) is never used up, and an empty topic deck is dealt again, so a day no longer runs out of conversations. |

## Routes stay open

Neither switch forces hearts or maximum values. The route (love or friendship) is decided once, at a
girl's first level-up, from hearts versus plain notes in her first gauge (`Parson >> levelUp`,
`Favor >> setStory`: friendship when hearts < plain notes). Conversations still add hearts or plain
notes exactly as the reaction table says; No Losses only stops notes from being removed. So both routes
remain reachable, and the endings (`PLY_KOK_A >> KOK_HANTEI`: level 4 and a kiss at level 4) are unchanged.

## How it works

The switches are an Integer bitmask in `GameParam` class variable 18, the `autoSkip` setting that the
game initialises, saves in the system data (config array element 0) and never reads; it is a leftover of
a cut "Auto Advance" option (its unused label texture `menu_set1` says so). Old saves and the unpatched
game hold `false` there, which reads as 0. Nothing in the save format changes.

`GameParam easyFlags` (nil or a Boolean → 0), `GameParam easy: bit` and `GameParam setEasyFlags:` are new
class-side methods. Every cheat is a small patch at the start of a leaf method: if its bit is off, the
original bytecode runs unchanged.

| Patch | Bit | Change |
|---|---|---|
| `Favor addTension:` | 1 | a negative change is dropped |
| `TensionGauge addTension:` | 1 | the same for the conversation gauge's own copy |
| `Favor downFeel` | 1 | answers -1 without removing a note (`FavorGauge >> run` then shows no loss icon) |
| `Favor addInterest:` | 1 | a negative change is dropped |
| `Favor downInterest` | 1 | sets `fInter`, so the nightly -1 is skipped; the nightly tension and panic decay stay |
| `Favor addBad:` | 1 | no jealousy mark |
| `Parson checkInterest` | 2 | rolls with interest + 3 |
| `MatchHistory checkLose3`, `checkLose4` | 2 | answer false |
| `TensionGauge getTension` | 2 | answers tension + 32 (read only by the walk-home, kiss and flustered tests in `K2_Script >> matchingTalk:`) |
| `GameParam class >> checkFirst`, `checkSecond` | 4 | re-roll `checkEncount:` up to 8 more times until `Parson isEnable:` |
| `GameParam useAttack`, `getAttack` | 8 | never consumes; shows the day's maximum |
| `TopicPlayer class >> getRemainder` | 8 | an empty deck is dealt again once (`setDeck`) |

The menu: `MainMenu >> makeMenu` adds command 6 after Settings, drawn with sprite 114 n 4
(`sysgraph/menu_main4`, the game's unused "Options" item, relabelled "Easy Mode" in
`translation/textures.toml`); `MainMenu >> menuTex:` supplies its sprite because the original table has
no entry 6. `MainMenu >> scriptMain` opens `Configuration >> easyMode: 0` for command 6, built like the
Settings branch. The panel (`easyMode:`, `easyRowY:`, `easyShow:`) is a `DialogBox` with `TextLine` text
(no new textures) and the Settings cursor sprite; each row has an "On" and an "Off" line that cross-fade,
like the Rumble switch. The English strings use the assembler's `en:"..."` constants.

## Game mechanics found on the way

How a conversation, an encounter and a day work. The full analysis with offsets and quoted bytecode is in
[easy-mode/conversation.md](easy-mode/conversation.md), [easy-mode/encounters.md](easy-mode/encounters.md)
and [easy-mode/menu.md](easy-mode/menu.md) (settings storage, title menu, Settings panel).

- **A day** has 4 map moves (Break 1, Break 2, Lunch, After School). A move with an event plays the event;
  otherwise two spots each roll a 20-entry person table for the place and time slot
  (`GameParam class >> checkEncount:`). 0 means nobody; a girl appears only if met (`deai`) and not
  removed (`Parson isEnable:`).
- **Meeting her**: `Parson >> checkInterest` rolls `interest > rnd(20)` (she comes to you), then
  `interest > rnd(10)` (she agrees to talk), else she refuses. Interest is 0..9, 3 at the start, -1 every
  night unless it went up that day.
- **A conversation** (`K2_Script >> matchingTalk:`) is up to 5 topics. Each turn is a hit or a miss against
  her hidden hand; a miss costs 8 or 12 tension, the third miss in a row also a note, the same topic three
  times 48 tension and a note; some hit reactions are bad too (15 % of the reaction table). At the end,
  tension changes by (score - 6) x 12. 4 misses in a row: she leaves; panic 4: she runs off flustered.
- **Attack** (one per day, two after a clear): with a part-filled gauge it invites her to walk home (needs
  stage ≥ 1 and tension ≥ 100), with a full gauge it tries a kiss (tension ≥ 100 and the place, clothes and
  crowd table must allow it).
- **Jealousy**: walking two girls home the same day, or a girl at level 2+ seeing a kiss, gives a mark;
  the second mark removes that girl from the game.
