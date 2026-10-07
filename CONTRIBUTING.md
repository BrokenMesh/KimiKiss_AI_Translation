# Helping with the translation

The English text is plain text files in `translation/en/` (one per scene, 226 files, about 35,000 lines). You can fix a line without installing anything, or use the tools to check and play your change.

Questions, planning and coordination: Discord, https://discord.gg/MXaM8ekzu

## What needs doing

1. **Read-through and polish.** The translation was made with AI assistance. It is faithful, but some lines are stiff, some voice-timing codes sit at the end of a line, and a few meanings are off. Pick a route (the file prefix: `ASU`, `ERI`, `MAO`, `MIT`, `NAR`, `YUM`, `MEG`, `NAN`, `PLY` = prologue and the player's own scenes, `ALL_` = shared scenes) and read its scenes in order.
2. **Clear the checker's warnings.** `python3 tools/qa/check_translation.py text` lists them (needs the extracted text, see below). Today: 0 failures, about 4,200 warnings, mostly moved control codes (harmless) and glossary hits (worth a look).
3. **Play and report.** Bugs and leftover Japanese found while playing: open an issue with day, place, screenshot.
4. **Images.** Remaining Japanese is inside icons (for example the help pages' `アタック` and `エスケープ`). See "Images" below.

## Fix one line, no tools

1. Find the line. Search the English text you saw in the game: `grep -rn "wake me up with a kiss" translation/en` (or use GitHub's search in the `translation/en` folder). The file name is the scene.
2. Edit the line under its header, for example:

   ```
   @PLY_PRO:143 PLY 09cf0cb2
   "It's because you said you'd wake me up with a kiss..."
   ```

3. Rules, the short version (full version: `docs/translation-format.md` and `tools/translate/TRANSLATOR.md`):
   - Do not touch the `@...` header line. The English is exactly one line under it.
   - Keep every `{...}` code (`{V0858}`, `{W3}`, `{Nm}`, `{Nn}`, ...) spelled the same. They are voices, timing and the player's name. You may move a code next to the English word it belongs to; do not delete or add any.
   - Plain ASCII only: straight quotes, `...`, `--`, no accents. Do not wrap lines by hand: the build wraps them.
   - Use the names in `docs/glossary.md` (for example Kuryuu Megumu, Shijou Mitsuki, "Big Bro" from Nana). Honorifics are dropped by policy.
   - Choices are one line with the options separated by the full-width `／`, same count as the Japanese.
4. Open a pull request (or an issue with the scene id and the new line). A pull request touches only `translation/en/`.

## Check and play your change (with the tools)

You need your own dump of the disc (see the README for the exact edition) and Python 3 with Pillow and numpy.

```sh
pip install -r requirements.txt
tools/build/build.sh --text-only "KimiKiss dump.iso"        # once: extracts the Japanese text into text/ (stays local, never commit it)

python3 tools/translate/batch.py show text PLY_PRO                       # Japanese and English side by side
python3 tools/translate/batch.py show text PLY_PRO --id PLY_PRO:139      # one line
python3 tools/qa/check_translation.py text --files PLY_PRO               # codes, characters, glossary, fit
python3 tools/qa/check_translation.py text                               # everything

tools/build/build.sh "KimiKiss dump.iso" build/test.iso                  # build a test image (about a minute)
```

Start `build/test.iso` in PCSX2 and go to the scene. Start a new game or use a memory card save; emulator save states from another build can show old text. The text typing speed and the window size are fixed by the patch; if a line does not fit the checker says `FIT_PX` or `FIT_WORD`.

Exit status 1 from the checker means a line is broken (a FAIL: a dropped control code, a forbidden character, a line that cannot fit); fix it before sending. Warnings are advice. The maintainers run the checker over everything before each release.

## Add or revise many lines

`python3 tools/translate/batch.py export text <SCENE> build/batch/<SCENE>.txt --format text` writes a scene with context; `batch.py import` validates and stores answers. This is the same path the AI translation used; the formats, the brief for a translator (human or model) and the compliance rules are in `tools/translate/TRANSLATOR.md`, `docs/phase-5-pipeline.md` and `docs/translation-format.md`. A scene's Japanese text changing under an English line is reported as `SRC_STALE`; `batch.py sync text` shows what changed.

## Images

Text in pictures is replaced by PNG files named after the archive entry (`GRAPH0_0178.png`, `GRAPH1_0194.png`, ...), exactly the original size. Details in `docs/phase-4-textures.md` ("Hand-edited textures"). The PNGs are derived from game art, so they are **not committed**. Put your PNGs in `texture_overrides/` (ignored by git), run `python3 tools/texture/overrides.py check`, build, and send the PNGs to the maintainers on the Discord; they go into the release patch. Many labels are redrawn automatically from `tools/texture/labels.tsv`; fixing a label is a one-line edit there (columns: entry, Japanese, English, note).

## Pull request checklist

Optional guard against committing game files by mistake: `git config core.hooksPath tools/githooks` (rejects disc images, executables and files over 5 MiB). `tools/qa/run_tests.sh` runs all test suites after one build.

- Only files you meant to change; no `text/`, no ISO, no PNG from the game, no extracted files.
- `python3 tools/qa/check_translation.py text --files <SCENE>` shows no FAIL (skip if you have no ISO; the maintainers run it).
- Glossary changes (`docs/glossary.md`, `tools/translate/glossary.json`) are decided by the maintainers: explain the reason in the pull request.

## Project history and decisions

`docs/decisions.md` has the numbered decision log (D-001 and on); `docs/README.md` indexes the reverse-engineering notes.
