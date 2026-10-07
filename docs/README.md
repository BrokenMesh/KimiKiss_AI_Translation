# Documentation index

## For players

- [GETTING_STARTED.md](GETTING_STARTED.md): apply the patch or build it yourself, play in PCSX2, report bugs.
- [source-iso.md](source-iso.md): the exact disc edition the patch needs and its checksums.

## For translators

- [../CONTRIBUTING.md](../CONTRIBUTING.md): how to fix a line, check it and play it.
- [translation-format.md](translation-format.md): the format of `translation/en/*.txt`, escapes, control codes, stale lines.
- [glossary.md](glossary.md): names, honorifics, who calls whom, terms. Decided by the project owner; changes go through the maintainers.
- [route-notes/](route-notes/): per-route notes on running jokes and decisions for consistency.
- [../tools/translate/TRANSLATOR.md](../tools/translate/TRANSLATOR.md): the full brief (length limits, line breaks, tone).
- [phase-5-pipeline.md](phase-5-pipeline.md): export/import/check commands and the file formats behind them.

## For tool and patch developers

- [pipeline.md](pipeline.md): every command of the pipeline, extraction to ISO. (The Ghidra and PCSX2 sections at the end describe the maintainer's own environment and are not needed to build or translate.)
- [formats/](formats/): the file formats of the disc (ISO/UDF, ARC, IMG, SCF scripts, TIM2 textures, LZSS, the font).
- [phase-3-text-engine.md](phase-3-text-engine.md), [phase-3-notes.md](phase-3-notes.md): how the game draws text and what was patched in the scripts.
- [phase-4-textures.md](phase-4-textures.md), [phase-4-textures.tsv](phase-4-textures.tsv): text in images and the hand-made texture mechanism.
- [phase-4-name-entry.md](phase-4-name-entry.md), [phase-4-system-text.md](phase-4-system-text.md), [phase-4-elf-strings.md](phase-4-elf-strings.md): name entry, system text limits, hard-coded strings in the executable.
- [size-budget.md](size-budget.md): space and memory limits on disc, in the executable and in the VM.
- [qa-scfvm.md](qa-scfvm.md): the offline script interpreter used by the tests.

## History

- [decisions.md](decisions.md): the numbered decision log (D-001 and on). Every design choice, with the reason and what was seen in the emulator.
- [project-plan.md](project-plan.md): the original phase plan.
- [phase-0-status.md](phase-0-status.md), [phase-1-2-report.md](phase-1-2-report.md): the first phases' reports (tool setup, recon).
