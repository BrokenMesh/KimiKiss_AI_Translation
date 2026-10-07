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

## D-015: Proportional menu text through one helper method

- Menus, dialogs and lists draw with `TextLine` (left-aligned) and `TextLineC` (centred), one `FontChar` per character at `posX + i·pitch` (centred: minus `(n−1)·pitch/2`). This is computed in `setText:`, `setPos`, `restart` and `move:` of both classes.
- A new method `TextLine >> xOf: i` returns the x offset of character `i` of `text`: the sum of the advances before it. Japanese and other codes advance by `pitch`; English codes by `width · pitch / 24`, the glyph's share of its 24 px cell. All eight sites call it: `i·pitch` becomes `self xOf: i`, the centring term becomes `((self xOf: n) − pitch) / 2`.
- Japanese positions are unchanged, except that the centring term is now a float division, so a centred line with an odd `(n−1)·pitch` moves by half a pixel.
- `setText:` stores `text` before placing glyphs (both classes), and `TextLine >> setText:` ends with `self setPos`, because glyphs reused from the previous text keep their old position.
- The alternative, keeping menus fixed-width with character limits, was rejected: the English glyphs are narrow and left-aligned in their cell, so fixed spacing leaves visible gaps after narrow letters.
- Verified in PCSX2: the name-entry confirm dialog (`ConfirmDialog`, centred `TextLineC`) shows "Use this name? little WWW" evenly spaced and centred, with no gaps after narrow letters. The Japanese name-entry grid and the dialog buttons render as before.

## D-017: Dialog box and deck-name width follow `xOf:`

- `ConfirmDialog >> initialize:` (7 args) sized the box as the longest line in characters x pitch (18). With English that gives boxes far too wide. The patch keeps the character pass (it still supplies the wrap width for an explicit `width`, and the engine clamp `< 128 -> 96`, `> 608 -> 576`, else `-32` is untouched). When `width` is nil it now measures the `TextLineC` lines it has just built: per line `line xOf: text length`, plus one pitch for every line after the first (the original counted the break character as the first character of the next line), and the maximum replaces `textW` before the `DialogBox` is scaled. The width logic stays in one place, `TextLine >> xOf:` (D-015); `ConfirmDialog` adds only a max loop.
- Japanese is identical: `xOf:` of an all-Japanese line is exactly `n * 18`, so `textW` is the same number (float instead of int, same value). Checked with a small bytecode interpreter on all 185 `ConfirmDialog` messages, plus explicit widths 50 / 200 / 400 / 700: same `DialogBox` arguments and same `TextLineC` arguments and texts. The only difference left is a message whose every line is narrower than one full-width character and which ends in a line break.
- The nil-width path is still not clamped (as before). English lines must stay within 576 px (`limits.json`); a 32-character Japanese-width line was already the limit.
- `DeckView >> setName` drew up to 6 `FontChar`s at a fixed 26 px pitch. It now builds a measuring `TextLineC` (pitch 26, scale 1.0, same layer), takes glyph x from `xOf:` with the same centring as before, then destroys the measuring line's glyphs. The glyphs are still plain `FontChar`s in `name`, so `openName`, `closeName` and `change` (zoom, fade) are untouched. The 6-character cut was a pure display cut of the stored name, so it became a pixel cut: characters are dropped from the end while the line is wider than 156 px (6 x 26). For Japanese this is the old 6 characters.
- `DeckListItem` (deck list rows) already draws a `TextLine`, so D-015 covers it; nothing else draws text with its own pitch except `NameEntryEdit` and `ShioriListItem`, which are patched separately.
- Not run in the emulator. To check: new test line `NameEntry:4` (two-line message, box must be as wide as the longer line plus one pitch for line 2); deck screen with an English deck name.
