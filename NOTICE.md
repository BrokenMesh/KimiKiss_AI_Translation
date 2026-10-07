# Notices

## What this repository is

An unofficial fan translation project. It is not affiliated with or endorsed by Enterbrain, Idea Factory or any rights holder of KimiKiss. KimiKiss and all its characters, text, art and sound belong to their owners.

## What is not in this repository

No game image, BIOS, executable, extracted game file or patched image. The text records, the Ghidra project and the hand-made textures (which are derived from game art) stay on the contributors' machines. You need your own legally obtained dump of the disc (`docs/source-iso.md` gives the exact edition and checksum). The only game-derived data published is `release/KimiKiss_EN.xdelta`, a binary difference that is useless without the original disc, plus short strings (names, labels, a few lines) quoted in documentation and tests.

## Licences of the parts

| Part | Licence |
|---|---|
| Code, patches, scripts, documentation, the English translation in `translation/en/` | MIT (`LICENSE`) |
| `tools/font/Inter-*.otf` | SIL Open Font License 1.1, see `tools/font/LICENSE-Inter.txt` (The Inter Project Authors) |
| `docs/logo.png` | Custom design by a project contributor, published for this project's README |
| The patch data inside `release/KimiKiss_EN.xdelta` | Derived from the original game; distributed only as a difference, as is usual for fan patches |

## Credits

- Disc, script and texture formats were worked out partly from the format knowledge in [21-ko/AMAGAMI-translation-tools](https://github.com/21-ko/AMAGAMI-translation-tools) (MIT, for Amagami, the same engine family). `tools/extract/scf.py` says where it differs.
- PCSX2 was used for testing; Ghidra for reverse engineering of the executable.
- Fan translators of Amagami (Ni-shi-shi Translations, Spazzery's Temple) showed which problems this engine family has.
