# YUM route notes (decisions to keep consistent)

Scenes done by this agent: YUM_DEA, YUM_MKI, YUM_GKE, YUM_KBE, YUM_MST, YUM_MAT, YUM_MED, YUM_TEL, YUM_TEN, YUM_TFO, YUM_DAT_A.

## Decisions
- Yuumi to the player: "{Nm}" (bare, vocative, often after a comma: "See you, {Nm}."); the player to her: "Hoshino". Never "Yuumi" in dialogue.
- ええ -> "Yes."; うん -> "Mm." (agreeing/soft) or "Yes."; ううん -> "No," ; うん in reply to a request "Mm."; ごめんなさい -> "I'm sorry." (ごめんね -> "Sorry,").
- Yuumi's laughs: フフッ -> "Fufu"; クスッ -> "Hehe..."; stammer used for her う、うん -> "M-mm", ど、どうして -> "W-why", ご、ごめん -> "S-sorry".
- Library Committee member: 図書委員 -> "Library Committee" ("I'm on the Library Committee"); 図書室 in prose -> "the library".
- Goodbye lines: またね -> "See you." (with "{Nm}" or nothing); さよならっ！ -> "Goodbye!" (breakup scenes).
- Bad-end/rebuke phrasing (YUM_KBE, YUM_TFO, shared across variants): "I had you all wrong", "such an awful person", "I only want to keep the good memories of us...", "If you have a girl like that, you didn't have to be nice to me...", "I can see why you're drawn to her". Keep these exact for the other YUM bad-end scenes.
- The rivals Yuumi names: Narumi (Year 1, cheerful), Mizusawa (Year 3), Sakino (soccer club), Futami (famous genius), Shijou (famous young lady), Kuryuu (Discipline Committee).
- Yuumi is moving away (引っ越し "the move", 転校 "transferring schools"): father transferred in August, house has a buyer, she may stay until the school festival; she asks the player to keep it secret (YUM_DAT_A).
- 着替え -> "change" (clothes). 電車通学 -> "commute to school by train". 職員室 -> "Staff Room". 校門 -> "the school gate". 放課後 -> "after school".
- Phone greeting: "Oh, I'm sorry to call so late at night. This is Hoshino calling, but..." (YUM_TEL). The player answers "Hello, this is {Nm}."
- Choices with echoed player lines: the echo repeats the choice wording exactly (YUM_DEA, YUM_MST, YUM_DAT_A).
- Time-skip narration: "...And so, ..." (こうして、...). Silence lines "......" are kept (checker WARN NO_LETTERS, harmless).
- Waits inside words ({W1}-{W8} splits) were redistributed between English words; many tiny waits ended up in clusters (timing only).

## Glossary proposals
- 風紀委員 / 栗生: Yuumi says "Kuryuu from the Discipline Committee" (kept contiguous so the glossary check passes).
- 話題 in YUM_DEA:71 means "popular/the talk of the moment", not the game system "topic"; the entry could be restricted to the game-system sense.
- ドキドキ = "heartbeat" is a dev-label entry; in narration "heart pounding" is more natural but the checker warns unless the word "heartbeat" appears.
- 引っ越し (move house) and 電車通学 (commute by train) recur in the YUM route; suggest adding "the move" / "commute by train".
