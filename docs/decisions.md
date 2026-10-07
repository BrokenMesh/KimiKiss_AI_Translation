# Decisions

## D-001: Source ISO lives outside the repo

- The user's disc image is stored at `../kimikiss-private/kimikiss.iso` relative to the checkout (override with `KIMIKISS_PRIVATE_DIR`). `tools/build/fetch_iso.sh` refuses a destination inside the repo.
- The image is read-only (`chmod 400`). Builds copy it into `build/`, which is gitignored.
- The first ingest records the SHA-1 in `tools/build/iso.sha1`. Every later ingest and build must match it.
- Defense in depth: `.gitignore` covers disc image, ELF, and IRX extensions plus `build/`, `text/`, and `qa/`. `tools/githooks/pre-commit` rejects staged ISO9660 images, ELF binaries, and files over 5 MiB regardless of name.
- Cloud session containers are ephemeral, so the ISO must be fetched again in each new session.

## D-002: Target edition is SLPS-25850

- The user's disc is the eb!Kore+ re-release (SLPS-25850, volume `KIMIKISSPLUS`), not the 2006 first print the brief names. Patches target this image only. Details are in `docs/source-iso.md`.
- Whether this edition's content differs from the 2006 first print has not been checked yet.

## D-003: Phase 0 deferred

- The user asked to start at Phase 1. Phases 1 and 2 need no emulator or Ghidra, so they were done first. Gates G0 and G1 remain open and must pass before Phase 3.

## D-004: Own SCF parser instead of the Amagami one

- `parser_scf.py` misreads type-8 array constants (see `docs/formats/scf.md`). `tools/extract/scf.py` is a strict parser and serializer that checks counts and requires exact EOF. All 386 members round-trip.

## D-005: Okumura LZSS encoder

- `tools/lzss/lzss_enc.c` is Okumura's 1989 binary-tree encoder with the engine's parameters. It reproduces SCRIPT.IMG and GRAPH0.PAC byte for byte, so Gate G3 holds for the compressed files and not only for their contents. It needs gcc at build time.

## D-006: Text JSON escapes control codes in braces

- Every ASCII control token in a line is written as `{token}` (for example `{V0858}`, `{W30}`, `{Nn}`). Characters the tokenizer doesn't recognize are braced one by one, so `unbrace()` is always lossless. The extractor refuses input that already contains braces.
- Translators can move or keep codes as whole tokens. Plain text outside braces will be encoded by the Phase 3 English encoding.
- `／` stays a literal line break for now. Wrapping rules come with the font patch.

## D-007: File classification by script, not by Haiku

- The brief assigns file classification to Haiku. The disc has 24 files in 4 container formats, and a deterministic script with magic-byte and structure checks gave an exact answer, so no model delegation was needed.

## D-008: Textures exchanged as indexed PNG

- TIM2 converts to 8-bit indexed PNG with the original header stored in a tEXt chunk. Alpha is scaled when all entries are ≤ 0x80 and copied raw otherwise. Pure Python, no Pillow dependency.

## D-009: Tool versions and where they live

- Ghidra 12.1.3, ghidra-emotionengine-reloaded built for 12.1.3, GhidraMCP 7.0.0-rc.1 (the first release that declares 12.1.3 support), PCSX2 v2.9.108. The extension versions must equal the Ghidra version exactly.
- Tools live in `/home/user/kimikiss-tools`. The BIOS and the Ghidra project (derived from the game binary) live in `/home/user/kimikiss-private`. Nothing from either directory enters the repo; `.gitignore` also covers BIOS companion files (`.EROM`, `.ROM1`, `.NVM`, `.MEC`, ...).
- The Japanese BIOS (77000) is used, matching the NTSC-J disc.

## D-010: PINE is used serially only

- `pine_get_info` pipelines opcodes; one dropped reply desyncs mcp-pine's reply queue. QA scripts use only serial PINE calls and keep modal dialogs off (null audio), see `docs/phase-0-status.md`.

## D-011: Font and layout patch in script bytecode, not ELF assembly

- The brief's Phase 3 step 4 assumes assembly patches. In this engine the control-code parser (`Parson >> message:`), layout, advance and wrap (`TextWindow >> putChar:`, `crlf`), menus (`TextLine >> setText:`) and backlog (`LogLine`) are all SCF bytecode in `SCRIPT.IMG`. The native glyph lookup (`SjisToGlyphIndex`, `0x0017f750`) already maps every Shift-JIS row into the font texture.
- The variable-width patch is therefore a rewrite of those script methods plus a new font texture. `SCRIPT.IMG` is rebuilt anyway for the translation, so this costs no extra ELF patching and no code cave.
- Script patches are recorded in `patches/` in the same way: class, method, original bytecode, new bytecode, reason.
- ELF assembly patches stay the fallback if a native limit turns up, for example in Phase 4 for hard-coded strings.

## D-012: English encoding

- Printable ASCII `0x20`–`0x7E` (95 characters) is stored as Shift-JIS codes in row 9/10 of the font: character index `i = c − 0x20`, code `0x85 << 8 | t`, with `t = 0x40 + i` for `i < 63` and `t = 0x41 + i` otherwise (skipping trail `0x7F`). For example, space is `0x8540`, `A` is `0x8561` and `~` is `0x859F`.
- Reason: single-byte codes are control codes or dropped (see `docs/formats/scf.md`), and these rows hold only placeholders. Keeping the original full-width Latin and Japanese glyphs intact keeps untranslated text and debug strings readable.
- Control codes stay plain ASCII exactly as in the original, so `{V0858}`-style tokens pass through the reinserter unchanged.
- Rows 11–12 and 14–15 stay free for extras (italics, ellipsis, accented letters).

## D-013: Width table in script, word wrap at reinsertion, pixel fallback in the engine

- Each English glyph is drawn left-aligned in its 24 × 28 cell. A width table, stored as an array constant in each patched class, gives its advance in pixels at scale 1.0. `putChar:` advances by `width·fontSclW` for English codes and keeps `fontW·fontSclW + pitchX` for everything else.
- Word wrap: the reinserter inserts `／` at word boundaries using the same width table and the window geometry (552 px line, continuation indent 92 px, 3 lines). This matches how the original script already breaks lines by hand.
- The engine's overflow check in `putChar:` stays as a safety net. It is changed to test the glyph's real width.
- Dynamic text (`Nn`/`Nm` names, `dispName`) is measured at its worst case: the longest name the name-entry screen allows. That limit is to be read in Phase 4.

## D-014: UDF bridge left stale for now

- `tools/build/iso_patch.py` updates only ISO9660 directory records. PS2 hardware (`sceCdSearchFile`) and PCSX2 read ISO9660, and the Phase 3 gate passed with a relocated `GRAPH0.PAC`.
- The image's UDF descriptors still point at the old extents. This matters only for PC tools that read UDF. Update them before release.
