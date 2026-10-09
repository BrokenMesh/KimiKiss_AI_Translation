# How to help translate

The English text is plain text files in `translation/en/`, one per scene. Questions and coordination happen on Discord: https://discord.gg/MXaM8ekzu

For a quick fix to one line you don't need any tools (see "Fix one line, no tools" in [CONTRIBUTING.md](CONTRIBUTING.md)). The steps below are for checking and playing your change.

## Requirements

- **Git**
- **Python 3** with Pillow and numpy (installed in step 1)
- **xdelta3**, only needed to build the distributable patch. Add `--no-xdelta` to skip it.
- **Your own dump of the game disc**, the exact edition named in the README (ebKore+)
- **PCSX2** to play the result
- Windows only: `build.bat` runs `build.sh` through Git for Windows' Git Bash, so Git must be installed there.

## 1. Set up the repo

```sh
git clone https://github.com/BrokenMesh/KimiKiss_AI_Translation.git
cd KimiKiss_AI_Translation
pip install -r requirements.txt
```

## 2. Extract the Japanese text

Run this once. It extracts the Japanese text into `text/`. That folder stays local and must never be committed.

- Linux / Git Bash: `tools/build/build.sh --text-only "KimiKiss dump.iso"`
- Windows: `.\build.bat --text-only "KimiKiss dump.iso"`

## 3. Find the scene

Scene files are named `<route>_<scene>`, for example `ASU_KBE` or `PLY_PRO`. Route prefixes are `ASU`, `ERI`, `MAO`, `MIT`, `NAR`, `YUM`, `MEG`, `NAN`, `PLY` (prologue and the player's own scenes) and `ALL_` (shared scenes).

The easiest way to find a scene is to search for the English text you saw in the game:

```sh
grep -rn "wake me up with a kiss" translation/en
```

You can also use GitHub's search in the `translation/en` folder. The file name is the scene.

To see the Japanese and English side by side:

```sh
python3 tools/translate/batch.py show text ASU_KBE
python3 tools/translate/batch.py show text ASU_KBE --id ASU_KBE:139    # one line
```

## 4. Translate

Open `translation/en/ASU_KBE.txt` and edit the line under its header:

```
@PLY_PRO:143 PLY 09cf0cb2
"It's because you said you'd wake me up with a kiss..."
```

Rules, the short version:

- Do not touch the `@...` header line. The English is exactly one line under it.
- Keep every `{...}` code (`{V0858}`, `{W3}`, `{Nm}`, `{Nn}`, ...) spelled the same. They are voices, timing and the player's name. You may move a code next to the English word it belongs to, but don't delete or add any.
- Plain ASCII only: straight quotes, `...`, `--`, no accents. Don't wrap lines by hand, because the build wraps them.
- Use the names in [docs/glossary.md](docs/glossary.md). Honorifics are dropped by policy.
- Choices are one line, with the options separated by the full-width `／` and the same count as the Japanese.

Full details: [docs/translation-format.md](docs/translation-format.md) and [tools/translate/TRANSLATOR.md](tools/translate/TRANSLATOR.md).

### Text in pictures (menus, buttons, map tags)

Menu and button labels are pictures. Their English is in [translation/textures.toml](translation/textures.toml), one block per picture, grouped by screen:

```toml
[[texture]]
entry = 459
name = "sysgraph/menu_set2"
size = [120, 32]
[[texture.line]]
japanese = "振動"
english = "Rumble"
```

Change `english` and nothing else unless the result does not fit. The other keys (box, alignment, font size, larger sprites) are explained at the top of the file. `python3 tools/texture/texdefs.py check` reports mistakes. To see the result without a full build, run `python3 tools/texture/redraw.py build/orig/GRAPH/GRAPH0.ARC build/tex_out --preview qa/tex --only 459`; it writes the original and the new picture side by side to `qa/tex/GRAPH0_0459.png`.

## 5. Validate

```sh
python3 tools/qa/check_translation.py text --files ASU_KBE
```

A FAIL means a line is broken (a dropped control code, a forbidden character, or a line that cannot fit). The checker then exits with status 1, and you must fix it before sending. Warnings are only advice.

## 6. Build and play (optional)

- Linux / Git Bash: `tools/build/build.sh "KimiKiss dump.iso" build/test.iso`
- Windows: `.\build.bat "KimiKiss dump.iso" test.iso`

The build takes about a minute. Start `build/test.iso` in PCSX2 and go to the scene. Start a new game or use a memory card save, because save states from another build can show old text.

## 7. Send it in

Open a pull request. It should touch only `translation/en/` (and `translation/textures.toml` for picture text), with no `text/`, no ISO and no files from the game. Alternatively, open an issue with the scene id and the new line.
