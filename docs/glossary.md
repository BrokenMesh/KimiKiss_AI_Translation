# KimiKiss translation glossary (DRAFT, needs approval)

Phase 5, step 1 of `kimikiss-translation-plan.md`. Nothing in bulk translation starts until the items marked **DECIDE** are answered. Machine-readable twin: `tools/translate/glossary.json` (same entries; `approved: false`; entries that depend on an open decision carry `depends_on`).

How to answer: reply with the decision ids and "yes" (take the recommendation) or the alternative, for example "D1 yes, D2 drop long vowels, D3 yes". Counts are occurrences in `text/*.json` after removing `{..}` codes and `／`; the number in brackets is the count over unique line texts (shared files repeat lines across routes). The text has 36,172 records.

## 0. Decision checklist

| id | question | recommendation |
|---|---|---|
| D1 | Name order | Japanese order, "Sakino Asuka" |
| D2 | Romanization of long vowels | Write the kana: Shijou, Yuumi, Kuryuu, Kouichi (anime/MAL spelling). Alternative: drop them (Shijo, Yumi, Kuryu, Koichi) |
| D3 | Honorifics | Keep -san/-kun/-chan/-senpai/-sensei, hyphenated |
| D4 | Megumu or Megumi | Megumu, keep the "it is Megumu" gag |
| D5 | Special address forms | Master, Mao-nee, Senpai, Onii-chan, Tomo-chan |
| D6 | Sound effects, laughs, tilde | Translate to English interjections; tilde mostly dropped |
| D7 | Ellipsis, stammer, quotes | "..." ellipsis, "S-sorry" stammer, "..." quotes for speech, (...) for thoughts |
| D8 | School and game terms | school festival, Topic Bag, Discipline Committee, Year 1-3 |
| D9 | Speaker plates | Surnames; raise indent 4 to 5 cells; MIC plate "Michi" |
| D10 | Credits and dev-memo lines | Romanize credits; dev memos low priority |
| D11 | Tone sheet per heroine (section 1) | As tabled |

## 1. Policy

| id | topic | recommendation | alternatives | evidence |
|---|---|---|---|---|
| D1 **DECIDE** | Name order | **Family-given** everywhere a full name is printed ("Futami Eriko", "Satonaka Narumi"). The seven name plates in `labels.tsv` (entries 72, 128, 180, 233, 292, 487, 539) are already family-given and the name-entry screen is surname first ({Nm} then {Nn}). Spoken address is nearly always surname+honorific or a bare given name, so order rarely shows. | Given-family ("Asuka Sakino", as Wikipedia and the anime subtitles do): then the 7 plate textures must be redrawn and the name-entry field order becomes odd. | Surname+san appears 2,432 times; a full name only in introductions (ASU_DEA:126, ERI_DEA:34, MIT_DEA:77, NAR_DEA:61, MEG_DEA:46-47). |
| D2 **DECIDE** | Romanization rule | **Hepburn, ASCII only, long vowels spelled as the kana: おう/おお -> ou/oo, うう -> uu, えい -> ei.** Results: Shijou, Yuumi, Kuryuu, Kouichi; names without a long vowel stay Mao, Eriko, Narumi, Asuka, Nana. No macrons, because the English font is ASCII only (D-012). Same spelling as the English anime database (Yuumi Hoshino, Mitsuki Shijou, Megumi Kuryuu, Kouichi Sanada). | (a) Drop long vowels: Shijo, Yumi, Kuryu, Koichi (matches the current default "Koichi", D-016; shorter; "Yumi" is plain English-readable). (b) Macrons as on English Wikipedia (Shijō): needs new glyphs in the free font rows 11-12. | Rubies in text: しじょう, ゆうみ, くりゅう. Wikipedia en: Shijō Mitsuki, Yūmi Hoshino, Kuryū Megumi. Manga volume title "Mitsuki Shijyo" shows publishers vary. |
| D3 **DECIDE** | Honorifics | **Keep and hyphenate:** -san, -kun, -chan, -senpai, -sensei, -nee (姉ちゃん), Onii-chan. Where the Japanese has a bare name, use a bare name. The honorific carries the relationship (Narumi's "Senpai", Asuka's "-kun" vs Eriko's bare surname). | (a) Localize ("Miss Sakino", "Big Sis Mao", "Teacher"); loses the characterisation and 2,432 + 1,906 occurrences need rephrasing. (b) Keep only -chan/-senpai/-sensei, drop -san/-kun: shortest, but Mitsuki's "-san" vs Eriko's bare surname disappears. | Counts: surname+さん 2,432; ちゃん 1,906; 君 991 (892 as {Nm}君); 先輩 797; 先生 314. -san costs 4 bytes, so budget is not a driver. |
| D4 **DECIDE** | Megumi / Megumu | **Kuryuu Megumu**, and translate the gag as written: the player reads her name as Megumi, she answers "It's Megumu, not Megumi!" (MEG_DEA:46-67, MEG_KIS_A:37). | Megumi (Wikipedia, anime) and flatten the gag. | Ruby on 恵 is めぐむ in her own line (MEG_DEA:47); the ja.wikipedia entry says she calls herself めぐむ because she dislikes the registered めぐみ. `labels.tsv` entry 72 currently says "Kuriu Megumi": wrong on both words. |
| D5 **DECIDE** | Special address forms | ご主人様 -> **Master** (Mitsuki, 201 of 242 uses); 摩央姉ちゃん -> **Mao-nee** (627 uses by the player); Narumi's 先輩 -> **Senpai**; お兄ちゃん -> **Onii-chan** (Nana, 375); トモちゃん -> **Tomo-chan** (Mao's nickname for Kawada, who objects); Eriko and Hiiragi call the player by bare {Nm}; Mao by bare {Nn} (264). | Master -> "my lord" / "Sir"; Mao-nee -> "big sis Mao"; Senpai -> "upperclassman"/"{Nm}" ; Onii-chan -> "big brother". | `{Nm}`/`{Nn}` are patched slots (8 + 8 characters, D-016), so bare names are cheap. |
| D6 **DECIDE** | Sound effects, laughs, tilde | **Translate to English interjections** (table below); romanized Japanese SFX only for the two signature ones, "Ehehe" and "Fufu". Narration onomatopoeia becomes English words (Thud, Crash). Tilde ～ (3,874 uses): drop by default, keep a trailing "~" only for Mao, Nana and Narumi when the line is playful; stretch a vowel ("Sooo") only for emphasis. | (a) Romanized SFX throughout (Fufu, Kusu, Doki-doki). (b) Action tags such as *giggle* (line budget suffers). | フフ(ッ) 633 uses, エヘヘ 231, クスッ 207. |
| D7 **DECIDE** | Ellipsis, stammer, quotes | **Ellipsis:** "..." for … (15,627 uses) and "......" for …… (824). **Stammer:** initial letter + hyphen, one repeat ("S-sorry", "I-it's"), only where the Japanese has そ、そんな style repeats (about 1,800 lines, PLY and YUM most). **Speech** in straight double quotes (「」 -> "..."), **thoughts** in parentheses as in the Japanese (（） -> (...)), narration bare. Keep ?! and !? as "?!"; never stack more than two marks. {W..} waits and voice codes stay where the text allows. | (a) Use a real ellipsis glyph from the free font rows (font work). (b) Drop quote marks and rely on the plate. | The `{W n}` splits inside words (`見{W2}る{W2}か{W2}ら`) are voice timing, not stammering; do not render them as hyphens. |
| D8 **DECIDE** | School and game terms | **school festival** (already in the hint banner texture), **Topic Bag** (labels entry 319; not "deck"), **Discipline Committee** (風紀委員), **Library Committee**, **Year 1/2/3** and **Class 2-A** (2年A組), **Infirmary**, **Schoolyard**, **Gym**. Tab texts stay as in `labels.tsv`; prose may use the longer natural phrase ("behind the school" for 校舎裏 which is "Back Lot" on the tab). | "culture festival"; "Topic Deck"; "Public Morals Committee"; "first-year/second-year/third-year". | See section 3. |
| D9 **DECIDE** | Speaker plates | **Surname plates as in the original** (Nana = given name, like the original 菜　々). Width measured with `tools/font/en_widths.json`: Hoshino 86 px, Kawada 86, Futami 73, Sakino 72, Shijou 65, Kuryuu 76, Hiiragi 70, Nana 56, Hiba 49, Yuzuki 73, but **Mizusawa 107, Satonaka 100, Kirishima 100, Kobayakawa 138**. The indent after the plate is 92 px. Recommend raising `putIndent:` from 4 to 5 cells (115 px, one operand byte in `Parson>>message:`, see `docs/phase-4-name-entry.md`) and using **Michi** for MIC. | Keep 92 px and use given names on all plates (Mao, Narumi, Yuumi...), which hides the surname the player is not on first-name terms with; or abbreviate (Mizusawa -> Mizu.). | Plates are the K2_Script labels `星　乃`, `里　仲`, `水　〆`... (section 2). EX1/EX2/ETC plates need a look in the emulator. |
| D10 **DECIDE** | Credits and dev memos | **Credits** (`StaffRoll` 146 rows + about 70 rows in `GUN_PRO`): romanize as printed, Family-Given, Hepburn without macrons, translate role words; voice actors use the names they publish under (Koshimizu Ami, Mizuhashi Kaori, Ikezawa Haruna, Hirohashi Ryou, Tanaka Rie, Noto Mamiko, Nogawa Sakura, Nakahara Mai, Kawasumi Ayako, Fukuyama Jun, Harada Hitomi). **Dev memos** (about 35 lines in MAO_PRO, ERI_PRO, YUM_KIS_A, ASU_PRO, NAR_KIS_A such as "LV2 kiss, all outfits, with or without mob") are not story text: translate literally, last priority. | Leave credits in Japanese; ask you for staff romanizations. | Credits contain misprints (水〆 for 水澤, 池〆 for 池澤, 明日香 for 明日夏): normalise to the real names. Kanji-only staff names can have several readings; unsure ones are flagged in the translation file. |
| D11 **DECIDE** | Tone per heroine | See table below. | Neutral register for all. | Counts from the speaker lines. |

### Tone per speaker (D11)

| speaker | evidence in Japanese | English voice |
|---|---|---|
| YUM Yuumi | ええ 279, うん 308, わね 68, ellipses 1,514, stammer pattern 186 | Soft, hesitant, polite but not stiff; many "..."; "Yes", "Mm"; laugh "Fufu". |
| NAR Narumi | です 1,353, ます 364, ～ 871, エヘヘ 143; calls player Senpai | Bubbly kouhai, always polite ("Senpai, it's ready!"), exclamations, "Ehehe", tilde allowed. |
| MAO Mao | わよ 290, のよ 235, ～ 663, フフ 187; teasing | Confident older-sister banter, teasing, "Mao Check #N" lines; "Fufu"; tilde allowed. |
| ASU Asuka | だよ 149, よね 170, うん 443, ellipses 1,205, あはは 81 | Casual tomboy, contractions, sports slang, "Ahaha", "Ehehe"; never prim. |
| ERI Eriko | わよ 194, わね 107, のよ 101, あなた 30, クスッ 126 | Dry, precise, deadpan; short sentences; no contractions in the cold lines; "Heh." |
| MIT Mitsuki | です 1,066, ます 474, ませ 225, ご主人様 | Formal, courteous, no contractions, gentle humor; "Master"; "Fufu". |
| MEG Megumu | わよ 65, のよ 52, お前 (to the kitten and offenders) | Stern, crisp, rule-quoting, fierce when "Megumi" is said; tomboyish pride. |
| NAN Nana | だよ 78, ～ 595, エヘヘ 54, お兄ちゃん 375 | Cheerful little sister, childish rhythm, "Onii-chan", "Ehehe", tilde allowed. |
| TOM Kawada | わよ 22, のよ 23, フフ 22 | Warm older-woman teacher, light teasing, "Fufu". |
| AKI Hiiragi | 俺 13, だろ 25, ぞ 17 | Casual guy, dry advice; no honorifics. |
| GUN Gunpei | わし, ええがな (Kansai/Sanuki flavor) | Gruff old shopkeeper; at most "ya", "gonna"; not heavy dialect. |
| PLY player | 僕 804, だよ 845, ellipses 8,335 | Ordinary boy, mild self-deprecation; thoughts in (...). |

### Sound effects and interjections (D6)

| JA | who | EN (proposed) | note |
|---|---|---|---|
| フフッ / フフ | all heroines, TOM | Hehe (tomboys, Nana, Narumi) / Fufu (Yumi, Mitsuki, Eriko, Mao, Kawada) | soft laugh; see tone table (D11) |
| エヘヘ | NAR 143, NAN 54, ASU 31 | Ehehe | embarrassed giggle; keep romanized, reads naturally |
| クスッ / クスクス | ERI, YUM, MIT | Heh. / Hehe... | quiet laugh; drop if the line is tight |
| あはは | ASU 81, MAO, NAN | Ahaha | open laugh |
| えっ / あっ / わっ / ええっ | all | Eh? / Ah! / Wah! / Eeh?! | startle; keep short |
| う～ん / え～と / えっと | all | Hmm... / Let's see... / Um... | thinking sounds |
| ドキドキ / ワクワク | SYS, PLY | (heart) pounding / excited | as adverb in narration: 'my heart pounded' |
| ビックリ / びっくり | SYS, PLY | startled / surprised |  |
| あわわ | PLY, ASU | Eep! / Whoa... | panic |
| ガウ！ | SYS (MIT_SEV_A:322-328) | Grrr! Woof! | dog barking (Mitsuki's dog Ringo, リンゴ) |
| ゾウさんパオーン！ | PLY (MIT_MW2_A:717-723) | Elephant go paooon! | a children's elephant game; keep the sound, translate ゾウさん |
| ドタバタ…ドスン！ガタガタ…パリ～ン！ | SYS (NAR_GKD_B) | Thump-thump... Thud! Rattle... Crash! | translate to English onomatopoeia |

## 2. Characters

Speaker codes are the `speaker` field of `text/*.json`. Totals: 34,517 lines with a plain code, 25 joint lines (`ERI/PLY`, `MAO/PLY`, ... written `A/B`; translate with the first-listed speaker's plate), 1,630 without a speaker (1,189 are system tables, the rest choice lists and labels). The route code is the file prefix (MAO ASU ERI NAR MIT YUM MEG NAN PLY ALL GUN, plus `system`). `PLY_*` files are shared event scenes, `ALL_*` shared encounters, `GUN_PRO` the joke prologue plus the credits.

| code | lines | kanji | reading | EN | role | plate |
|---|---:|---|---|---|---|---|
| `PLY` | 14846 | 相原 光一 (default) | あいはら こういち | {Nm} {Nn} (default Aihara Kouichi) | Player character: thoughts （…） and speech 「…」 share the code | {Nm} |
| `SYS` | 997 | (narration) |  |  | Narration, no plate |  |
| `ASU` | 2762 | 咲野 明日夏 | さきの あすか | Sakino Asuka | Heroine, 2-C, plays on the boys' soccer team | Sakino |
| `NAR` | 2708 | 里仲 なるみ | さとなか なるみ | Satonaka Narumi | Heroine, 1-A, Nana's classmate, udon-shop granddaughter, Udon/Home Ec clubs | Satonaka |
| `ERI` | 2698 | 二見 瑛理子 | ふたみ えりこ | Futami Eriko | Heroine, 2-B, IQ-190 loner of the science lab | Futami |
| `MIT` | 2674 | 祇条 深月 | しじょう みつき | Shijou Mitsuki | Heroine, 2-B, heiress; calls the player ご主人様 | Shijou |
| `MAO` | 2662 | 水澤 摩央 | みずさわ まお | Mizusawa Mao | Heroine, 3rd-year older childhood friend ('Mao-nee'); the font prints 水〆 | Mizusawa |
| `YUM` | 2359 | 星乃 結美 | ほしの ゆうみ | Hoshino Yuumi | Heroine, 2-A, shy Library Committee member | Hoshino |
| `NAN` | 1224 | 相原 菜々 | あいはら なな | {Nm} Nana | Player's little sister, 1-A; unlockable route NAN; family name follows the player's {Nm} | Nana |
| `MEG` | 859 | 栗生 恵 | くりゅう めぐむ | Kuryuu Megumu | Heroine (unlocked later), 2-A, Discipline Committee, judo dojo; insists on めぐむ | Kuryuu |
| `TOM` | 295 | 川田 知子 | かわだ ともこ | Kawada Tomoko | Modern-Japanese teacher, Swim Club adviser; Mao calls her トモちゃん | Kawada |
| `AKI` | 271 | 柊 明良 | ひいらぎ あきら | Hiiragi Akira | Player's best friend and adviser, 2-A | Hiiragi |
| `KAO` | 43 | 夕月 薫子 | ゆづき かおるこ | Yuzuki Kaoruko | Narumi's friend, 1-B, udon club; Narumi: るっこちゃん | Yuzuki |
| `MAN` | 37 | 飛羽 愛美 | ひば まなみ | Hiba Manami | Narumi's friend, 1-C, udon club; Narumi: まなちゃん | Hiba |
| `GUN` | 10 | 里仲 軍平 | さとなか ぐんぺい | Satonaka Gunpei | Narumi's grandfather, owner of 里なか; 10 lines incl. the 鬼兵 drill-sergeant gag | Gunpei |
| `MIC` | 5 | 小早川 美千 | こばやかわ みち | Kobayakawa Michi | First-year girl who adores Asuka (5 lines; name only in credits and plate) | Michi |
| `KEI` | 5 | 霧島 敬子 | きりしま けいこ | Kirishima Keiko | Guidance officer (補導員), 5 lines | Officer |
| `ETB` | 30 | 男子 |  | Boy | Male student extras (plate 男　子) | Boy |
| `ETG` | 10 | 女子 |  | Girl | Female student extras (plate 女　子) | Girl |
| `ETC` | 9 | ？？？ |  | ??? | Unnamed speaker: ramen/udon cooks, shop staff (plate ？？？) | ??? |
| `EX1` | 7 | 特殊１ |  | CHECK in game | Special extra 1 (Mao's friends, soccer teammates); plate 特殊１ probably blank | ? |
| `EX2` | 6 | 特殊２ |  | CHECK in game | Special extra 2 (same pool) | ? |

**Name forms found in the text.** Readings in bold are spelled in the text (ruby `{R}kanji{Rn}kana`, 13 pairs): 栗生**くりゅう**, 恵**めぐむ**(and the misreading めぐみ), 里仲**さとなか**, 咲野**さきの**, 明日夏**あすか**, 二見**ふたみ**, 瑛理子**えりこ**, 祇条**しじょう**, 深月**みつき**, 柊**ひいらぎ**, 明良**あきら**, 星乃**ほしの**, 結美**ゆうみ**. All other readings are from ja.wikipedia (section 5): みずさわ まお, かわだ ともこ, ゆづき かおるこ, ひば まなみ, さとなか ぐんぺい, こばやかわ みち, きりしま けいこ. In the text Mao's surname is always printed **水〆** (37 uses, never 水澤): the font lacks 澤, so 〆 is a stand-in; the credits do the same for the actress (池〆 for 池澤). Translate every 水〆 as Mizusawa. The game also prints the title as 『キミキスＰＬＵＳ』 (this disc) and 『キミキス』 (the original, for carry-over).

### Who calls whom (D3, D5)

| speaker | calls the player | the player calls them | others |
|---|---|---|---|
| YUM | {Nm}君 341 | 星乃さん 499 | Hiiragi: 星乃さん |
| NAR | 先輩 766, {Nm}先輩 183 | なるみちゃん 538 | Nana: なるちゃん 44; Kawada 里仲さん |
| MAO | {Nn} bare 264, あなた 13 | 摩央姉ちゃん 627 (Mao herself: まおね〜ちゃん) | Kawada, Asuka, Megumu: 水〆さん; Mao calls Kawada トモちゃん |
| ASU | {Nm}君 383 | 咲野さん ~430 | Narumi: 明日夏先輩 11; Michi: 明日夏先輩 |
| ERI | {Nm} bare 196, あなた 30 | 二見さん ~460 | classmates: 瑛理ちゃん; her mother: えりちゃん; Eriko calls Hiiragi 柊 |
| MIT | {Nm}さん 260, ご主人様 in 201 lines, あなた 59 | 祇条さん ~450 | she asks the player to call her 深月 (MIT_SEV_B:184) |
| MEG | {Nm}君 120, あなた 27 | 栗生さん ~140 | Narumi: 栗生先輩 |
| NAN | お兄ちゃん 375 | 菜々 (bare) ~306 | Narumi and Mao: 菜々ちゃん 71 |
| TOM | {Nm}君 48, あなた 16 | 川田先生 107 | Mao: トモちゃん; Kawada asks to be called 知子 in a free event (PLY_FEV:502-505) |
| AKI | {Nm} bare 40, 君 21 | 柊 bare ~47 | - |
| KAO / MAN | お前 / おまえ (rare) | - | Narumi: るっこちゃん / まなちゃん |

### Name forms table

| JA | EN (proposed) | n (unique) | labels.tsv | note |
|---|---|---:|---|---|
| 摩央 | Mao | 667 (578) |  | given name; player says 摩央姉ちゃん |
| 二見 | Futami | 623 (481) |  | ruby ふたみ |
| 星乃 | Hoshino | 603 (521) |  | Yumi's family name; K2 plate 星　乃 |
| なるみ | Narumi | 593 (497) |  | given name; usually なるみちゃん |
| 祇条 | Shijou | 565 (472) |  | ruby しじょう; labels.tsv entry 233 says 'Gijo' (wrong reading) |
| 咲野 | Sakino | 535 (448) |  | ruby さきの |
| 菜々 | Nana | 444 (400) | Nana | little sister; family name is the player's surname {Nm} |
| 栗生 | Kuryuu | 178 (152) |  | ruby くりゅう; labels.tsv entry 72 says 'Kuriu' |
| 川田 | Kawada | 136 (120) |  | teacher; reading かわだ from ja.wikipedia (no ruby in text) |
| 柊 | Hiiragi | 82 (74) |  | ruby ひいらぎ; called bare 柊 by the player and Eriko |
| 水〆 | Mizusawa | 37 (35) |  | in-game spelling of 水澤 (〆 stands in for the missing glyph) |
| 瑛理 | Eri | 35 (33) |  | short form: 瑛理ちゃん (classmates), えりちゃん (her mother) |
| 深月 | Mitsuki | 33 (28) |  | given name, ruby みつき; labels.tsv says 'Mizuki' (wrong) |
| 瑛理子 | Eriko | 31 (29) |  | given name, ruby えりこ |
| 明日夏 | Asuka | 30 (30) |  | given name, ruby あすか (credits misprint 明日香) |
| 里仲 | Satonaka | 26 (22) |  | Narumi's and Gunpei's family name; ruby さとなか (shop 里なか is the same name) |
| 結美 | Yuumi | 22 (22) |  | given name, ruby ゆうみ (YUM_DEA); written 'Yumi' in labels.tsv entry 539 |
| 愛美 | Manami | 8 (5) |  | nickname まなちゃん (Mana-chan) used by Narumi |
| めぐみ | Megumi | 7 (7) |  | the misreading everyone makes; keep as the gag (D4) |
| 明良 | Akira | 6 (6) |  | given name, ruby あきら |
| 知子 | Tomoko | 5 (5) |  | Kawada's given name; Mao calls her トモちゃん |
| 夕月 | Yuzuki | 5 (3) |  | ゆづき from public sources (ja.wikipedia); not spelled in text |
| 薫子 | Kaoruko | 5 (3) |  | nickname るっこ (Rukko) used by Narumi |
| 飛羽 | Hiba | 5 (3) |  | ひば from public sources; not spelled in text |
| めぐむ | Megumu | 3 (3) |  | her own reading (MEG_DEA:47, MEG_KIS_A:37); labels.tsv entry 72 says 'Megumi' |
| 軍平 | Gunpei | 3 (3) |  | Narumi's grandfather, owner of Satonaka udon shop |
| 小早川 | Kobayakawa | 3 (3) |  | Asuka's underclass admirer (speaker MIC) |
| 栗生恵 | Kuryuu Megumu | 2 (2) |  | full name; 恵 alone is also in 知恵の輪, so only the full name is a checkable key |
| 美千 | Michi | 2 (2) |  | given name from credits |
| 霧島 | Kirishima | 2 (2) |  | guidance officer (speaker KEI), credits only |
| 敬子 | Keiko | 2 (2) |  | given name from credits |
| 鬼兵 | Onihei | 1 (1) |  | joke persona in GUN_PRO (鬼兵先任伍長, a drill-sergeant gag) |
| 相原 | Aihara | 1 (1) |  | default player surname = {Nm} (D-016) |
| 光一 | Kouichi | 1 (1) |  | default player given name = {Nn} |
| 水澤 | Mizusawa | 0 (0) |  | font has no 澤: the game prints 水〆 (see 水〆) |

## 3. Places, school terms and game terms

### Places

| JA | EN (proposed) | n (unique) | labels.tsv | note |
|---|---|---:|---|---|
| プール | Pool | 138 (123) | Pool | labels: Pool |
| 教室 | classroom | 116 (113) |  |  |
| 図書室 | Library | 83 (81) | Library | labels: Library |
| 校門 | School Gate | 75 (61) |  |  |
| 商店街 | shopping street | 60 (55) |  | Narumi's shop and most date meeting points are here |
| 屋上 | Rooftop | 59 (49) | Rooftop | labels: Rooftop |
| 公園 | park | 55 (55) |  |  |
| 駅前 | in front of the station | 52 (42) |  |  |
| 輝日南 | Kibina | 43 (34) |  | town / school prefix |
| 校舎裏 | behind the school | 42 (39) | Back Lot | labels: Back Lot (REVIEW); prose can be 'behind the school' |
| 保健室 | Infirmary | 37 (37) | Infirmary | nurse's office; labels: Infirmary |
| 理科準備室 | Science Prep Room | 36 (36) |  | labels: Prep Room (location panel) |
| テラス | Terrace | 35 (32) | Terrace | labels: Terrace |
| 校庭 | Schoolyard | 34 (30) | Schoolyard | labels: Schoolyard |
| 河原 | riverbank | 34 (30) |  | Asuka's practice spot |
| 廊下 | hallway | 33 (32) |  | labels: Year N Hall |
| 食堂 | Cafeteria | 30 (28) | Cafeteria | labels: Cafeteria |
| 輝日南高校 | Kibina High School | 29 (24) |  | school name; 輝日南 = きびな (ja.wikipedia) |
| 家庭科室 | Home Ec Room | 29 (28) | Home Ec | labels: Home Ec |
| 音楽室 | Music Room | 28 (27) | Music Room | labels: Music Room |
| 噴水 | Fountain | 25 (24) | Fountain | labels: Fountain |
| 体育館 | Gym | 24 (24) | Gym | labels: Gym (Gymnasium is too wide) |
| 本屋 | bookstore | 24 (23) |  |  |
| 理科室 | Science Lab | 22 (22) | Science Lab | labels: Science Lab |
| 輝日東商業 | Kibito Commercial High School | 21 (14) |  | rival soccer opponent; 輝日東 = きびと |
| 職員室 | Staff Room | 19 (11) |  |  |
| ゲームセンター | game center | 19 (19) |  | guidance officers patrol it |
| デパート | department store | 19 (18) |  |  |
| 遊園地 | amusement park | 17 (17) |  |  |
| きびな池 | Kibina Pond | 14 (13) |  | date spot |
| 里なか | Satonaka | 12 (10) |  | Sanuki udon shop run by Narumi's grandfather |
| 並木道 | tree-lined path | 11 (10) |  |  |
| 路地裏 | back alley | 10 (10) |  |  |
| 花壇 | Garden | 9 (9) | Garden | labels: Garden (REVIEW); literally flower bed |
| 下駄箱 | shoe lockers | 9 (9) |  |  |
| 更衣室 | Locker Room | 9 (8) |  |  |
| 渡り廊下 | Walkway | 5 (4) | Walkway | labels: Walkway |

### School terms and game terms

| JA | EN (proposed) | n (unique) | labels.tsv | note |
|---|---|---:|---|---|
| 先輩 | senpai | 797 (660) |  | Narumi's address for the player |
| 先生 | sensei | 314 (287) | Teacher | labels topic: Teacher |
| キス | kiss | 308 (230) |  | title word; LV1/2/3 kiss events |
| ご主人様 | Master | 242 (171) |  | Mitsuki's address for the player (242 uses, 201 lines spoken by MIT; the player and Nana quote it); alt 'my lord' |
| 水着 | swimsuit | 163 (153) | Swimsuit | labels: Swimsuit |
| 主人公 | protagonist | 116 (68) |  | dev label; = the player character |
| 学園祭 | school festival | 113 (89) |  | labels hint banner: 'school festival' (alt: culture festival) |
| 放課後 | after school | 110 (91) | After School | labels: After School (period tab) |
| 制服 | uniform | 91 (81) | Uniform | labels: Uniform |
| 転校 | transfer | 90 (74) | Transfer | labels topic: Transfer |
| 週末 | weekend | 84 (67) |  |  |
| 部活 | club activities | 81 (76) | Clubs | labels: Clubs |
| サッカー部 | soccer club | 76 (61) |  | Asuka is in the boys' team |
| 校則 | school rules | 74 (70) | Rules | labels: Rules |
| 受験 | entrance exams | 65 (62) | Exams | labels topic: Exams |
| 体操服 | gym clothes | 62 (58) |  |  |
| ドキドキ | heartbeat | 60 (57) |  | dev label; as interjection see SFX |
| スクール水着 | school swimsuit | 59 (56) |  |  |
| 夏休み | summer vacation | 48 (45) |  |  |
| 風紀委員 | Discipline Committee | 46 (46) |  | Megumi's post (wiki: school disciplinary group) |
| 図書委員 | Library Committee | 44 (43) |  | Yumi's post |
| デート | date | 44 (41) |  | labels: after-school date, holiday date |
| 昼休み | lunch break | 40 (39) | Lunch | labels tab: Lunch |
| 宿題 | homework | 40 (39) |  |  |
| 水泳部 | Swim Club | 36 (34) |  | Kawada is the adviser |
| お嬢様 | young lady | 33 (29) |  | Mitsuki as a rich heiress |
| ブルマ | bloomers | 32 (28) |  |  |
| 登校 | going to school | 31 (29) |  |  |
| アスカターン | Asuka Turn | 29 (24) |  | Asuka's soccer move she is perfecting |
| 話題 | topic | 27 (26) |  | game system; labels: topic names |
| フリーイベント | Free Event | 27 (27) |  | dev label in EventTable |
| 勉強アレルギー | study allergy | 26 (26) |  | Mao's studying allergy (hives) |
| 告白 | confession | 22 (22) |  |  |
| 婚約者 | fiance | 21 (21) |  | Mitsuki's arranged fiance |
| 出汁 | dashi | 20 (20) |  | broth |
| 知恵の輪 | puzzle ring | 18 (13) |  | Nana's puzzle borrowed from Narumi |
| 休み時間 | break | 16 (16) |  | labels: Break 1 / Break 2 |
| 家庭部 | Home Ec Club | 15 (12) |  | Narumi's club |
| 摩央チェック | Mao Check | 14 (13) |  | Mao's numbered 'rules for girls' (その1..); keep 'Mao Check #N' |
| うどん同好会 | Udon Club | 12 (12) |  | Narumi, Manami, Kaoruko |
| 紙芝居 | kamishibai | 12 (12) |  | picture-card storytelling (Yumi's route) |
| ロジ | Roji | 12 (12) |  | Megumi's stray kitten (found in a 路地 alley, hence the name) |
| 下校 | heading home | 10 (10) |  | labels hint banner: after-school date |
| マッチング会話 | Topic Match | 10 (10) |  | K2_Script scene label (dev); in-game mini-conversation using topics |
| ジンマシン | hives | 9 (9) |  |  |
| 讃岐うどん | Sanuki udon | 9 (7) |  |  |
| リアクション | reaction | 8 (8) |  | dev label |
| デコちゅー | forehead kiss | 8 (8) |  | Nana's 'deco-chu'; alt keep 'deco-chu' |
| 保健体育委員 | Health and PE Committee | 7 (7) |  |  |
| 補習 | remedial lesson | 7 (7) |  |  |
| 赤点 | failing grade | 7 (7) |  |  |
| 現代文 | modern Japanese class | 6 (5) |  | Kawada's subject (現代国語) |
| 話題袋 | Topic Bag | 4 (3) | Topic Bag | labels entry 319: Topic Bag (REVIEW); alt Topic Deck |
| 好感度 | affection | 3 (3) |  | labels hint banner: affection gauge |
| 補導員 | guidance officer | 2 (2) |  | speaker label KEI |
| アタック | Attack | 1 (1) | Attack | labels: Attack |
| テンション | Tension | 1 (1) |  | dev label |
| リンゴ | Ringo | 1 (1) |  | Mitsuki's family dog |

**Topic names.** The 44 topic names in `WadaiTable` (世間話 ... カミカゼ) all have a label in `labels.tsv` and the English already agrees (Small Talk, Clubs, Uniform, Committee, Rules, Teacher, Transfer, Home Study, Grades, Exams, Italian, P.E., Swimming, Sports, Dance, Music, Video, Reading, Shopping, Fashion, Accessories, Makeup, Swimsuit, Meal, Sweets, Drinks, Cooking, Udon, Junk Food, Health, Diet, Body, Love, Private, Naughty, Future, Past, Praise, Gaze, Smile, Act Cool, Hold Hands, Kamikaze). Without a label: ハズレ (WadaiTable 0.0.0, proposed **Miss**) and the six attribute words 平凡 / 真面目 / 活発 / エッチ / 食い道楽 / おしゃれ (proposed **Ordinary / Serious / Lively / Naughty / Foodie / Stylish**; only Naughty and Stylish are labelled). `docs/phase-4-system-text.md` says the topic icons are graphics, so these strings may never be shown.

### Conflicts and checks against `labels.tsv`

| entry | label now | glossary | verdict |
|---|---|---|---|
| 233 祇条 深月 | Gijo Mizuki | **Shijou Mitsuki** | **Wrong reading** (しじょう みつき from ruby). Redraw. |
| 72 栗生 恵 | Kuriu Megumi | **Kuryuu Megumu** | **Wrong** (くりゅう めぐむ). Redraw. D4. |
| 539 星乃 結美 | Hoshino Yumi | Hoshino Yuumi | Only if D2 keeps long vowels. |
| 128 / 180 / 292 / 487 | Futami Eriko, Satonaka Narumi, Mizusawa Mao, Sakino Asuka | same | OK for D1 = family-given. |
| 16 / 429 菜々 | Nana (REVIEW) | Nana | OK; REVIEW can be cleared (her surname is the player's {Nm}). |
| 2 校舎裏 | Back Lot (REVIEW) | tab "Back Lot", prose "behind the school" | Compatible (D8). |
| 117 / 119 / 354 / 481 花壇 | Garden | Garden | Compatible; prose may say "flower bed". |
| 31 / 223 / 333 / 336 保健(室) | Infirmary | Infirmary | OK. |
| 80 / 331 / 472 準備室 | Prep Room | Science Prep Room in prose | Compatible. |
| 28 昼休み | Lunch | lunch break in prose | Compatible. |
| 84 先生 | Teacher | -sensei in prose | Compatible (topic name vs address). |
| 330 委員 | Committee | Discipline / Library Committee | Compatible. |
| 94 / 341 / 395 / 486 / 536 / 41 / 227 hint banners | school festival, affection gauge, favorite topic | same | OK. |
| 86 カミカゼ | Kamikaze (REVIEW) | Kamikaze | Topic name 0.43; keep. |

## 4. Other recurring terms (5 or more occurrences), by frequency

Proper nouns and set expressions are in sections 2 and 3 (names, places, clubs, running gags such as アスカターン 29, 摩央チェック 14, 勉強アレルギー 26, ご主人様 242). This list adds recurring common nouns and loanwords where a single English choice should be fixed. Obvious words that need no ruling (好き, 一緒, 今日...) are left out.

| # | JA | EN (proposed) | n (unique) | note |
|--:|---|---|---:|---|
| 1 | うどん | udon | 234 (210) |  |
| 2 | サッカー | soccer | 222 (193) |  |
| 3 | 海 | the sea | 114 (97) | date destination; beach is fine; 海パン = swim trunks |
| 4 | イタリア | Italy | 75 (68) | Asuka's dream league; also a topic |
| 5 | ラーメン | ramen | 65 (64) |  |
| 6 | ダンス | dance | 61 (51) |  |
| 7 | テレビ | TV | 56 (51) |  |
| 8 | おじいちゃん | Grandpa | 51 (49) | Narumi's name for Gunpei |
| 9 | イタリア語 | Italian | 51 (47) | topic label Italian |
| 10 | お父様 | Father | 45 (38) | Mitsuki; お母様 = Mother; お兄様 appears 0 times |
| 11 | ピアノ | piano | 41 (41) |  |
| 12 | ダイエット | diet | 41 (39) | topic label Diet |
| 13 | ケーキ | cake | 36 (36) |  |
| 14 | 山 | mountain | 36 (31) |  |
| 15 | コーヒー | coffee | 33 (33) |  |
| 16 | カレー | curry | 33 (30) |  |
| 17 | 夕日 | sunset | 33 (28) |  |
| 18 | 跳び箱 | vaulting box | 33 (25) | Narumi/PE scenes |
| 19 | アイス | ice cream | 32 (31) |  |
| 20 | アレルギー | allergy | 29 (29) | also 勉強アレルギー |
| 21 | 映画 | movie | 29 (27) |  |
| 22 | ゴルフ | golf | 28 (28) |  |
| 23 | 麻雀 | mahjong | 27 (27) | mahjong mini-event (K2_Script 81.26) |
| 24 | クラシックバレエ | classical ballet | 27 (26) | Mitsuki's accomplishment |
| 25 | バレーボール | volleyball | 26 (26) |  |
| 26 | チョコ | chocolate | 26 (26) |  |
| 27 | 紅茶 | tea | 24 (24) | black tea |
| 28 | 参考書 | study guide | 23 (23) | reference book |
| 29 | チアガール | cheerleader | 23 (23) |  |
| 30 | 監督 | coach | 23 (20) | Asuka's team; コーチ = coach too (DECIDE-lite: coach vs manager) |
| 31 | 手料理 | home cooking | 22 (18) | topic label Cooking |
| 32 | 屋敷 | mansion | 21 (20) | Mitsuki's house; お屋敷 |
| 33 | 花火 | fireworks | 20 (20) |  |
| 34 | ラブレター | love letter | 20 (20) |  |
| 35 | ママ | Mama | 20 (19) | also パパ = Papa; お母さん / お父さん = Mom / Dad |
| 36 | 洋食 | Western food | 19 (19) |  |
| 37 | テニス | tennis | 19 (19) |  |
| 38 | スナック菓子 | snacks | 19 (19) |  |
| 39 | コンタクト | contact lenses | 19 (19) |  |
| 40 | 弁当 | bento | 18 (16) | lunchbox |
| 41 | 占い | fortune-telling | 18 (15) | Kawada's speciality |
| 42 | ハンバーグ | hamburger steak | 17 (17) |  |
| 43 | コロッケパン | croquette bun | 17 (17) |  |
| 44 | カップラーメン | instant ramen | 17 (17) |  |
| 45 | フランス | France | 16 (16) |  |
| 46 | ジャンクフード | junk food | 15 (15) | topic label Junk Food |
| 47 | 逆上がり | bar flip | 15 (14) | reverse bar swing (sakaagari) |
| 48 | おじさん | uncle | 13 (13) |  |
| 49 | 顧問 | adviser | 13 (11) |  |
| 50 | ディフェンダー | defender | 13 (7) |  |
| 51 | カラオケ | karaoke | 12 (12) |  |
| 52 | 味噌汁 | miso soup | 11 (11) |  |
| 53 | ブランコ | swing | 11 (10) |  |
| 54 | 紙飛行機 | paper airplane | 10 (10) |  |
| 55 | ジョギング | jogging | 10 (10) |  |
| 56 | 柔道 | judo | 10 (9) | Megumi's family dojo |
| 57 | ビーチバレー | beach volleyball | 10 (9) |  |
| 58 | フォークダンス | folk dance | 10 (6) | school festival dance |
| 59 | プレゼント | present | 9 (9) |  |
| 60 | リフティング | juggling | 8 (7) | soccer ball juggling |
| 61 | ピザ | pizza | 7 (7) |  |
| 62 | サンドウィッチ | sandwich | 7 (7) |  |
| 63 | リムジン | limousine | 7 (6) | Mitsuki's ride |
| 64 | ベンチ | bench | 7 (5) |  |
| 65 | 道場 | dojo | 6 (6) |  |
| 66 | ユニフォーム | kit | 6 (6) | soccer kit |
| 67 | マネージャー | manager | 6 (6) | club manager |
| 68 | ハムカツパン | ham cutlet bun | 6 (6) |  |
| 69 | ソフトテニス | soft tennis | 6 (6) |  |
| 70 | キャプテン | captain | 6 (5) |  |
| 71 | ワールドカップ | World Cup | 5 (5) |  |
| 72 | メイド | maid | 5 (5) |  |
| 73 | ソフトボール | softball | 5 (5) | Mitsuki |

## 5. Sources

- ja.wikipedia, キミキス (characters, readings, classes, 輝日南 = きびな, 輝日東 = きびと, Megumu and Tomo-chan notes): https://ja.wikipedia.org/wiki/%E3%82%AD%E3%83%9F%E3%82%AD%E3%82%B9
- en.wikipedia, KimiKiss (macron romanizations Yūmi Hoshino, Mitsuki Shijō, Megumi Kuryū; voice cast): https://en.wikipedia.org/wiki/KimiKiss
- MyAnimeList, KimiKiss Pure Rouge characters (English database spellings Yuumi, Shijou, Kuryuu, Kouichi, Manami Hiba, Kaoruko Yuzuki; licensed English release by Sentai Filmworks per Anime News Network): https://myanimelist.net/anime/2927/KimiKiss_Pure_Rouge/characters
- Anime News Network encyclopedia, release listing: https://animenewsnetwork.com/encyclopedia/releases.php?id=17833
- Limits: I could not read the Sentai subtitle script itself, so "anime subtitle spelling" means the English-language database spellings above. English fan pages disagree on the school name ("Kibina High", from きびな); the game text itself gives きびな池 (Kibina Pond, ERI_GKD_A:219).
- In-game evidence is cited by record id (`file:index`), e.g. `MEG_DEA:47`.
