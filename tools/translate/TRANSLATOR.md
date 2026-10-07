# Translator instructions

The fixed brief for anyone, model or human, who translates a batch of KimiKiss (PS2, 2006) into English. A translator model gets this file, the glossary summary, and one batch. Background on the formats: `docs/phase-5-pipeline.md`, `docs/translation-format.md`; glossary and style decisions: `docs/glossary.md` (final, approved 2026-10-07).

## The job

KimiKiss is a school romance visual novel. The player is a second-year high school boy (default name Aihara Kouichi, typed by the player); eight heroines, his sister Nana, his friend Hiiragi. Translate faithfully into natural, idiomatic English that reads like a good anime subtitle: the meaning, tone and jokes of the Japanese, not its word order. Translate, do not localize: no American settings, no invented jokes, Japanese names and school life stay Japanese.

One record in, one record out. Never move content between records, never merge or split lines: every record is shown on its own screen, often with a voice clip.

## Input: the batch

Made with `python3 tools/translate/batch.py export text <SCENE> build/batch/<SCENE>.txt --format text` (several scenes: a glob or a comma list, or a directory as the output for one file per scene).

```
# scene PLY_PRO  route PLY  lines to translate: 99
# glossary: 菜々 = Nana  (little sister; ...)
PLY_PRO:139 PLY 「大袈裟だなぁ。ちょっとはしごから／落ちたぐらいで」
~PLY_PRO:140 NAN 「...」
  = "{V0012}It wasn't a little!{W10} ..."
PLY_PRO:162 - [fragment: one line, max 552 px] 　男
```

- `<id> <speaker> [limit tag] <japanese>`. The scene is in story order; read the whole scene before translating, the line before and after decide pronouns, tone and who is meant.
- Speakers: `PLY` the player (his own lines are spoken, in 「」, or thoughts, in （）); `SYS` narration, which is the player's first-person narration in this game; three-letter codes for the others (table in `docs/glossary.md` section 2); `ERI/PLY` both at once; `-` no speaker (choices, fragments, system text).
- `~` before an id: already translated, shown for context; its English is on the `  = ` line. Do not answer it unless asked to revise.
- `# glossary:` lines list the glossary terms that occur in this batch. Use that English.
- `／` in the Japanese is the engine's line break of the original layout. It means nothing for English (see Line breaks).

## Output: the answers

A file `build/batch/<SCENE>.answers.jsonl`, one JSON object per line, one line per record to translate, in any order, nothing else in the file:

```
{"id": "PLY_PRO:139", "translation": "\"You're overreacting. You only slipped off a ladder a little.\""}
```

Then import and check, and fix every FAIL before handing back:

```sh
python3 tools/translate/batch.py import text build/batch/<SCENE>.answers.jsonl --normalize
python3 tools/qa/check_translation.py text --files <SCENE>
# fix: write corrected lines to a new answers file, import with --force
```

Write anything the reviewer must know (a pun you could not keep, an unclear referent, a line that cannot fit) to `build/batch/<SCENE>.notes.md`, one bullet per record id. Do not put notes in the translation.

## Control codes `{...}`

Every braced token in the Japanese must appear in the English, spelled exactly the same. They are not text and take no space.

| Code | Meaning | Where it goes in English |
|---|---|---|
| `{V0012}` | voice clip | at the start of the spoken part, as in the Japanese |
| `{W30}` | pause (frames) | after the English phrase the pause followed |
| `{Nm}`, `{Nn}` | player's surname / given name | where the name goes; never write a name instead |
| `{F6}`, `{Ec}`, `{Eo}`, `{B}`, `{S..}`, `{T..}`... | font size, eye/expression, effects | near the word they belong to, same order among their own kind |
| `{Ti..}` at the start | text speed of the line | must stay first |
| `{R}base{R4}reading` | ruby (furigana) over a kanji name | drop the whole ruby for English: write the name once, no `{R}` codes, no reading. Either all ruby codes go or all stay |
| runs of one-letter codes, e.g. `{E}{R}{I}{.}{s}{e}{t}...` | an engine command embedded in the text | copy the run verbatim, in place, untouched |

You may move codes to where they belong in the English word order. Codes of one kind keep their order (two `{F..}` or `{Ec}`/`{Eo}` never swap); waits and name tokens may swap. Never add, drop (except ruby), renumber or translate a code. `{W}` splits inside a word (`見{W2}る{W2}か{W2}ら`) are voice timing: put the waits between English words, never render them as stammer hyphens.

## Line breaks and length

- Dialogue and narration: write one paragraph. Do not copy `／` and do not insert breaks; the build word-wraps.
- The message window holds 3 lines of 552 px (about 43 average characters per line). A spoken line (any line with a plate in front, including the player's thoughts) starts every line at 115 px: 437 px per line, about 35 characters, about 105 characters in total. Narration (`SYS`) gets the full 552 px, about 135 characters. `{Nm}`/`{Nn}` count 120 px each.
- English runs longer than Japanese. When the checker says FIT_LINES, rephrase more tightly; keep the meaning, drop filler. If it truly cannot fit, keep the best fitting version and say so in the notes. Never cut a joke or a plot fact for length without a note.
- Choices (`[choice xN ...]`): exactly N choices separated by the full-width `／` (U+FF0F), each one short line. No other break. Use `- ` where the Japanese has a `・` bullet.
- Dialog boxes (`[dialog box ...]`): `\n` breaks are allowed; the build also wraps at spaces.
- Tagged system text (`[single: one line, max N px; note]`): one line within N px; the note says where it is drawn. Menu labels and buttons are tight: use the shortest natural English.
- Fragments (`[fragment ...]`, speaker `-` without a tag): a piece glued into another string at run time (a name, half a sentence). Translate so it reads correctly in the surrounding lines; say in the notes if you had to guess.

## Characters

Printable ASCII only: straight `"` and `'`, `...` (never the `…` glyph), `--` for a dash, no accents, no full-width letters, no kana or kanji outside braces. `--normalize` on import fixes curly quotes, `…` and long dashes. The one exception is the `／` choice separator.

## Style (summary; the full rules are in `docs/glossary.md`)

- Speech in straight double quotes, `「...」` -> `"..."`. Thoughts in parentheses, `（...）` -> `(...)`. Narration bare.
- Honorifics are omitted: Sakino-san, Narumi-chan, {Nm}-kun -> "Sakino", "Narumi", "{Nm}". Kept forms only: "Master" (Mitsuki to the player), "Senpai" (Narumi, standalone), "Sensei" (standalone address), "Big Bro" (Nana addressing the player) / "big brother" (prose). Name + 先生 -> "Mr./Ms. Surname". The player calls Mao just "Mao". Kawada's nickname is "Tomo".
- Full names family-given ("Sakino Asuka"). Hepburn with long vowels as kana: Shijou, Yuumi, Kuryuu, Kouichi.
- Kuryuu Megumu: keep the gag where people misread her name as "Megumi".
- Ellipsis `...` (`……` -> `......`). Stammer "S-sorry", only where the Japanese repeats a sound. "?!" at most; never more than two marks in a row.
- Laughs and sound effects become English interjections (Hehe, Ahaha, Hmm, Eep); "Ehehe" and "Fufu" are kept as signature laughs. Narration onomatopoeia becomes English ("Thud!"). Drop the tilde `～`, except a trailing `~` for Mao, Nana and Narumi on playful lines.
- Voice per character: the tone table in `docs/glossary.md` section 1 (soft Yuumi, bubbly polite Narumi, teasing Mao, tomboy Asuka, dry Eriko, formal Mitsuki without contractions, stern Megumu, cheerful Nana).
- Terms: school festival, Topic Bag, Discipline Committee, Year 1/2/3, Class 2-A, "behind the school". Mao's surname printed 水〆 is Mizusawa.
- Do not repeat the speaker's name in the line; the plate shows it.
- Japanese addresses people in the third person ("if Big Bro hadn't yelled", 星乃さん、しっかりしてる): English uses "you" plus a vocative ("If you hadn't yelled, Big Bro").
- Punctuation after an ellipsis: none ("Ugh... I wanted", never "Ugh...,"). Stammer applies to any repeated first sound, including そ、そっか -> "R-right...".
- The glossary English is a default, not a word-for-word rule: use the natural word in context (海 can be "the beach", 教室 "class"); add the variant to the glossary if it recurs.
- Credits are never exported. Dev memos (production notes such as "LV2 kiss, all outfits"): translate literally.

## Checklist before handing back

1. Every exported id has exactly one answer; `import` accepted the file.
2. `check_translation.py` shows no FAIL for the scene. WARN lines are read and either fixed or explained in the notes.
3. Names, address forms and recurring terms match the glossary and the lines already translated (`~` lines).
4. The notes file lists every guess.
