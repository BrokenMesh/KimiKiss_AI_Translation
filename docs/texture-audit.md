# Texture text audit (menu and UI pictures)

Date: 2026-10-09. Status: log only. Nothing in `translation/textures.toml` was changed.

## What was audited

- `translation/textures.toml` (every `[[texture]]` and `[[texture.line]]`, plus the header that documents the keys).
- `qa/audit/sheet_00.png` to `sheet_23.png` (all 24 contact sheets, looked at one by one) and the closer `qa/audit/GRAPH0_NNNN.png` tiles where a sheet was not clear.
- `qa/audit/index.tsv` (222 rows) for the numbers: font size, squeeze, weight, outline rings, shadow.
- `docs/glossary.md` (UI labels, school terms, names) and `docs/decisions.md` D-035 (the settings panel, used as the model for "fixed and consistent").

Method: the style of each picture was compared with the pictures it appears with (same screen, same sprite family, normal/highlighted pair). Wording was compared with the glossary and across screens. Sizes in this log are the `font_px` values of the build in `index.tsv`. "Spread" means smallest to largest px in a group.

What was checked and found fine: all name spellings (Hoshino Yuumi, Satonaka Narumi, Mizusawa Mao, Sakino Asuka, Futami Eriko, Shijou Mitsuki, Kuryuu Megumu, Nana) follow the glossary; "Topic Bag", "Year 1/2/3", "Infirmary", "Schoolyard", "Gym", "Back Lot" follow D8; spelling is American everywhere ("Favorite", "Cafeteria", "Makeup"); no British forms were found. The map dialog (304) reads and fits well. Same Japanese gets the same English in all places checked (OK 決定, Back 戻る, Settings 設定, Wallpaper 壁紙, Album, Extras, Library, Music, Garden, Rooftop, Cafeteria, Schoolyard), apart from the cases listed below.

Where `textures.toml` has no explicit style keys, the look comes from the Japanese pixels, so sizes and outlines change from picture to picture. That is the main cause of almost every issue below. The remedy is the same each time: give each family one explicit set of keys.

## Conventions to apply

1. **One size cap per family.** Add `max_size` (it also raises the default, which is taken from the Japanese text height) and a common `squeeze` floor. A word that does not fit shrinks, never the other way round. Targets:
   - Topic names (`icon_wadai/itNNN`, 96x32): `max_size = 22`, `squeeze = 0.8`.
   - Conversation categories (`kaiwa/wtNNN` and their unnamed copies, 80x32): `max_size = 22`, `squeeze = 0.8`.
   - Area choices (`idou/choiceNN`, 80x32): `max_size = 22`, `squeeze = 0.8`.
   - Map tags with star or dot (`eriaNNm*`, 112x40): `max_size = 17`, `squeeze = 0.8`.
   - Map location plates (`eriaNNs*`): `max_size = 18`, `squeeze = 0.75`.
   - Menu plates 112x32 (girls, main, name tabs, save/load, night room, info, settings title): `max_size = 17`, `squeeze = 0.85`.
   - Small buttons 48x24 to 80x24 (`txt_NNN`): `max_size = 18`, `squeeze = 0.8`.
   - Pill headers (Album, Main Menu, Extras): `max_size = 30`.
   - Weekday tags (40x48): `max_size = 22`.
2. **State pairs get identical keys.** If two pictures have the same Japanese, copy the whole line block (box offsets aside): same `max_size`, `squeeze`, `rings`, `shadow`, `fill`, `outline`. Never fix one half only.
3. **Weight.** Bold with an outline or shadow for anything drawn on art (the default). SemiBold only for the 16 px settings rows on a transparent background (D-035), and nowhere else. Remove the hand-set `font = "SemiBold"` from topic 447, categories 248, 150, 190, 433 and plates.
4. **Outline versus shadow.** Pictures that had an outline keep an outline, `rings = 2`, with an explicit dark `outline` colour when the default reads a grey or white halo. Pictures that had a plain shadow (menu plates, pill headers) use `style = "shadow"`, `rings = 0`, `shadow = [2, 2]` on plates and `[0, 2]` on pill headers, `fill = "#ffffff"` on plates. Do not mix `rings = 1` with no shadow in a set of plates.
5. **Hand-set black outlines (`outline = ["#090909"]` and similar) are not allowed on coloured labels.** The coloured outline of the original (cyan, green, pink) is part of the look.
6. **Alignment.** Text is centred in the free area of its picture (`align = "centre"` with a `box`), except settings rows (left, D-035) and unplated Save/Load/To Title (left edge of the old text). Keep 2 to 3 px of margin to the picture's edge: `box` or `x_min`/`x_max`, not touching.
7. **Case.** Title Case for menu items, labels, tabs and buttons ("Reset to Default", "Auto Advance", "Hold Hands"). Sentence case with a final "!" for hint banners; question for the dialog. ALL CAPS only for the two art captions "LEVEL UP!!" and the map's "LIKE"/"FRIENDS". Abbreviations allowed: "P.E.", "Home Ec", "Prep Room", "OK". No new ones.
8. **Same English for different Japanese is allowed only where the glossary says so.** Where two Japanese words get one English word (Save, Sports), see T-028 and T-018.

## Issues

Priority: high = visible inconsistency on one screen or wrong text; medium; low. "Fixable" = fixable in `textures.toml`.

### Topic names (`icon_wadai/itNNN`, 45 pictures, entries 380 ... 533)

**T-001** Topic names, outline colour wrong on 9 pictures. Priority: high. Fixable: yes.
- Entries 177 (Music), 199 (Makeup), 526 (Health), 14 (Reading), 421 (Future), 66 (Past), 447 (Hold Hands), 86 (Kamikaze). Hold Hands and Kamikaze have a white outline around white text, so the letters have no edge and look smeared; the others have a grey, blurred halo instead of the crisp black outline of Small Talk, Clubs, Uniform and the rest (compare sheet_00 with sheet_01).
- Fix: on every line of the 45 blocks add `outline = ["#101010"]` and `rings = 2` (explicit, so the colour is not read from the picture). If the original of one topic has a thinner outline (253 Act Cool, 203 Escape), keep `rings = 2` anyway for consistency; 1 ring at 15 px is not readable.

**T-002** Topic names, size spread 14.9 to 26.4 px (median 24.1), set only by the height of the Japanese. Priority: high. Fixable: yes.
- 22 pictures are 14.9 to 20.7 px: 253 Act Cool 14.9, 203 Escape 14.9, 447 Hold Hands 16.5, 78 Accessories 17.0, 390 Home Study 17.3, 284 Junk Food 18.4, 118 Private 18.4, 120 Shopping 19.5, 437 Fashion 19.5, 172 Diet 19.5, 86 Kamikaze 19.5, 330 Committee 19.6, 310 Swimming 20.4, 476 Italian 20.7, 149 Sweets 20.7. Eight are 25.3 to 26.4: 445 Rules, 140 Uniform, 357 Exams, 199 Makeup, 34 Meal, 526 Health, 361 Body, 479 Love.
- Fix: on every line `max_size = 22`, `squeeze = 0.8`. Short words land at 22, long ones (Accessories, Home Study, Junk Food, Act Cool, Hold Hands, Kamikaze) drop to about 16 to 18 instead of 15 to 17. Check the result in `--preview`.

**T-003** Topic 447 (Hold Hands) is hand-set to something different. Priority: medium. Fixable: yes.
- The block has `font = "SemiBold"`, `squeeze = 1`, `rings = 1`, so it is the only SemiBold, unsqueezed, single-ring topic and is the blurriest picture of the group.
- Fix: delete those three keys; it then follows T-001/T-002.
- Also: `rings` is 3 on 256 (Praise) and 144 (Smile), 1 on 253, 203, 447, and 2 on the other 40. With T-001 all become 2.

**T-004** Topic names touching the left or right edge of the 96 px picture. Priority: medium. Fixable: yes.
- Entries 380 Small Talk, 84 Teacher, 14 Reading, 390 Home Study, 277 Transfer, 78 Accessories, 86 Kamikaze, 330 Committee, 310 Swimming: the outline reaches the picture's edge (clipped on Kamikaze and Home Study).
- Fix: `box = [3, 0, 93, 32]` on these nine lines (or on all 45, same text area for every topic).

**T-005** Wording of topic 203 (エスケープ). Priority: low. Fixable: yes.
- "Escape" is opaque, the note in the file says it means skipping class (REVIEW). Proposal: `english = "Skip Class"` (10 chars, fits at 16 px with squeeze 0.8). Keep "Escape" only if the owner wants the original loan word.

**T-006** Topic entries marked REVIEW whose English is acceptable, no action needed unless the owner disagrees: 330 Committee (D8 uses "Discipline Committee" only for 風紀委員, so plain "Committee" is correct), 277 Transfer, 357 Exams, 362 Video, 315 Naughty, 66 Past, 86 Kamikaze. Priority: low. Fixable: n/a. (Listed so the fixer does not spend time on them.)

### Map screen: calendar

**T-007** Calendar "Day" (151). Priority: low. Fixable: partly.
- 14.9 px, ring 1, sits fine. The note says it reads "2 Day (Tue)" because the number sprite stays left of the word, which is wrong English order ("Day 2"). The number is a separate sprite, so toml cannot fix the order; it needs an in-game check by a human (see the final table, T-043). In toml only: add `max_size = 17` so it matches other small labels.

### Map screen: area and period choices

**T-008** Area choices (`idou/choice01` to `choice13`, entries 272, 384, 33, 220, 333, 527, 173, 282, 480, 170, 360, 9, 117), size spread 15.6 to 30.5 px. Priority: high. Fixable: yes.
- Year 1/2/3: 30.5, 28.5, 28.0 (squeeze 0.85). Music 30.0. Gym 25.3, Garden 25.0, Library 24.1, Rooftop 23.6, Science 23.1, Home Ec 20.3, Cafeteria 19.8, Infirmary 19.1, Schoolyard 15.6. These 13 are shown together as one list.
- Fix: all 13: `max_size = 22`, `squeeze = 0.8`. Result: Year 1/2/3 = 22, Music/Gym/Garden = 22, the long words 16 to 19.

**T-009** Area choices, outline and edge fit. Priority: medium. Fixable: yes.
- `rings` is 1 on 220, 527, 480, 360, 9 and 2 on 272, 384, 33, 333, 173, 282, 117, and 3 on 170 (Gym). On 360 Cafeteria and 9 Schoolyard the outline is a thin grey that makes the text look soft. Library (220), Music (282), Rooftop (480), Garden (117) touch both edges of the 80 px picture.
- Fix: `rings = 2` on all 13, plus `box = [2, 0, 78, 32]`.

**T-010** Period tabs (`idou/choice_1` to `choice_4`). Priority: medium. Fixable: partly.
- 269 Break 1 (17.2 px, squeeze 0.93), 376 Break 2 (17.4, 0.85), 28 Lunch (17.2, 1.0) are SemiBold, no outline, black on a white patch; the patch is wider than the old text and the text starts at the picture's left edge. 215 After School is a hand-made override and is smaller and thinner than the other three (see the sheet_03 bottom rows). They do not look like one set.
- Fix in toml: give 269, 376, 28 the same `squeeze = 0.9` and `max_size = 17` so Break 1 and Break 2 are the same width. The override (215) cannot be changed by the fixer; see the final table. If the owner prefers, remove the override and let a toml block draw After School like the others (note on line in file says it falls back to "After" if it does not fit).

### Map screen: place tags (`eriaNNmN` = star or dot tag, `eriaNNsN` = location plate, pairs of s0/s1)

**T-011** Star and dot tags (24 pictures, `eriaNNm*`), size spread 12.5 to 23.0 px. Priority: high. Fixable: yes.
- Smallest: 273 Science Lab 12.5, 145 Music Room 12.5, 331 Prep Room 12.5, 472 Prep Room 13.0, 80 Prep Room 13.0, 110 Schoolyard 13.5, 519 Bookshelf 14.0. Largest: 432 Gym 23.0, 507 Fence 21.8, 354 Garden 19.5, 406 Library 19.5, 440 Home Ec 19.0, 236 Walkway 18.5.
- Fix: all 24 lines `max_size = 17`, `squeeze = 0.8`, same shadow `[0, 2]`, `rings = 1`. Today `rings` is 0 to 2 and shadow `[0, 1]` to `[0, 3]` (for example Library 406 `[0, 3]`, Year 1 Hall 294 `[0, 2]`). This lifts the 12.5 px ones to about 14 to 15 and brings Gym/Fence down to 17.

**T-012** Location plates: the two states of one place are different from each other. Priority: high. Fixable: yes.
- Size: 03s (358: 20.1, 477: 21.5), 08s (258: 19.6, 449: 21.0), 10s (436: 24.1, 10: 26.2), 06s (392: 14.1, 37: 14.7), 11s (60: 14.6, 246: 15.0).
- Shadow and rings: 09s (513: shadow `[0,1]`; 153: none), 11s (60 `[0,1]`; 246 none), 13s (481: ring 1, no shadow; 119: ring 0, shadow `[1,1]`), 04s (524 `[0,1]`; 171 `[0,2]`), 03s (358 `[0,3]`; 477 `[0,2]`), 01s (411 and 57 both ring 0, shadow `[2,2]`, fine), 10s (436 `[1,1]` set by hand; 10 not set).
- Fix: for each pair use one set of keys on both: same `max_size`, `squeeze`, `rings`, `shadow`. Suggested: `max_size = 18`, `rings = 1`, `shadow = [1, 1]` on all s-plates, with `fill = "#ffffff"` as now.

**T-013** Location plates, text too small. Priority: medium. Fixable: yes (mostly).
- 88/283 Home Ec 13.1/13.2, 392/37 Science 14.1/14.7, 513/153 Rooftop 14.5, 60/246 Cafeteria 14.6/15.0, 524/171 Library 16.5. The build flags 283, 37, 153, 246, 119 and 10 as "small text".
- Fix: `squeeze = 0.75` on these ten lines (text becomes about 15 to 17 px in the same box). Do not widen the boxes: the plates are narrow (about 53 to 61 px). If still too small, that is a plate-size limit ("needs larger sprite").

**T-014** Location plates, leftovers and damage from the erase. Priority: high. Fixable: partly.
- 119 Garden (112x64, highlighted): the pink plate is cut off at the bottom and right (the white outline is missing there) and the word touches the blue tile. 481 Garden: same word touches the green tile, the plate's lower right outline is flattened. 10 Gym: a notch at the left of the pink plate (the plate is cut where the old text ended). Compare with 436 Gym, which is intact. 513/153 Rooftop: the plate's top-left corner is eaten.
- Fix: put `box` inside the plate and stop the "commonest" fill from repainting the outline, for example 119 and 481: `box = [8, 32, 54, 56]` (right edge at 54, not 60, so the word stops before the tile) and `max_size = 15` with `squeeze = 0.75`; 10: `x_min = 124`. Mark CHECK-ART and look at `--debug`. If the plate outline stays damaged, a human artist has to repaint it (see final table).

**T-015** Same Japanese, different English on the map tags. Priority: low. Fixable: yes.
- 準備室 appears as "Prep Room" on 472, 80 and 331 (three different areas). The glossary says "Science Prep Room" for 理科準備室 (36 uses). Tags sit next to the area, so "Prep Room" is understandable; only change if the owner wants the glossary form (it will not fit at 112x40).
- Abbreviation "Home Ec" (440, 88, 283, choice07 173) is consistent and glossary-conform. No change.

### Dialog

No issue found in entry 304 (Go to this area? / OK / Back): sizes 29.9 and 21.8 are consistent with each other and the text sits inside the panel.

### Conversation: topic categories (`kaiwa/wtNNN` and their unnamed copies)

The ten categories have a normal picture (named, entries 248 ... 532) and a highlighted copy without a name in the executable (entries 295, 52, 238, 1, 190, 433, 375, 491, 499, 266). They must read the same.

**T-016** Hand-set black outline and SemiBold on coloured category labels, pairs do not match. Priority: high. Fixable: yes.
- 248 School Life (SemiBold, `fill #ffffff`, `outline #090909`, 14.2 px) against its copy 295 (Bold, default look, 15.8 px, pale blue outline): the pair does not read as one label, and 248 loses the cyan look of the original.
- 150 Beauty (SemiBold, outline `#1a3a32`, 20.7) against 190 Beauty (SemiBold, outline `#101830`, 20.7): two different outline colours for the same label, and neither is the original's green.
- 388 Stylish (Bold, pink, 17.2 px, `[0,1]` shadow) against 433 Stylish (SemiBold, black outline, 14.0 px, `max_size = 14`): the highlighted copy is black on white while the normal one is pink.
- Fix: on 248, 150, 190, 433 delete `font`, `fill`, `outline`, `squeeze`, `max_size`. Then give all 20 category lines the same keys (T-017). Check that "School Life" fits 80 px at about 15 px (squeeze 0.8); if not, let it shrink.

**T-017** Category size spread 14.0 to 26.4 px, and the pairs differ in rings and shadow. Priority: medium. Fixable: yes.
- Sizes (normal / highlighted): Study 26.4/26.4, Sports 25.3/25.3, Action 25.3/25.3, Effect 25.3/25.3, Leisure 23.8/24.8, Beauty 20.7/20.7, Food 19.5/19.5, Romance 19.3/19.3, Stylish 17.2/14.0, School Life 14.2/15.8.
- Pairs that differ in the build: Sports 81 (rings 2, shadow `[0,1]`, squeeze 0.91) and 52 (rings 3, no shadow, 0.89); Leisure 200 (squeeze 0.88, no shadow) and 238 (0.85, `[0,1]`); School Life 248 (SemiBold, ring 1) and 295.
- Fix: all 20 lines `max_size = 22`, `squeeze = 0.8`, `rings = 2`, `shadow = [0, 1]`.

**T-018** Category wording. Priority: low. Fixable: yes.
- 美容健康 shows "Beauty" (150, 190) and drops "Health"; the topic "Health" (健康, 526) sits under this category, so the player sees Beauty with the topic Health inside. Acceptable; keep "Beauty" unless a longer form fits 80 px (it does not at 14 px: "Beauty/Health" needs about 100 px).
- 運動 (81, 52) is "Sports", the same English as topic スポーツ (417). Proposal: change the category to "Exercise" (81 and 52), keep the topic "Sports". Medium-low; the note on 417 should be kept.
- おしゃれ "Stylish" and the topic ファッション "Fashion" are fine together.

### Level-up banner

**T-019** "LEVEL / UP!!" (347). Priority: low. Fixable: yes.
- The outline is a soft blue-grey, not crisp (it is read from the picture), and "UP!!" sits left of centre under "LEVEL" while the original lines were staggered right.
- Fix: `outline = ["#1c4fa0"]`, `rings = 2`, and a second line with `align = "centre"`. Do not lower the 21 px size.

### Map hint banners (`sysgraph/map_hN`, 328x32; there is no map_h6)

**T-020** Banners are aligned and framed differently, some touch the frame. Priority: high. Fixable: yes.
- 395 is right-aligned next to its icon; 41, 536, 94 are centred over the full width; 227 and 341 start flush against the left frame; 94 touches the frame on both sides; 486 is centred left of its icon. Outline rings: 395 1, 41 1, 227 2, 341 1, 536 2, 94 2, 486 1. Shadow: `[0,1]`, `[1,1]`, `[0,1]`, none, `[0,1]`, `[0,1]`, `[0,1]`. Size is 18.4 everywhere except 41 at 17.2.
- Fix: all seven lines `align = "centre"`, `max_size = 17`, `squeeze = 0.85`, `rings = 2`, `shadow = [0, 1]`. Banners with an icon on the right (395, 227, 341, 486): `box = [8, 0, 282, 32]`. Banners without an icon (41, 536, 94): `box = [8, 0, 320, 32]`. Replace the current `x_max` keys by these boxes.

**T-021** Banner wording is too long for the banner. Priority: medium. Fixable: yes.
- 227 "Let's go on an after-school date!" (33 chars) and 94 "The school festival is this weekend!" (36 chars) only fit by touching the frame. Proposals: 227 `english = "Go on an after-school date!"`; 94 `english = "School festival this weekend!"`. 536 "Holiday date this weekend!" is fine (keep). 486 "Favorite topic changed!" is fine.

### Album, Main Menu, Extras and Wallpaper pill headers

**T-022** The three pill headers are different sizes and shadows. Priority: medium. Fixable: yes.
- 124 Album 32.2 px, shadow `[0,3]`; 545 Main Menu 29.9 px (squeeze 0.91, runs to the pill's right end), shadow `[0,2]`; 23 Extras 31.0 px, shadow `[0,2]`.
- Fix: all three `max_size = 30`, `shadow = [0, 2]`, `rings = 0`. For 545 also `box = [40, 6, 180, 48]` so the "u" does not touch the pill's edge.

**T-023** Wallpaper pill (102) is hard to read. Priority: medium. Fixable: yes.
- 18.8 px, pale pink on white with only a faint shadow; the other pills have a clear dark shadow. The box ends at x = 128 although the pill is 144 wide.
- Fix: `shadow = [0, 2]` (same as Main Menu), `box = [45, 6, 138, 46]`, `max_size = 22`. If the colour read from the Japanese is also too light, add `fill` with the pink of the Album text.

### Girls menu (`menu_girl0` to `girl9`)

**T-024** Plates differ in size and outline. Priority: medium. Fixable: yes (7 of 10).
- Everyone 424, Nana 429, Other 186: 18.4 px, ring 1, no shadow. Names: 539 Hoshino Yuumi 14.9, 487 Sakino Asuka 16.8, 233 Shijou Mitsuki 15.9, 72 Kuryuu Megumu 13.9 (squeeze 0.86, touches the plate frame). Shadow `[0,1]` on 539 and 233 only.
- Fix: all ten (including the three overrides if they are ever rebuilt) one set of keys: `max_size = 16`, `squeeze = 0.85`, `rings = 1`, `shadow = [0, 1]`, `box` 3 px inside the plate. Names stay about 14 to 16, words 16.
- The overrides 180, 292, 128 (the other three names) are heavier and larger than the toml names; see final table.

### Main menu plates (`menu_main0` to `main5`, plus unnamed 278 Carry Over)

**T-025** "Carry Over" is a different style from the other main menu buttons. Priority: high. Fixable: yes.
- 535 and 278: 17.9 px, black text with white outline, shadow `[1,2]`, ring 1; the five others (279 New Game, 393 Continue, 38 Album, 224 Extras: 16.1 px, white, ring 0, shadow `[2,2]`) are white with a shadow; 340 Options: 16.1 px, ring 1, no shadow.
- Fix: for 279, 393, 38, 224, 340, 535, 278 use the same keys: `fill = "#ffffff"`, `style = "shadow"`, `shadow = [2, 2]`, `rings = 0`, `max_size = 17`, `squeeze = 0.85`. 535 and 278 must be identical to each other.

### Name entry and history tabs (`menu_name0` to `name4`)

**T-026** Tabs mix outline and shadow. Priority: medium. Fixable: yes.
- 61 Hiragana 18.4 and 247 Katakana 16.1: shadow `[2,2]`, ring 0. 500 Kanji 19.5, 438 ABC 123 18.4 (ring 2, heavy black), 12 History 18.4: outline, no shadow. Size spread 16.1 to 19.5.
- Fix: all five `style = "shadow"`, `shadow = [2, 2]`, `rings = 0`, `fill = "#ffffff"`, `max_size = 17`, `squeeze = 0.85`.

### Save and load menu (`menu_sio0` to `sio5`)

**T-027** Save/Load plates and plain labels differ in size and shadow. Priority: medium. Fixable: yes.
- Plated: 401 Save 17.2 px `[2,2]`, 46 Save 18.4 `[3,3]`, 230 Load 17.2 `[3,3]`. Plain (no plate): 350 Save 18.4 `[1,2]`, 547 Load 17.2 `[1,2]`, 105 To Title 16.1 ring 1 `[0,1]`. So Save is 18.4 and Load 17.2 in the same menu, and the shadow is 1 to 3 px.
- Fix: all six `max_size = 17`, `style = "shadow"`, `shadow = [2, 2]`, `rings = 0`, `fill = "#ffffff"`; 350, 547, 105 `align = "left"` (the plain ones are left-aligned like the original).

**T-028** Two different Japanese words both become "Save". Priority: low. Fixable: yes.
- 401 しおり (bookmark) and 46/350 セーブ are all "Save". If both are shown in the same menu the player cannot tell them apart. Check in game; if so, 401 could be "Bookmark" (fits 112 px).

### Settings panel (`menu_set0` to `set9`; reference D-035)

**T-029** Auto Advance (342) does not match the settings rows. Priority: high. Fixable: yes (left edge needs a check).
- 342: Bold 19.5 px, ring 1, shadow `[0,1]`, drawn at the position of the Japanese. All other rows: SemiBold 16 px, no ring, shadow `[1,1]`, left aligned (set2, set3, set4, set8, set9, set5). So one row of the same list has another weight, size and edge.
- Fix: `font = "SemiBold"`, `max_size = 16`, `style = "shadow"`, `shadow = [1, 1]`, `align = "left"`, `box = [X, 0, 144, 32]`. `X` is the left edge the rows share on screen; the rows use `x = 40` in the 120 px sprites and 20 for Text Speed (all centred on the old centre), so compute it from the position of the 144 px sprite and check in game. If the 144 px sprite's left edge is further right than the others, say so as "needs larger sprite" (menu_set1).
- Check the same for 402 Reset to Default (144 px, no `box`): its text starts about 10 px in, which is a different left edge than the rows. Treat the same way.

**T-030** Values "Yes" and "None" (48, 232) for あり/なし. Priority: medium. Fixable: yes.
- With "Rumble", "BGM", "Voice", "Wallpaper" the natural pair is "On" / "Off". "None" is an odd opposite to "Yes". Note on 48 says REVIEW. Proposal: 48 `english = "On"`, 232 `english = "Off"`. If the same value sprites are also used for Text Speed or other rows where "Yes/No" fits better, keep "Yes" and use "No" (and not "None"). Needs an in-game check of where each is shown.

### Night room menu (`menu_yoru0` to `yoru2`) and Info (`menu_jo0`)

**T-031** Night room plates mix shadow. Priority: low. Fixable: yes.
- 16 Girls (ring 1, no shadow), 122 Sleep (ring 1, `[0,1]`), 319 Topic Bag (ring 1, `[1,1]`), 285 Info (ring 1, `[0,1]`), all 18.4 px. The size is consistent; the shadow is not.
- Fix: same as menu plates convention: `style = "shadow"`, `shadow = [2, 2]`, `rings = 0`, `fill = "#ffffff"`, `max_size = 17`.
- Wording: 16 菜々 reads "Girls" (D-029) while the girls menu shows 菜々 as "Nana" (429). Decision exists; log only. Priority low, no action.

### Buttons and small labels (`sysgraph/txt_001` to `txt_022`, 48x24 to 80x24)

**T-032** Two button labels are illegible at 12.4 px. Priority: high. Fixable: yes.
- 68 Settings (48 px wide, squeeze 0.88) and 542 Observe (48 px, squeeze 0.86), both 12.4 px, flagged as small.
- Fix: `squeeze = 0.7` and `max_size = 15` on both; Observe at 7 letters and Settings at 8 letters then fit about 15 px. Alternatives if still too small: 68 `english = "Setup"`, 542 `english = "Look"`.

**T-033** Button size spread 12.4 to 20.7 px, and the "Yes" outline is ragged. Priority: medium. Fixable: yes.
- Sizes: 321 Yes 20.7, 366/398 OK 18.4, 369 Next 18.4, 451 Edit 18.4, 90 Rename 18.4, 100 Move 18.4, 422 Play 18.4, 345 Memo 18.4, 125 Erase 18.4; 483/44 Back 17.2; 206 Delete 16.4; 426 No 16.1, 261 Hint 16.1, 17 Test 16.1; 537 Pattern 14.9, 179 Scroll 14.9. Yes (48 px sprite) is the biggest and looks jagged; No (64 px sprite) is smaller.
- Fix: all 20 `max_size = 18`, `squeeze = 0.8`, `rings = 1`. That brings Yes down and Pattern/Scroll up to 16 or more. Set Yes and No to the same size (both 18).

**T-034** "Memo" (345) is marked REVIEW. Priority: low. Fixable: yes.
- 枠メモ is read by the note as hard to read (枠 or 終). "Memo" is safe; if the first kanji is 枠 ("frame"), a better English is "Note". Keep unless the owner knows the screen.

### Weekdays (40x48, entries 21, 219, 343, 79, 423, 457, 250)

**T-035** Weekday abbreviations have wildly different sizes. Priority: high. Fixable: yes.
- Sun 22.8, Mon 20.1, Tue 23.1, Wed 19.1 (flagged small text), Thu 22.6, Fri 35.1 (squeeze 0.85, ring 2), Sat 26.8. Fri is almost twice Wed.
- Fix: all seven `max_size = 22`, `squeeze = 0.8`, `rings = 1`. Check "Fri" and "Wed" still fit 40 px.

### Other unnamed pictures

**T-036** Next / OK (45). Priority: low. Fixable: no change needed.
- "Next" 29.9 px green and "OK" 17.2 px white on blue: matches the original design. No action. (Listed so the fixer can skip.)

## Not fixable in textures.toml

| ID | Entries | Problem | Who can fix |
|---|---|---|---|
| T-037 | GRAPH0 262 (64x128 green bag) and 289 (64x128 shrine charm) | Hand-made overrides that are byte-identical to the original (D-020 notes this). The kanji 類 and 合格 are still Japanese on screen. Priority: high | human artist (draw English on the art), then replace the override |
| T-038 | 453 `sysgraph/map` (override) | "LIKE" and "FRIENDS" on the map overview are tiny (about 9 px), crooked, and the old katakana left ghost marks (dashes and speckles on both sides of each word); they do not match any other label. Priority: medium | human artist |
| T-039 | 215 `idou/choice_4` (override, After School) | Thinner, smaller and lighter than the toml-drawn Break 1, Break 2, Lunch (see T-010). Priority: medium | human artist redraws at SemiBold 17 like the others, or delete the override and use a toml block |
| T-040 | 223, 336 (`eria05s0/s1`, Infirmary), 311, 418 (`eria12s0/s1`, Schoolyard) | Overrides are condensed and smaller (about 12 px) than the toml plates (13 to 18 px); the highlighted copy has a different text colour from the normal one. Priority: medium | human artist, or delete the overrides and give them toml blocks (the blocks already exist in the file) |
| T-041 | 180, 292, 128 (`menu_girl2/3/5`, three heroine names) | Overrides, heavier and larger than the toml name plates (T-024). Priority: low | human artist, or delete the overrides and use the toml blocks that already exist |
| T-042 | 119 Garden, 10 Gym plates (T-014); 342 Auto Advance left edge (T-029) | If the toml box and keys do not clear the damage or the left edge, a larger sprite or repainted plate art is needed. Priority: medium | human, after the in-game check |
| T-043 | 151 calendar "Day" | The number sprite is separate; "Day" cannot be placed after the number. Priority: low | human (script or sprite order) |

## Count by priority

High: T-001, T-002, T-008, T-011, T-012, T-014, T-016, T-020, T-025, T-029, T-032, T-035, T-037. Medium: T-003, T-004, T-009, T-010, T-013, T-017, T-021, T-022, T-023, T-024, T-026, T-027, T-030, T-033, T-038, T-039, T-040, T-042. Low: T-005, T-006, T-007, T-015, T-018, T-019, T-028, T-031, T-034, T-036, T-041, T-043. T-036 and T-006 need no change; they are listed only to prevent wasted work.

## Outcome (fix pass)

Date: 2026-10-09. All edits are in `translation/textures.toml`. Previews of the result: `qa/fix_all/` (all 217 textures, 16 sheets). Sizes below are the measured `font_px` of the preview. Entries that have a hand-made override in `texture_overrides/` were not touched (their toml blocks have no effect in the build).

Counts: fixed 24, partly fixed 4 (T-007, T-010, T-024, T-029), not fixed 10 (T-005, T-018, T-028, T-030, T-037 to T-041, T-043), not needed 4 (T-006, T-015, T-034, T-036). T-042 is a pointer to T-014 and T-029 and is not counted.

- **T-001** fixed. All 45 topic lines: `outline = ["#101010"]`, `rings = 2`. The hand-set `font`, `squeeze` and `rings` of 447 are gone. Crisp black edge on every picture.
- **T-002** fixed. `max_size = 22`, `squeeze = 0.8` on all 45. Result: 40 pictures at 22 px, long words smaller: Accessories 17.5, Home Study 18.5, Hold Hands 19, Committee 20, Escape 21, Junk Food 21, Swimming 21, Small Talk 21.5.
- **T-003** fixed (font, squeeze and rings removed from 447; all topics now use 2 rings).
- **T-004** fixed. `box = [3, 0, 93, 32]` on all 45. Exception 390 Home Study: `box = [2, 0, 95, 32]`, because the old outline reaches x = 94 and a stray line stayed at the right edge with the proposed box.
- **T-005** not fixed. "Escape" is kept. エスケープ sits next to アタック ("Attack", topic 533) and both are named together as icons on the help pages (decisions.md, phase 6 notes). It looks like a conversation action, not "skipping class", so "Skip Class" is not clearly better and was not applied. The REVIEW note stays.
- **T-006** not needed.
- **T-007** partly fixed. `max_size = 17`; "Day" is now 17 px. The word order ("2 Day") is still wrong, see T-043.
- **T-008** fixed. `max_size = 22`, `squeeze = 0.8`. Year 1/2/3, Music, Gym, Garden, Library, Rooftop, Science at 22; Home Ec 20.5, Infirmary 19.5, Cafeteria 19, Schoolyard 15.5.
- **T-009** fixed, with one finding. `rings = 2`, `box = [2, 0, 78, 32]`. The original art is black text with a white outline. The auto read gave white text with a black outline on Year 1/2/3 and a thin grey outline on the others. All 13 now have `fill = "#090808"`, `outline = ["#ffffff", "#ffffff", "#ffffff"]`.
- **T-010** partly fixed. 269, 376, 28: `max_size = 17`, `squeeze = 0.85` (not 0.9: at 0.9 Break 2 fell to 16 px). Break 1, Break 2 and Lunch are 17 px. 215 (override) is unchanged, see T-039.
- **T-011** fixed. All 24: `max_size = 17`, `squeeze = 0.8`, `rings = 1`, `shadow = [0, 2]`. Seven tags were limited by their box, so the box was widened to the right end of the orange strip: 145, 273, 110 `[34, 4, 108, 37]`; 331 `[40, 5, 108, 36]`; 80, 472, 519 `[40, 4, 108, 37]`; 507 `[38, 4, 106, 37]` (the old Fence text started at x = 39 and left a stray line). Result 14.5 to 17 px: Music Room and Science Lab 14.5, Prep Room 15, Schoolyard 15.5, Bookshelf 16, the rest 17.
- **T-012** fixed. All 22 plates without override: `max_size = 18`, `squeeze = 0.75`, `rings = 1`, `shadow = [1, 1]`, `fill = "#ffffff"` and an explicit `outline = ["#2e2220"]` (the dark colour the original text uses). Without the explicit colour 119 had no outline and 481 had one. Pairs are identical.
- **T-013** fixed. Home Ec 15, Rooftop and Science 16 to 16.5, Cafeteria 16.5, Garden 16, Library, Year and Music 18, Gym 18. No flag left on these plates.
- **T-014** fixed (check in game). 119 and 481 Garden: `box = [9, 31, 58, 57]`, `max_size = 16` (the proposed `[8, 32, 54, 56]` still erased the white outline at the bottom; the plate face is x 9..58, y 31..56). 10 and 436 Gym: the notch came from erasing the corner of the neighbouring tile and the bottom outline. Both now have `box = [126, 3, 205, 31]` and a `background` list that includes the tile colours (10: `["commonest", "#15b5ff", "#06329a"]`; 436: `["commonest", "#b3fdb7", "#509356", "#7b442c"]`); this is better than `x_min = 124`. 513 and 153 Rooftop: `box = [8, 16, 59, 44]`; the plate corner is intact in the preview. The Garden word ends about 1 px from the tile.
- **T-015** not needed.
- **T-016** fixed. `font`, hand-set `fill`, `outline`, `squeeze`, `max_size` removed on 248, 150, 190, 433. Because the auto read gave different colours for the two states, the three pairs that differed got the same explicit colours: School Life (248, 295) white with `["#6bb9c7", "#2d7786"]` (cyan), Beauty (150, 190) white with `["#96caa9", "#4a7058"]` (green), Stylish (388, 433) white with `["#b08ab2", "#090909"]` (pink, then black). The other seven pairs keep the colours read from the picture (they match).
- **T-017** fixed. All 20: `max_size = 22`, `squeeze = 0.8`, `rings = 2`, `shadow = [0, 1]`, plus `box = [3, 0, 77, 32]` so that nothing touches the edge (Beauty did). Result: 22 px for Food, Sports, Beauty, Leisure, Effect, Stylish, Study, Action; Romance 19; School Life 16 (long word).
- **T-018** not fixed (wording kept). "Beauty" kept. "Exercise" for 運動 was tried and undone: at 20.5 px with squeeze 0.81 and two rings the letters run together. 運動 stays "Sports" (same word as topic 417). Use "Exercise" only with a wider sprite.
- **T-019** fixed. `outline = ["#1c3aa8"]`, `rings = 2`, `align = "centre"`. A line cannot be centred on its own, so the second line is written with two leading spaces: `english = "LEVEL\n  UP!!"`. 21 px kept.
- **T-020** fixed, with a change. All seven: `align = "centre"`, `max_size = 17`, `squeeze = 0.85`, `rings = 2`, `shadow = [0, 1]`, `x_max` removed. Boxes: `[8, 4, 276, 28]` for 395, 227, 341, 486 (icon on the right) and `[8, 4, 320, 28]` for 41, 536, 94. The proposed `[8, 0, 282, 32]` erased the frame (rows 0 to 3 and 28 to 31) and cut the heart of 395; the icon starts at x = 279. All seven are 17 px.
- **T-021** fixed. 227 "Go on an after-school date!", 94 "School festival this weekend!".
- **T-022** fixed. 124, 545, 23: `max_size = 30`, `shadow = [0, 2]`, `rings = 0`; 545 also `box = [40, 6, 180, 48]`. All three are 30 px (Main Menu 0.87 squeeze).
- **T-023** fixed. 102: `shadow = [0, 2]`, `rings = 0`, `box = [45, 6, 138, 46]`, `max_size = 22` (21.5 px). The fill was already the same pink as Album (`#d2a2a1`), so no `fill` key. It is still the palest of the four because the strokes are thin.
- **T-024** partly fixed (7 of 10, the overrides 180, 292, 128 are not touched). Keys: `fill = "#ffffff"`, `style = "shadow"`, `rings = 0`, `shadow = [1, 1]`, `max_size = 16`, `squeeze = 0.85`, `x_min = 9`, `x_max = 105`, `align = "centre"`. This differs from the proposal (`rings = 1`, `shadow = [0, 1]`): the original plates are white text with a drop shadow, and an outline made the names heavy. Sizes: Everyone, Nana, Other 16, Sakino 16, Shijou 15.5, Hoshino 14.5, Kuryuu 13.5. Nothing touches the plate frame now. `align = "centre"` is needed: with `x_min` and the default alignment "Other" moved 12 px to the right (see new problems).
- **T-025** fixed. 279, 393, 38, 224, 340, 535, 278: `fill = "#ffffff"`, `style = "shadow"`, `rings = 0`, `shadow = [2, 2]`, `max_size = 17`, `squeeze = 0.85`. All 17 px; 535 and 278 identical.
- **T-026** fixed. 500, 61, 247, 438, 12 with the same keys as T-025. All 17 px.
- **T-027** fixed. 401, 46, 230, 350, 547, 105 with the same keys as T-025. The three plain ones also have `align = "left"` and `box = [2, 0, 110, 32]` (old text started at x = 2 or 3). All 17 px.
- **T-028** not fixed. Needs an in-game check of whether しおり and セーブ are shown in the same menu. 401 stays "Save" (D-029).
- **T-029** partly fixed. 342: `font = "SemiBold"`, `max_size = 16`, `style = "shadow"`, `shadow = [1, 1]`, `align = "left"`, `box = [0, 0, 144, 32]` (16 px, left edge at the sprite's left edge, the same place the other rows start in their original sprites). Whether the 144 px sprite is drawn at the same x as the other rows is not known from the files; it needs an in-game check. 402 is a reference block and was not changed (its text starts about 10 px in).
- **T-030** not fixed. 48 and 232 are reference blocks (D-035) and must not change. The wording "Yes/None" versus "On/Off" needs an in-game check of the rows that use these values.
- **T-031** fixed. 16, 122, 319, 285 with the keys of T-025. 154 (Settings plate) got them too because it is the same plate family. All 17 px. Wording: no action.
- **T-032** fixed. 68 Settings and 542 Observe: `max_size = 15`, `squeeze = 0.7`; both 15 px (was 12.4). The alternatives "Setup" and "Look" were not needed.
- **T-033** fixed, with a change. All 20: `max_size = 18`, `squeeze = 0.8`, `fill = "#ffffff"`, `outline = ["#0b537a", "#0b537a"]`, `rings = 2` (not 1: the original art has a 2 px dark-blue outline, and one ring looked thin). Yes and No are both 18 px; Pattern and Scroll 18; Delete 18 at squeeze 0.8. 68 and 542 stay at 15 (T-032).
- **T-034** not needed ("Memo" kept).
- **T-035** fixed. All seven: `max_size = 22`, `squeeze = 0.8`, `rings = 1`, plus `style = "outline"`, `outline = ["#1c739c"]`, `fill = "#ffffff"` (Sat had a shadow, the others none) and `box = [1, 0, 40, 48]` (the kanji outline reaches x = 1 and x = 39 and left stray lines with a narrower box). Sizes: Wed 19.5, Mon 21, Thu, Sun, Tue, Sat and Fri 22.
- **T-036** not needed.
- **T-037** not fixed (hand-made override, needs an artist).
- **T-038** not fixed (override, needs an artist).
- **T-039** not fixed (override 215; the toml block exists).
- **T-040** not fixed (overrides 223, 336, 311, 418). Their toml blocks were left as they were. See the new problem about their boxes.
- **T-041** not fixed (overrides 180, 292, 128). The toml blocks of the other seven names in T-024 are done.
- **T-042** see T-014 (fixed, check in game) and T-029 (check in game).
- **T-043** not fixed (the number sprite is separate).

### New problems noticed

1. The toml blocks of the four overridden map plates (223, 336 Infirmary; 311, 418 Schoolyard) erase part of the plate outline at the left and bottom when drawn (they would show 10 to 13 px text). If one of the overrides is ever removed, their boxes must be fixed first (same method as 119: box inside the plate face).
2. `redraw.py`: with `x_min` or `x_max` and the default alignment ("old-text"), the English is placed too far right (186 "Other" moved about 12 px). `align = "centre"` avoids it. The cause was not investigated.
3. A `commonest` box that touches the picture frame erases the frame (seen on the hint banners, rows 0 to 3 and 28 to 31). Keep boxes inside the face.
4. The weekday and topic pictures need the box to cover the old outline completely (x = 1 and 39 of 40, x = 94 of 96), or a stray line stays.
5. 453 (map overview, override) is still flagged by the preview ("background differs left/right"); unchanged.
6. 347 now uses leading spaces in the English text to centre "UP!!". If a tool trims the text, the line goes back to the left.
7. Several name plates (Hoshino 14.5, Kuryuu 13.5) and the long area tags (Music Room, Science Lab 14.5) are still below 16 px; a wider sprite would be needed to raise them.
