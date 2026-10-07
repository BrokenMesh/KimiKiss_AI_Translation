<p align="center"><img src="docs/logo.png" alt="KimiKiss" width="480"></p>

# KimiKiss English translation patch (PS2, SLPS-25850)

Fan translation of KimiKiss (eb!Kore+ re-release, SLPS-25850) into English. Status: test build under QA. Expect bugs; see "Reporting bugs".

This repository contains no game data. The patch only works on your own dump of the disc.

## Play it (Windows, no programming)

Step-by-step with screenshots-free instructions: **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)**.

Short version:

1. Have a dump of your own KimiKiss disc: 1,267,597,312 bytes, SHA-1 `40a70c43ef4c57b8bcdfeab3814437c3eaf4821c`. Check it with `certutil -hashfile "KimiKiss.iso" SHA1` in a Command Prompt.
2. Download `release/KimiKiss_EN.xdelta` from this repository.
3. Apply it to your dump with an xdelta patcher (for example xdeltaUI or Delta Patcher). Source file: your ISO. Patch: `KimiKiss_EN.xdelta`. Result: `KimiKiss_EN.iso`.
4. Start `KimiKiss_EN.iso` in PCSX2 (tested with v2.9.108, with your own BIOS dump).

## Reporting bugs

Open an issue on this repository. Include where in the game it happened (day, location, scene), a screenshot, and your PCSX2 version. Typical findings: leftover Japanese, clipped or overlapping text, a wrong name, a crash or hang, text in a picture that is still Japanese.

## Build it yourself

Needs Python 3 (with `pip install -r requirements.txt`), xdelta3, and on Windows Git for Windows. Then:

```sh
tools/build/build.sh "KimiKiss dump.iso" build/KimiKiss_EN.iso      # Linux, macOS, Git Bash
build.bat "C:\path\to\KimiKiss dump.iso"                              # Windows
```

The build checks your ISO's checksum first, never writes to it, prints one line per step (details in `build/build.log`) and ends with the path of the patched image and of its `.xdelta`. Details for contributors: `docs/pipeline.md`. Design decisions: `docs/decisions.md`. Name glossary: `docs/glossary.md`.

The logo is a custom design by the project's contributor. The Inter font files in `tools/font/` are under the SIL Open Font License (`tools/font/LICENSE-Inter.txt`).
