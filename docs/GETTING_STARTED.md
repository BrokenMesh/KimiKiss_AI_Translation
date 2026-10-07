# Getting started (for players)

You need: your own KimiKiss PS2 disc dump, a PS2 BIOS dump, and a Windows, Linux or macOS computer. Nothing here provides the game or a BIOS.

## 1. Check your dump

The patch only works on one exact dump: the eb!Kore+ KimiKiss, serial SLPS-25850, 1,267,597,312 bytes.

- Windows: open a Command Prompt in the folder with the ISO and run `certutil -hashfile "KimiKiss.iso" SHA1`.
- Linux or macOS: `sha1sum KimiKiss.iso`.

The result must be `40a70c43ef4c57b8bcdfeab3814437c3eaf4821c`. If it differs, the patch is not for your dump (a different edition, a modified or damaged image) and it will not work.

## 2. Apply the patch

Download `release/KimiKiss_EN.xdelta` from this repository (open the file on GitHub and use the download button).

With a graphical patcher (Windows): open an xdelta patcher such as xdeltaUI or Delta Patcher, set the source file to your ISO, the patch to `KimiKiss_EN.xdelta`, and the output to a new name such as `KimiKiss_EN.iso`. Press Patch. Your original ISO is not changed.

With the command line: `xdelta3 -d -s "KimiKiss.iso" KimiKiss_EN.xdelta KimiKiss_EN.iso`.

The result is 1,267,597,312 bytes. If the patcher reports a checksum or source mismatch, go back to step 1.

## 3. Play

1. Install PCSX2 (https://pcsx2.net). Tested: v2.9.108.
2. On first start, point PCSX2 at your own BIOS dump when it asks.
3. Add the folder with `KimiKiss_EN.iso` to the game list and start it. Default settings work.
4. Use a new game or a memory-card save. Save states made with another version of the patch do not work; they can crash or show old text.

PCSX2 maps the PS2 pad to the keyboard by default; change it under Settings > Controllers. In the game, L1 opens the message backlog.

## 4. Report problems

Open an issue on this repository with: the day and location (or scene), a screenshot, the PCSX2 version, and what you expected. Say whether you used the patch from `release/` or a build you made yourself.

## Building the patch yourself (optional)

Install: Python 3 from python.org (tick "Add to PATH"), then `python -m pip install -r requirements.txt`; Git for Windows; xdelta3 (download the Windows `.exe` from https://github.com/jmacd/xdelta-gpl/releases and put it in a folder on your PATH). Then double-click or run `build.bat "C:\path\to\KimiKiss dump.iso"`. Output: `build\KimiKiss_EN.iso` and `build\KimiKiss_EN.iso.xdelta`. The build prints what is missing, with the exact fix.
