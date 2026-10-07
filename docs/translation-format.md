# Translation files (translation/en)

The English text of the game lives in `translation/en/<SCENE>.txt`, one file per scene, committed to this repo. It contains no Japanese. Fix a line by editing the file and opening a pull request: the diff is one line.

## Edit a line

```
# ASU_DAT_A -- English. Edit the line under each @ header. Empty line under a header = untranslated.
# Format: docs/translation-format.md

# note: she says this after the beach scene
@ASU_DAT_A:12 YUM 3f2a91c0
"Hey, {Nn}. Wait a second."

@ASU_DAT_A:13 SYS 9b01de44

```

- The header `@<id> <speaker> <src>` is written by the tools. Do not edit it. `id` is the record (scene and index), `speaker` is who talks (`-` = nobody: choices, name fragments; `SYS` = narration; `ERI/PLY` = two speakers), `src` is the first 8 hex digits of the SHA-1 of the Japanese line this English was written against.
- The English is exactly **one physical line** right under the header. An empty line means not translated yet. Do not put a blank line between the header and the English.
- Do not wrap dialogue by hand: the build wraps it to the message window (3 lines). Write one paragraph.
- Lines starting with `#` are comments. A comment block right before a header belongs to that record; tools keep it when they rewrite the file. Use it for translator notes.
- Records are listed in scene order; the tools regenerate headers and order. Records the game must not translate are not listed.

## Escapes

| Write | Means |
|---|---|
| `\n` | a line break, only for ConfirmDialog (memory card, save/load, confirmations) messages |
| `\\` | a backslash |
| `\#`, `\@` | `#` or `@` as the first character of the line (otherwise it would be a comment or header) |

Choices (`ASU_DAT_A:40.1` style ids) are one line: the choices are separated by the full-width `／` (U+FF0F) as in the Japanese, one per choice, same count. That character, `｜` and U+3000 are the only non-ASCII characters accepted. Everything else must be printable ASCII: straight quotes only, `...` for an ellipsis, `--` for a dash, no accents. Use `- ` where the Japanese choice has a `・` bullet. The importer and the test suite refuse Japanese characters in this directory.

## Control codes

Everything in braces, `{V0858}`, `{W30}`, `{Ec}`, `{Nm}`, `{Nn}`, is part of the line and must stay, spelled the same. Move them to the English word they belong to if needed, but do not drop, add or renumber them, and do not reorder codes of the same kind. `{Nm}` / `{Nn}` are the player's surname and given name. The full rules (length, wrapping, glossary) are in `docs/phase-5-pipeline.md`, "Rules for the translator".

## Check and build locally

You need your own copy of the game: the Japanese text is extracted from your ISO into `text/` (ignored by git, never commit it; see `docs/pipeline.md`).

```sh
# see Japanese and English side by side
python3 tools/translate/batch.py show text ASU_DAT_A --id ASU_DAT_A:12
python3 tools/translate/batch.py show text ASU_DAT_A

# does the line pass (control codes, characters, fit in the window)?
python3 tools/qa/check_translation.py text --files ASU_DAT_A

# build an ISO with the committed translation
tools/build/build.sh path/to/your.iso build/en.iso
```

After the extractor ran or the game text changed: `python3 tools/translate/batch.py sync text` adds new records, keeps all lines and comments, and reports problems. Without `text/` you can still edit and open a PR; the maintainers run the checks.

## STALE

If the Japanese of a record changed after its English was written, the header hash no longer matches. `check_translation.py` reports `SRC_STALE` (a warning), and `batch.py sync` keeps the English and adds a `# STALE src: ...` comment above the record. Read the English against the current Japanese (`batch.py show`), fix it if needed, then run `batch.py sync text --accept-src` to store the new hash and drop the comment. An untranslated record just gets the new hash silently.

Records whose id disappeared from the extracted text are kept at the end of the file with `# ORPHAN` and reported; nothing is deleted automatically.
