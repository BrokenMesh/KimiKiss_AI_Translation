**Discord (general work, planning, questions): https://discord.gg/MXaM8ekzu**

<p align="center"><img src="docs/logo.png" alt="KimiKiss English patch logo" width="480"></p>

# KimiKiss English Patch (PS2 English Translation)

Fan translation of **KimiKiss** (キミキス, also written Kimi Kiss; Enterbrain, PlayStation 2) into English (キミキス 英語化パッチ). A free xdelta patch for your own dump, playable in PCSX2. It covers the full script (about 35,000 lines, all routes), menus, name entry, save/load screens, the in-game help pages and most of the text in images.

**The translation was produced with AI assistance** (Claude models, with a glossary, per-scene context and automatic checks) and has been spot-checked, not yet read through by a human editor. It is faithful but sometimes stiff. Human review is the most valuable help right now; see "Helping with the translation".

Status: **test release**. Everything was played through the first days in PCSX2 without crashes, but not every route and every scene has been checked. Expect rough lines and a few leftovers; please report them (see below or discord).

Project page: https://brokenmesh.github.io/KimiKiss_AI_Translation/

This repository contains **no game data**. You need your own dump of the disc. The patch is a binary difference that only works on that exact dump.

| | |
|---|---|
| Edition | eb!Kore+ KimiKiss, serial **SLPS-25850**, volume `KIMIKISSPLUS` (2008 budget re-release) |
| Size | 1,267,597,312 bytes |
| SHA-1 | `40a70c43ef4c57b8bcdfeab3814437c3eaf4821c` |
| Tested on | PCSX2 v2.9.108 |

## Two ways to get the English game

### A. Apply the ready patch (recommended, five minutes)

1. Check your dump: `certutil -hashfile "KimiKiss.iso" SHA1` (Windows) or `sha1sum KimiKiss.iso` (Linux, macOS). It must print the SHA-1 above.
2. Download [`release/KimiKiss_EN.xdelta`](release/KimiKiss_EN.xdelta) (open the file on GitHub, press the download button).
3. Apply it with an xdelta patcher (for example xdeltaUI or Delta Patcher): source = your ISO, patch = `KimiKiss_EN.xdelta`, output = `KimiKiss_EN.iso`. Command line: `xdelta3 -d -s KimiKiss.iso release/KimiKiss_EN.xdelta KimiKiss_EN.iso`.
4. Start `KimiKiss_EN.iso` in PCSX2.

The patch contains everything: the translation, the code changes and the hand-made images (title logo, help pages, charts).

### B. Build it yourself from the source

Needs Python 3, `pip install -r requirements.txt`, xdelta3, and on Windows Git for Windows (Git Bash).

```sh
tools/build/build.sh "KimiKiss dump.iso" build/KimiKiss_EN.iso      # Linux, macOS, Git Bash
build.bat "C:\path\to\KimiKiss dump.iso"                              # Windows (add --no-xdelta to skip the patch file)
```

The build checks your ISO's checksum first, never writes to it, prints one line per step and ends with `OK: created the ISO` and `OK: created the patch`. Both files are in the `build/` folder: `build/KimiKiss_EN.iso` and `build/KimiKiss_EN.iso.xdelta` (share the `.xdelta`, never the ISO). About a minute. The hand-made images are in `texture_overrides/` and are used automatically, so the result equals the release patch. Do this if you want to change the translation, the images or the tools.

Step-by-step with all prerequisites and common errors: **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)**.

## Easy Mode (optional)

The title menu has an **Easy Mode** item with four switches, all off by default: **No Losses** (a bad conversation or a declined girl never lowers her mood, notes or interest), **Fewer Rejections** (she agrees to talk more often and does not walk off), **Easier Meetings** (girls you have met turn up more often on the map) and **More Tries** (the daily invite/kiss Attack and the topic deck do not run out). Both the love and the friendship routes stay reachable. Details: [docs/easy-mode.md](docs/easy-mode.md).

## Reporting bugs

Open an issue, or write on the Discord. Include: where in the game (day, location, scene), a screenshot, your PCSX2 version, and whether you used the release patch or your own build. Typical findings: leftover Japanese, clipped or overlapping text, a wrong name, a crash or hang, a picture that is still Japanese.

## Helping with the translation

Fixing a line is a one-line edit in a text file. See **[CONTRIBUTING.md](CONTRIBUTING.md)**. All the files of the translation are in `translation/en/`, one per scene.

## Repository map

| Path | What |
|---|---|
| `translation/en/` | the English text, one file per scene |
| `texture_overrides/` | the hand-made images (PNG) that replace Japanese images |
| `tools/` | extraction, reinsertion, build, texture, translation and QA tools |
| `patches/` | the changes to the game's scripts (`scripts/`) and executable (`elf/`) |
| `release/` | the distributable xdelta patch |
| `docs/` | documentation; start with [docs/README.md](docs/README.md) |

## Legal

Unofficial fan project, not affiliated with the rights holders. No game data is distributed. Code and translation: MIT (`LICENSE`); see `NOTICE.md` for the parts under other licences (the Inter font), the note on the images and credits. The logo is a custom design by a project contributor.
