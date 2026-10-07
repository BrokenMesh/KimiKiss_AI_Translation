# Phase 5: translation pipeline

How Japanese records become English in the game: export a batch for a translator model, import the answers, run the deterministic compliance check, build, look at it in the emulator. Tools: `tools/translate/batch.py` (export, import, prepare), `tools/translate/rules.py` (limits, measuring, wrapping, glossary; shared), `tools/qa/check_translation.py`, tests in `tools/qa/test_check_translation.py`. Nothing here calls a model. All paths are relative to the repo root; `text/` and `build/` are gitignored and hold game text, so no example below is real game text.

## Workflow

```sh
# 0. Text records exist in text/ (extract_text.py, docs/pipeline.md). Glossary approved: tools/translate/glossary.json
# 1. Export one scene (or a glob / comma list) as a batch for the translator model
python3 tools/translate/batch.py export text ASU_DAT_A build/batch/ASU_DAT_A.jsonl
python3 tools/translate/batch.py export text 'ASU_*' build/batch/        # a directory: one file per scene

# 2. The translator model reads the batch, answers one JSON object per line: {"id": "...", "translation": "..."}

# 3. Import. Validates everything first, writes nothing if any line is bad
python3 tools/translate/batch.py import text build/batch/ASU_DAT_A.answers.jsonl --normalize

# 4. Compliance pass (exit status 1 on any FAIL); the JSON report is what the Haiku pass reads
python3 tools/qa/check_translation.py text --files ASU_DAT_A --json build/qa/ASU_DAT_A.check.json

# 5. Build. prepare wraps the lines; reinsert_text.py (inside build.sh) does not wrap by itself
python3 tools/translate/batch.py prepare text build/prepared_text
tools/build/build.sh ../kimikiss-private/kimikiss.iso build/en.iso build/prepared_text

# 6. Emulator spot check (tools/qa/emu.sh), see below
python3 tools/qa/test_check_translation.py        # unit tests of 2-4
```

Order inside a scene: translate the K2_Script speaker labels (`K2_Script:13, 19, 22, ...`) first. Their width is part of the line budget of every line that speaker says, and `check_translation.py` and `prepare` read the translated labels when they exist (without one they assume the worst case, 92 px).

Steps 3-4 repeat until the check has no FAIL. WARN lines go to the strong-model review together with a random sample, as in the plan.

### Where wrapping happens

D-013 says the reinserter inserts the line breaks. `reinsert_text.py` does not do that yet: it encodes the `translation` as stored. `batch.py prepare` therefore copies the text directory and replaces each translation with the text to reinsert (dialogue word-wrapped with the line break, ConfirmDialog lines wrapped with `\n`). `text/` itself keeps the translator's unwrapped text. `check_translation.py` measures the same prepared text, so a PASS means the build will fit. If `reinsert_text.py` is later changed to call `rules.prepare_text`, drop the `prepare` step.

### Emulator spot check

A static check cannot see glyph shapes, clipping or layout. After a build: boot with `tools/qa/emu.sh start`, walk to the scenes that were just translated (`spam`/`turbo` skip text), take `shot`s and look at: line count and wrap, speaker label against the first line, names (`{Nm}`/`{Nn}`) with a long typed name, choices, the backlog. Write what was checked in the phase report.

## File formats

### Batch line (`export`)

One JSON object per line, in scene order. Records with `translate=false` in `limits.json` are left out, and so are records that already have a translation (`--include-translated` keeps them).

| Field | Meaning |
|---|---|
| `id` | record id (`SCENE:index` or `SCENE:index.sub`); the key for import |
| `scene`, `route`, `speaker` | file, heroine route (`system` for non-script text), speaker slot (`PLY`, `YUM`, ... , `SYS` narration, `ERI/PLY` joint, `null` for choices and fragments) |
| `ja` | Japanese with control codes in braces, e.g. `{W30}`; `／` is a line break |
| `control_codes` | the braced tokens of `ja`, in order |
| `prev`, `next` | up to `--context` (default 3) neighbouring records of the scene: `id`, `speaker`, `ja`, and `en` when that neighbour is already translated, so names and phrasing stay consistent |
| `limit` | the rule for this record, see below |
| `glossary` | glossary entries whose Japanese occurs in `ja`: `ja`, `en`, `note` (empty when `glossary.json` is missing) |
| `translation` | existing translation or `null` |

`limit.kind` and what it means:

| kind | Where it is drawn | Rule |
|---|---|---|
| `dialogue` | message window | at most `lines` (3) lines; `first_px` for line 1 and `cont_px` for the others; wrapped automatically |
| `choice` | choice list | `choices` choices separated by `／`, each one line of at most `max_px` (552), same number as the Japanese; never wrapped |
| `fragment` | text glued into another string or a label | one line, at most 552 px; no wrapping, no `／` |
| `single` | labels, credits, menu text | one line of at most `max_px` px (see `note`) |
| `confirm` | ConfirmDialog (memory card, save/load, confirmations) | at most `lines` lines of 576 px (at the dialog's 0.75 scale); lines split on `\n`; wrapped automatically at spaces |

The numbers are pixels of the English width table (`tools/font/en_widths.json`), already converted for the consumer: a translator never converts scales. `label_px` is the space the speaker label takes.

### Answer line (`import`)

`{"id": "ASU_DAT_A:12", "translation": "..."}`. `en` is accepted as an alias for `translation`; extra fields are ignored; `translation: null` skips the line; blank lines and ``` fences are tolerated. `import` refuses (and writes nothing) for an unknown id, a duplicate id, an empty or non-string translation, a record whose `limits.json` entry says `translate=false`, and a record that already has a different translation unless `--force`. `--normalize` turns curly quotes, the ellipsis character and long dashes into ASCII; `--dry-run` only reports. `import` does not judge content; run the check.

### Text record

`text/<scene>.json` is a list of records: `file, offset, id, speaker, text, control_codes, byte_budget, route, context_prev, context_next`, plus `translation` once translated (D-006 format, written with indent 1 as the extractor does). `translation` wins over `text` when the scripts are rebuilt. `byte_budget` is informational: strings are length-prefixed and the archive is rebuilt.

### Glossary (`tools/translate/glossary.json`)

`{"terms": [{"ja", "en", "kind", "note"}], "policy": {}}`. A missing or unreadable file is tolerated (export leaves `glossary` empty, the check skips step d). The check accepts `en` as one string, alternatives written `"a|b"`, or a list, and the optional keys `variants` (list) and `check` (`false` switches the term off). Terms with `kind` `honorific` or `suffix`, and terms of one or two kana, are not checked because they match inside unrelated words; the policy for those is a review matter.

### Check report

Console: one block per record that is not PASS (`-v` prints PASS too): status, id, kind, then one line per reason `LEVEL CODE: message`, and a summary line with counts. `--json` writes `{"summary": {...}, "results": [...]}`; each result has `id, file, status, kind, speaker, reasons[{level, code, msg}]`, the measured line widths (`lines_px`), and, for non-PASS records, `ja` and `en`. Exit status 1 when any record FAILs (`--strict`: also WARN; `--require-all`: untranslated records FAIL).

| Code | Level | Meaning |
|---|---|---|
| `CC_MISSING`, `CC_EXTRA` | FAIL | a control code was dropped, added or altered |
| `CC_ORDER` | FAIL | codes of one family were reordered (see below) |
| `CC_MOVED` | WARN | same codes in another order (allowed by D-006) |
| `CC_PREFIX` | FAIL | the line began with `{Ti..}` and no longer does |
| `CC_BRACE` | FAIL | unbalanced or nested braces |
| `JP_LEFT` | FAIL | kana, kanji or full-width characters outside braces |
| `NOT_ENCODABLE` | FAIL | a character with no English glyph (accents, curly quotes, `…`, dashes, emoji) |
| `CONTROL_CHAR` | FAIL | a newline outside ConfirmDialog, or another control character |
| `FIT_LINES`, `FIT_PX`, `FIT_COMPOSITE`, `CHOICE_COUNT` | FAIL | does not fit (see Limits) |
| `FIT_WORD` | WARN | a single word is wider than the line; the engine breaks it mid-word |
| `GLOSSARY` | WARN | a glossary term's English is missing |
| `EMPTY`, `UNTRANSLATED` | FAIL | empty, or identical to the Japanese |
| `TRANSLATE_FALSE` | FAIL | translation on a record that must not be translated |
| `DOUBLE_SPACE`, `EDGE_SPACE`, `QUOTES`, `BRACKETS`, `NO_LETTERS`, `IDEOGRAPHIC_SPACE`, `NO_LIMIT` | WARN | suspicious |

## Rules for the translator

1. **Control codes are part of the text.** Every `{...}` token in `ja` must appear in the translation, spelled the same (`{V0858}`, `{W30}`, `{Ec}`, `{Nm}` ...). Do not add, drop, translate or renumber them. They are not spoken text and take no space.
2. **Moving tokens is allowed (D-006), within reason.** Put each code where it belongs in the English: `{W}` waits after the phrase they paced, `{Nm}`/`{Nn}` where the name goes, `{V...}` voice at the start of the spoken part. Never reorder codes of the same kind among themselves (the check fails `{Ec}`...`{Eo}` swapped, or two `{F..}` swapped). Waits and the two name tokens can swap freely. A line that starts with `{Ti..}` must still start with it.
3. **Names.** `{Nm}` is the player's surname and `{Nn}` the given name, typed by the player. They are measured as 120 px each (a typical 8-letter English name), and a longer name may wrap mid-word. Use `{Nm}` and `{Nn}` as the Japanese does; do not write a default name instead. Heroine names come from the glossary.
4. **Line breaks.** `／` (U+FF0F) is the engine's line break and `\n` is not: the message window drops `\n`, and `TextLine` menus draw it as a glyph. Only ConfirmDialog strings use `\n`. In dialogue **do not insert line breaks and do not copy the Japanese `／`**: wrapping is automatic at word boundaries (`prepare`). Write the line as one paragraph. A `／` you do write is kept as a forced break (rarely wanted). Choices are the exception: `／` separates the choices and you keep one per choice.
5. **Length.** Dialogue may take three lines of 552 px (about 43 average letters per line); with a speaker label the first line gives up the label width and the other lines start at the 92 px indent (460 px). Narration (`SYS`) has no label and no indent. Do not pad or abbreviate unless the check says it does not fit; then shorten the English. If it still fails, tell the reviewer instead of cutting meaning.
6. **System text** has a fixed pixel budget per record (`limit.max_px`, `lines`, `note`): labels 92 px, credits 560 px, default names 72 px, ConfirmDialog 576 px. A ConfirmDialog message is not wrapped by the engine: lines are split on `\n` (the pipeline adds breaks at spaces for you; your own `\n` are kept). The topic message is three strings glued at run time (`K2_Script:240`, a topic name, `K2_Script:241`); their sum must stay on one line (552 px). The memory card status and the following `MemoryCardCheck` text are shown together (status + blank line + text <= 14 lines). Records marked `translate=false` are never exported.
7. **Characters.** Only printable ASCII (space to `~`) exists in the English font. No curly quotes (`"` and `'` only), no `…` (write `...`), no dashes except `-` (write `--` for an em dash), no accents. `--normalize` fixes the common ones on import. Full-width letters, kana, kanji and `・` must not remain (a choice may keep the `・` bullet). Keep text inside the quote marks the Japanese uses: `「...」` becomes `"..."`; thoughts in `（...）` become `(...)` or plain text, as the style guide decides.
8. **Glossary.** If the Japanese contains a glossary term, use its English (any listed variant). Honorific policy is in the glossary `policy`.
9. **One answer line per exported line**, same `id`, no commentary, no markdown.

## Limits and how the check measures them

All widths are summed from `en_widths.json` at the consumer's scale (message window and `TextLine` 1.0, ConfirmDialog 0.75); `{Nm}`/`{Nn}` count `en_text.NAME_PX` (120 px, scaled); other braced codes count 0; any remaining Japanese character counts 23 px (window), 24 px (`TextLine`) or 18 px (ConfirmDialog).

- **Dialogue.** `en_text.wrap` is run with the record's `first_px` and `cont_px`, then every line is measured. `first_px = 552 - label_px`, `cont_px = 552 - 92 = 460` for a named speaker; 552 and 552 for `SYS` and for narration without label. `label_px` is the width of the translated `K2_Script` label of the speaker (`SPEAKER_LABEL_ID` in `rules.py`), or 92 if that label is not translated yet; `PLY` is at least `NAME_PX` because the label becomes the player's surname at run time; a joint speaker (`ERI/PLY`) takes the widest. Rows are counted with the engine's overflow wrap: a line wider than its limit adds `ceil(px / limit) - 1` rows, and trailing lines holding only codes draw nothing. More than 3 rows is `FIT_LINES`.
- **Choices.** Split on `／`; the count must equal the Japanese; each part at most 552 px.
- **ConfirmDialog.** Lines split on `\n` and `／`; each at most `max_px` (576) at scale 0.75; the line count at most the record's `lines` (usually 14).
- **Other system text.** One line at `max_px` from `limits.json`, no newline.
- **Runtime concatenations.** Topic message: `K2_Script:240 + WadaiTable:* + K2_Script:241` <= 552 px; the per-part budgets (200 + 250 + 100) are only warnings. For a topic record the other two parts count as translated, else as their budget. Memory card: the longest status (`MemoryCard:11.1,2,3,5`) + 2 + `MemoryCardCheck:9.19` <= 14 lines; untranslated parts count with the Japanese line count.

## Engine rules I could not confirm

These shaped the checker; none is verified in the emulator for translated text.

- Whether the speaker label is drawn for every speaker, including `PLY` thoughts and `NAR`, and whether `putIndent: 4` also applies when the label is empty. The checker assumes yes (worst case).
- Where the name plate for `PLY` lands when the typed surname is wider than the 92 px indent: it only moves the start of line 1 (`phase-4-name-entry.md`); the checker reserves 120 px.
- Records with speaker `null` outside the choice lists (about 200: names, half sentences such as an opening quote or a trailing clause) are glued into other strings at run time. The checker treats them as one line of at most 552 px and cannot know their real context; translate them so the concatenation reads correctly and look at them in the emulator.
- Whether `｜` (the pause code) and `U+3000` may remain in English text. The checker allows both outside choices, warning on `U+3000` inside a sentence; they draw as a pause and a 23 px blank.
- `reinsert_text.py` does not wrap (see above). If D-013 is meant literally, `rules.prepare_text` is the function to call from it.
