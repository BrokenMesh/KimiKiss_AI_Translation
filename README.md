<p align="center"><img src="docs/logo.png" alt="KimiKiss" width="480"></p>

# KimiKiss English translation patch (PS2, SLPS-25850)

Fan translation of KimiKiss (eb!Kore+ re-release, SLPS-25850) into English. Status: test build, under QA. Expect bugs; see "Reporting bugs".

This repository contains no game data. The patch is an xdelta file that only works on your own dump of the disc.

## Apply the patch

Required source image: 1,267,597,312 bytes, SHA-1 `40a70c43ef4c57b8bcdfeab3814437c3eaf4821c`.

```sh
sha1sum KimiKiss.iso
xdelta3 -d -s KimiKiss.iso release/KimiKiss_EN.xdelta KimiKiss_EN.iso
```

A GUI patcher such as Delta Patcher also works (source: your ISO, patch: `release/KimiKiss_EN.xdelta`). A different dump or edition fails the checksum or produces a broken image.

Run the result in PCSX2. Save states from other builds do not carry over; start from a memory-card save or a new game.

## Reporting bugs

Include: where in the game (scene, day, location), what the screen showed, a screenshot, and the PCSX2 version. Typical findings: leftover Japanese, clipped or overlapping text, wrong name, crash or hang, text in an image that was not translated.

## Build it yourself

```sh
tools/build/build.sh /path/to/KimiKiss.iso build/KimiKiss_EN.iso
```

The build verifies the checksum, never writes to the source ISO, and writes `build/KimiKiss_EN.iso.xdelta`. Requirements and every tool are described in `docs/pipeline.md`. Design decisions are in `docs/decisions.md`; the name glossary is `docs/glossary.md`.

The logo is a custom design by the project's contributor.
