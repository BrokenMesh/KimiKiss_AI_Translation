# Getting started (for players)

You need: your own KimiKiss PS2 disc dump, a PS2 BIOS dump (for the emulator), and a Windows, Linux or macOS computer. Nothing here provides the game or a BIOS.

There are two ways to get the English game. Way A needs no programming. Way B builds it from the source and lets you change the translation.

## 1. Check your dump (both ways)

The patch only works on one exact dump: eb!Kore+ KimiKiss, serial SLPS-25850, 1,267,597,312 bytes.

- Windows: open a Command Prompt in the folder with the ISO and run `certutil -hashfile "KimiKiss.iso" SHA1`.
- Linux or macOS: `sha1sum KimiKiss.iso`.

The result must be `40a70c43ef4c57b8bcdfeab3814437c3eaf4821c`. If it differs, the patch is not for your dump (another edition, a modified or damaged image) and will not work. If your dump is a `.bin/.cue`, `.chd` or similar, convert it to a single `.iso` first.

## Way A: apply the ready patch

1. Download `release/KimiKiss_EN.xdelta` from this repository (open the file on GitHub and use the download button).
2. Graphical patcher (Windows): open an xdelta patcher such as xdeltaUI or Delta Patcher. Source file: your ISO. Patch: `KimiKiss_EN.xdelta`. Output: a new file such as `KimiKiss_EN.iso`. Press Patch. Your original ISO is not changed.
3. Command line: `xdelta3 -d -s "KimiKiss.iso" KimiKiss_EN.xdelta KimiKiss_EN.iso`.
4. The result is 1,267,597,312 bytes. If the patcher reports a checksum or source mismatch, go back to step 1.

This patch contains everything, including the hand-made images (title logo, help pages, charts).

## Way B: build it yourself

Use this to change the translation, test a fix, or check what the patch does.

Install once:

- Python 3 from python.org (Windows: tick "Add to PATH"), then `python -m pip install -r requirements.txt` (Pillow and numpy).
- xdelta3: Linux `apt install xdelta3`; Windows: download the `.exe` from https://github.com/jmacd/xdelta-gpl/releases and put it in a folder on your PATH. (Skip with `KIMIKISS_NO_XDELTA=1` if you only want the ISO.)
- Windows only: Git for Windows (https://git-scm.com/download/win). The build is a bash script and runs in Git Bash.

Build:

```sh
tools/build/build.sh "KimiKiss dump.iso" build/KimiKiss_EN.iso        # Git Bash, Linux, macOS
build.bat "C:\path\to\KimiKiss dump.iso"                                # Windows Command Prompt
```

It prints one line per step and ends with `OK: created the ISO` and `OK: created the patch`. Both files are in the `build` folder of the repository: `build\KimiKiss_EN.iso` (play this; never share it) and `build\KimiKiss_EN.iso.xdelta` (the patch you can share). A bare output name such as `my.iso` is also put in `build`; the name must end in `.iso`. Options go after the ISO path, for example `--no-xdelta` to skip the patch file (do not write `KIMIKISS_NO_XDELTA=1` as a second argument: Windows treats the `=` as a separator). Details are in `build/build.log`. The first run also extracts the disc into `build/orig/` and the Japanese text into `text/` (local only, never commit them).

The hand-made images are the PNG files in the repository's `texture_overrides/` folder (`GRAPH0_0178.png`, `GRAPH1_0194.png`, ... named after the archive entry) and are used automatically; the build prints how many it found. To try your own image, put it there with the same naming scheme and the original size, or point `KIMIKISS_OVERRIDES` at another folder.

Typical errors, all printed with the fix by the build itself: wrong Python (no Pillow/numpy), missing xdelta3, ISO checksum mismatch.

## Play

1. Install PCSX2 (https://pcsx2.net). Tested: v2.9.108.
2. On first start, point PCSX2 at your own BIOS dump when it asks.
3. Add the folder with the English ISO to the game list and start it. Default settings work.
4. Start a new game, or continue from a memory card save. Emulator save states made with another version of the patch can crash or show old text.

PCSX2 maps the PS2 pad to the keyboard by default; change it under Settings > Controllers. In the game, L1 opens the message backlog. The text speed is set in the game's Settings menu.

## Report problems

Open an issue or write on the Discord (https://discord.gg/MXaM8ekzu) with: the day and location (or scene), a screenshot, the PCSX2 version, and whether you used the release patch or your own build.
