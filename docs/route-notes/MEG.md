# MEG route notes (decisions to keep consistent)

Scenes done by this agent: MEG_DEA, MEG_MKI, MEG_GKE, MEG_KBE, MEG_MST, MEG_MAT, MEG_MED, MEG_TEL, MEG_TEN, MEG_TFO, MEG_DAT_A, MEG_GKD_A, MEG_KOK_A.

## Decisions
- Megumu to the player: "{Nm}" (bare, often a vocative after a comma: "See you, {Nm}."); the player to her: "Kuryuu". She says "Dad" / "Mom" (父さん / 母さん) and "Roji" (her kitten).
- The gag: the player/everyone reads 恵 as "Megumi"; she answers "It's not Megumi, it's Megumu!" (MEG_DEA). Ruby on 恵 is always dropped.
- Voice: stern, crisp, rule-quoting, no slang; laughs フフッ -> "Hehe", クスクス -> "Hehe"; ええ -> "Yes." (or "Yes, I guess so."); じゃあね / またね -> "See you." (bad-end farewell さよなら -> "Goodbye."); おはよう -> "Good morning, {Nm}!"
- Stammer used for her う/え/そ/ち/ど repeats: "Y-yes", "W-why", "S-see you", "R-right", "T-then", "P-patrol"; the player's ご、ごめん -> "S-sorry", そ、そっか -> "R-right."
- 風紀委員 -> "Discipline Committee" (she says "I'm on the Discipline Committee"); 校則 -> "the school rules"; 寄り道 -> "detour"; 見回り -> "patrol" (running gag in MEG_GKD_A: "It's not a detour, it's a patrol!").
- 不純異性交遊 (her phrase for dating in school) -> "improper boy-girl fraternizing" in all bad-end scenes (MEG_KBE, MEG_TFO).
- Bad-end phrasing, keep identical in both scenes: "I told you there'd be no second time", "Were you flaunting her in front of me?!", "I thought better of you!", "Goodbye! Don't ever come near me again!", "Try to keep your dating wholesome", "Haah... what an idiot", "Meek and quiet, gentle and kind, so girlish... To a boy, she's the ideal".
- Rivals as she names them (bare): Hoshino, "The Year 1 girl, Satonaka", Mizusawa (no senpai), Sakino, Futami, Shijou ("a young lady").
- Pool/dojo scenes: 道場 -> "dojo", 柔道 -> "judo"; 稽古 -> "training"; 受け身 -> "breakfalls"; 有段者 -> "black belt"; 参った -> "I yield" (ギブ -> "I give!" by the player).
- Place names: 丘の上公園 -> "Hilltop Park"; 路地裏 -> "back alley"; 駅前 -> "in front of the station"; 校門 -> "the school gate"; ゲームセンター -> "game center"; クレーンゲーム -> "crane game".
- Roji named for 路地: the pun is carried by "Since I found you in the back alley, your name is Roji".
- Cat sound -> "Meeeow"; throw sounds -> "Thud!" / "Wham!"; footsteps -> "Pitter-patter-patter...".
- Stray SYS line ひとつしか無いですよ appears in MEG_DEA:72 and MEG_DAT_A:163 -> "There's only one, you know." (meaning unknown; probably a hidden message).
- Dev jokes MEG_GKE:25 ("A mirror match?! Impossible!") and MEG_MAT:60/82 ("That's not fair, TT Fuck!! MAT") are literal.
- Narration in MEG_KOK_A:180-192 is Megumu's own first-person epilogue; her quoted words get double quotes inside the narration.
- Time-skip narration: "...And so, ..." (こうして、...). Silent lines "......" are kept (checker WARN NO_LETTERS, harmless).
- Waits inside words ({W1}-{W8} splits) were spread between English words; the checker counts every wait, so clusters like {W3}{W3} appear at line ends.

## Glossary proposals
- 登校 -> "going to school" is forced by the checker and reads badly in "got to school safely" (MEG_DEA:71); suggest adding variant "got to school" / "come to school".
- ドキドキ = "heartbeat" is a dev label; in dialogue "my heart pounds" is natural and triggers a WARN (MEG_GKD_A:272, 274, 275).
- Add 丘の上公園 = Hilltop Park, 見回り = patrol, 寄り道 = detour, 不純異性交遊 = improper boy-girl fraternizing, 稽古 = training, 電車通学 = commute by train, 稽古/受け身 = breakfalls.
