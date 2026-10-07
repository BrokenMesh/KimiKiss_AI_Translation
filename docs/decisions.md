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

## D-014: UDF bridge kept in step with ISO9660 (resolved)

- Originally `tools/build/iso_patch.py` updated only the ISO9660 directory records, which is all PS2 hardware (`sceCdSearchFile`) and PCSX2 read, and the UDF file entries kept pointing at the old extents. Fixed before release.
- The image is a UDF 1.02 bridge (NSR02). File data is shared: UDF block = ISO9660 LBA - 265, same length. Every file has one File Entry with one short_ad. Layout and tag rules are in `docs/formats/iso.md`.
- `iso_patch.py` now also rewrites, for each patched file, the FE information length, logical blocks recorded and short_ad, then recomputes the tag CRC (CRC-ITU-T, using the CRC length stored in the tag) and checksum. The UDF code is in `tools/build/udf.py`.
- The relocation limit was wrong: it was the ISO9660 volume size (618,944), but the UDF partition ends at 618,943 and the last sector is the trailing Anchor. It is now the partition end. If a build outgrows it, the image grows (ISO9660 volume size, both partition descriptors, LVID size table, trailing Anchor moved). Current builds relocate about 1.8 K sectors into 10.2 K free ones, so growth is not triggered; it was tested with synthetic files.
- `tools/qa/check_iso_udf.py <iso>` walks both trees and checks LBA and size agreement, tag checksums and CRCs, anchors, both VDS copies, partition bounds, LVID, extent overlaps. `tools/build/build.sh` runs it as its last step and fails the build on any problem. It passes on the clean image and on the test build.
- No independent UDF reader (7z, isoinfo, xorriso, kernel udf driver) is installed in the cloud container, so the check is by our own parser only. To cross-check outside the container: `7z l <iso>` or `isoinfo -i <iso> -l -R` on a PC, plus mounting the image on Windows or Linux (both prefer UDF).

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

## D-016: Name entry takes 8 + 8 English characters (bytecode patches)

Written after D-017; the number was reserved for the name-entry work of `docs/phase-4-name-entry.md`.

**What changed** (`patches/scripts/NameEntry*.asm`, `Parson.setDispName1.asm`, `ShioriListItem.initialize2.asm`, `ShioriData.serialize0.asm`, `ShioriData.cut1.asm`; `@EN_SYMBOLS` in `tools/reinsert/apply_script_patches.py`; default names in `tools/qa/make_en_test_text.py`):

- `NameEntryEdit` has 2 x 8 slots in player mode (6 in deck mode). The cursor positions are `0` back, `1..16` slots, `17` confirm (`slots + 1`; `NameEntry` asks the edit object instead of using the literal 7). New helper methods give the geometry (`slots`, `fieldN`, `fieldW`, `fieldL:`, `emptyW`), `adv:` gives the advance of a slot's code, `layout` places everything.
- Layout: two fields at x -44..38 and 46..128 between the two diamonds (82 px each), one scale for both, `s = min(1, 82 / natural width)` where an empty slot counts 13 px. `Aihara` / `Koichi` get 0.85, 8 x `W` get 0.47, 8 full-width Japanese characters get 0.43. Glyph centres at `left + 12 s`, constant baseline, underline stretched to the slot, cursor box follows the slot. The deck name keeps its geometry (one field of 6 cells, empty slot 24 px, scale 1), only proportional glyphs. This replaces the doc's fixed 0.75 scale and the 96 px cap, because the cap would refuse 8 full-width characters (the requirement says they must still fit by scaling).
- Typed codes go through `toEnglish:`: full-width digits, capitals and lower case `+0x301` (`Ａ` 0x8260 -> 0x8561), the full-width blank 0x8140 -> space 0x8540, and 31 symbols with an ASCII twin (`@EN_SYMBOLS`: `， ． ： ； ？ ！ ＾ ＿ ‐ ～ ‘ ’ “ ” （ ） ［ ］ ＋ － ＝ ＜ ＞ ＄ ％ ＃ ＆ ＊ ＠`). `／` and `｜` are left alone (line break and pause codes). Every other code, English ones included, is unchanged. Deck names use the same mapping.
- Names are read by `getStr: from to:`: leading and trailing blanks (0x8140 or 0x8540) are dropped, an inner blank becomes 0x8540. An empty field still restores the current name. `getStrH`, `getStrL` and the deck `getStr` call it.
- The entry screen opens on the 英数記号 page (`NameEntryList >> run` page 3, menu row and `curY` 3 in `NameEntry >> scriptMain`). The history page has four 96 px columns (x -124, -28, 68, 164, cursor 96 px wide).
- `Parson >> setDispName:` keeps the whole surname (empty gives the blank 3-cell plate). `ShioriListItem >> initialize:` measures both names with `xOf:` and uses text scale 1 up to 150 px total, 0.75 up to 200 px, else 0.5; Japanese names of up to 3 + 3 characters land on exactly the old positions (checked in a script interpreter).
- Defaults: `GameParam:166` `Aihara`, `GameParam:167` `Koichi`, `K2_Script:13` `Aihara` are ordinary text records, so they are set through the translation JSON (the test builder does it).

**Save header measurement** (`ShioriData` / `SerializeData` / `MemoryCard`):

- The slot header is exactly 256 bytes. `MemoryCard` primitive 6 (`writeAllData`, command 6, handler `0x0010ae00`) writes `0x100` bytes from the header ByteArray whatever its length, then the body at `slot * 0x2800 + 0x100`; `ShioriData class >> load:` reads 5120 bytes and slices 20 x 256. A longer header is silently cut. The reader then fails inside the `try` of `load:`, which blanks all 20 slot headers (inferred, not run).
- `String >> toByteArray` (`0x00116898`) writes high byte then low byte for every 16-bit code above 0xFF, so a 0x85xx code takes 2 bytes. `String newFromByteArray` (`0x00116284`) treats any byte with bit 7 set as a lead byte and rebuilds `(lead << 8) | trail`. `Integer >> asChar` (`0x00119358`) builds the 2-byte string for codes above 0xFF. A 0x85xx code therefore round-trips through save and load, and the existing prologue text already uses them.
- Size, measured by running the real `ShioriData >> serialize`, `SerializeData >> serialize:` and `FavorBase >> makeArray` bytecode in an interpreter: **header = 200 + 3 k + 2 (chars of Nm + chars of Nn) bytes**, where k is the number of non-nil entries in the two-element `bad` arrays of the 8 `FavorBase` records (0..16). The doc's 216 fixed bytes assumed four ints per girl and was wrong. Names may therefore use `56 - 3 k` bytes: 28 characters at k = 0, 16 at k = 8, 4 at k = 16. The original game with 3 + 3 characters already overflowed at k >= 15 (260 bytes).
- **N = 8 + 8** as required: it fits for k <= 8. For k > 8 the patched `serialize` shortens its own copy: it serializes, and while the result is longer than 256 bytes drops the last character of the longer name (header copy only; the game and the save body keep the full names). Worst case the slot list shows truncated names for that slot; the file is never cut.
- The save body (`GameParam >> makeShioriBody`, 9984 bytes per slot) holds the names too. Its size was not bounded here; the names add at most 20 bytes more than the original maximum of 12.

**Risks left** (nothing here ran in the emulator; the new methods were run in a Python bytecode interpreter against stubbed `FontChar` / `Sprite` / `TextLine`, including a random input fuzz and the header sizes above):

- Layout assumptions: a `FontChar` position is the centre of its 24 px cell and scales about the centre (derived from the centred `TextLineC` code); the underline sprite 142 is taken to be 24 px wide and the cursor box 25 px. If the underline is another width it will look too short or long.
- No pixel cap: 8 x `W` is 176 px (8 full-width characters 192 px), while `en_text.NAME_PX` reserves 156 px per `{Nm}` / `{Nn}`. A typical 8-letter name is about 100 px. The engine's overflow check wraps a line that is too long, but the budget in `en_text.py` should be revisited.
- The history page and the plate are not scaled; a name wider than 96 px overlaps the next column, and a plate wider than the 92 px indent only changes where line 1 of the text starts.
- The grid still shows the full-width glyphs (the mapping is on input); the tab names and button guides are textures. Rewording row `64.3.6` to put `．` or `’` on the grid is a text task.
- Voice clips, the confirm dialog text and the 履歴 contents are unchanged.

## D-018: Offline bytecode interpreter as the first patch check

- `tools/qa/scfvm.py` runs real SCF bytecode with native classes stubbed and their calls logged; `tools/qa/test_patches_jp.py` runs every patched method and its original on Japanese inputs and fails on any difference in the logged draw calls (details: `docs/qa-scfvm.md`). Every patch must pass it before an emulator run; the emulator stays the final check for how English looks.
- Its first run found two patch bugs, both fixed: `TextLine >> xOf:` read past the end of `text` when `setText:` had left glyphs of a longer previous text in `fList` (crashed the staff roll; `xOf:` now clamps `i` to the text length), and `Parson >> setDispName:` used the `and` opcode as a guard, but `and` evaluates both operands, so a nil name sent `isKindOf:` to nil (now two jumps).
- Rule for patches: `and`/`or` never guard a send or an index; use jumps.
- Emulator check of D-016/D-017 (PCSX2, test build before the D-018 fixes): the name entry opens on the 英数記号 page with "Aihara" / "Koichi" in proportional English; letters typed from the grid enter as English codes (Ａ→`A`, ２→`2`), symbols without an English glyph (…, ♀) stay full-width, and the field holds 6+ characters without overlap; the quit dialog shows the two-line English message centred in a box that fits it; the confirm dialog shows its English message. Not yet seen in the emulator: names inside dialogue and the name plate, save/load of English names, deck naming.

## D-019: Texture text is redrawn at build time, from labels and the original palette

- The English UI text of the `GRAPH0` textures is not stored as images. `tools/texture/labels.tsv` (entry, Japanese, English, notes) and `layout.tsv` (box and background rule where needed) are the tracked source; `tools/texture/redraw.py` decodes each original TIM2, erases the Japanese text, draws the English with Inter (system font, SIL OFL, see `tools/font/LICENSE-Inter.txt`) and maps every pixel to the palette entries the texture already uses. This keeps game art out of the repo (`text/` is ignored for the same reason), keeps the results reproducible, and means a change of wording is a one-line edit.
- Same TIM2 length, same palette, same header, pixels changed only inside the label boxes. So no ARC offset or size moves, and the font path is unchanged: `tools/texture/apply_graph0.py` replaces entry 77 and the textures in one pass over the original archive and writes `GRAPH0.ARC` and the LZSS `GRAPH0.PAC`. `tools/font/apply_en_font.py` still works on its own (font only). `build.sh` still verifies the ISO hash and starts from `build/orig`, which is extracted from the verified image.
- Build dependency: Pillow, numpy and an Inter OTF. The font glyph sheet (`en_font.pgm`) needed none of them at build time; textures do.
- Limit: the first list (109 textures from a thumbnail pass) was wrong in both directions. A second inventory of all 551 `GRAPH0` textures found 216 with Japanese UI text, all redrawn (220 lines). Open: entry 453 (captions over art) is poor; 18 full-screen help pages and one bubble label in `GRAPH1` are untouched (the pipeline handles `GRAPH0.ARC` only). See `docs/phase-4-textures.md`. Check: `tools/qa/test_graph0_textures.py`.

## D-020: Hand-edited textures come from a private directory, as PNG overrides

- Textures that cannot be redrawn automatically (entry 453, the 18 GRAPH1 help pages, art with painted text) are drawn by hand. The results are game-derived images, so like the ISO (D-001) they live outside the repo: `$KIMIKISS_OVERRIDES`, else `$KIMIKISS_PRIVATE_DIR/texture_overrides`, else `../kimikiss-private/texture_overrides`. `tools/texture/overrides.py` refuses a directory inside the repo unless git ignores it; `.gitignore` lists `texture_overrides/`. No directory means the build is byte-identical to the one before this change (checked: the test ISO has the same SHA-1).
- Files are `GRAPH0_NNNN.png`, `GRAPH1_NNNN.png`, `GRAPH2_NNNN.png`, the entry numbering of `tim2.py topng`. The PNG must have the original size. It becomes the entry's TIM2 with the original header and length (no ARC offset moves). Indexed PNG with a palette of the original size: its palette is used (new palette allowed, alpha convention of D-008 from the original). Anything else: nearest existing palette entry (the quantizer of `redraw.py`), pixels equal to the original keep their index. An override replaces the automatic redraw of that entry. Wrong size, unknown entry, non-TIM2 entry, the font entry and duplicates stop the build with a message.
- GRAPH1 and GRAPH2 are not stored like GRAPH0: no PAC, no LZSS; each TIM2 is raw inside the `.ARC`, which the engine opens as a stream (`LoadGraph1` 0x00104738, `LoadGraph2` 0x00104928; only `LoadGraph0` references `GRAPH0.PAC`). So the patch is a same-size write at the entry's offset (`tools/texture/apply_graph12.py`), and `iso_patch.py` writes the 172 MB / 239 MB file back in place. GRAPH0 overrides go through `apply_graph0.py` into ARC and PAC (project LZSS encoder). Based on disassembly and file structure; not yet seen in the emulator.
- `build.sh` runs `apply_graph12.py` after `apply_graph0.py` and adds `GRAPH/GRAPH1.ARC` / `GRAPH2.ARC` to the `iso_patch.py` list only if the step wrote them. Tests: `tools/qa/test_graph_overrides.py`.
- Cost of the choice: a build with GRAPH1/GRAPH2 overrides handles a 172 MB or 239 MB copy and rewrites it into the image; builds without them are unchanged. Pillow and numpy were already needed for D-019.


## D-021: Wrapping runs in the build, not in the reinserter

- D-013 said the reinserter inserts the `／` breaks; it never did (only the test-text builder wrapped). `build.sh` now runs `tools/translate/batch.py prepare` on the text directory first (dialogue wrapped with `en_text.wrap` and the speaker-indent rule, ConfirmDialog lines wrapped), and `reinsert_text.py` reads the prepared copy in `build/work/text`. Translators write unwrapped English; the checker (`tools/qa/check_translation.py`) measures the prepared form. Already-wrapped lines pass through unchanged.

## D-022: English lives in translation/en/*.txt, keyed by record id and a hash of the Japanese

- Until now translations were stored as a `translation` field in `text/*.json`, which is gitignored because it holds the Japanese game text (D-001). The repo is going public and people must be able to fix one English line with a pull request, so the English moves to `translation/en/<SCENE>.txt`: committed, one file per scene, one header line (`@<id> <speaker> <src>`) and one translation line per record, comments allowed. `src` is the first 8 hex digits of the SHA-1 of the Japanese text, so the file proves which Japanese a line was written against without containing any of it. No Japanese text enters the repo (the importer and `tools/qa/test_translation_store.py` refuse it).
- `text/` stays Japanese only and local. `tools/translate/store.py` reads, writes and syncs the format; `batch.py export/import/prepare/sync/show/migrate` and `check_translation.py` read the English from the store (`--trans`, default `translation/en`). `prepare` merges both into the wrapped JSON the reinserter reads, so `tools/build/build.sh <iso> <out.iso>` builds with the committed translation. Format and contributor guide: `docs/translation-format.md`.
- Changed Japanese does not silently invalidate English: `sync` keeps the line and marks it `# STALE src`, `check_translation.py` warns `SRC_STALE`, and `sync --accept-src` records the new hash after review.
- Reasons: the repo is public, a fix must be a one-line diff in a plain text file, and contributors need no JSON tooling. Cost: a sync step when the extractor output changes, and `／` (the choice separator) is the one non-ASCII character that appears in the files.


## D-023: Speaker plate column is 5 cells, and line 1 starts at it

- `Parson>>message:` prints the speaker plate, then `putIndent: 4`, which only set the indent of lines 2-3 (92 px); line 1 continued straight after the plate. The Japanese plates are 3 cells and the hanging `「` filled the gap, so the text of line 1 lined up with lines 2-3. English plates have no bracket and are wider (Mizusawa 107 px, Satonaka 100 px, the player's surname up to 120 px), so the text either touched the plate or started right of the indent.
- Two patches: `Parson.message1.asm` sends `putIndent: 5` (115 px); `TextWindow.output0.asm` makes command 7 (sent only there, only after a plate) also move the pen to the indent column, or 6 px after the plate when the plate is wider. Narration has no plate and no indent and is unchanged.
- Budget: `en_text.INDENT_PX = 115`, `PLATE_GAP_PX = 6`; `rules.label_px_for` returns `max(115, plate + 6)`. A spoken line has 437 px on every line (552 for narration). The glossary keeps plates at most 115 px (D9).
- Untranslated Japanese lines also start at 115 px, one cell further right than before: 19 instead of 20 cells on lines 2-3. Accepted, all dialogue is translated. The backlog (`LogLine`) is not changed.
- Emulator (2026-10-07, `build/pilot.iso`, translated prologue, `qa/p5b/`): line 1 lines up with lines 2-3 under every plate (Nana, Aihara, Hiiragi, Boy); plate and text keep the same layout in the backlog (`bl2.png`, `bl3.png`). The player's thoughts carry the surname plate too and get the same column.

## D-024: The message window starts a new page when the next message does not fit

- The window is not cleared per message. Scene scripts clear it themselves (`K2_Script.WIN clear` after a `:` send) and let short messages share the 3-row page: in a static scan of all scene methods (`push_const <record>` / `#:` sends between `WIN #clear` sends), 11,106 pages hold one message and 11,026 hold two or more (8,744 two, 1,797 three). Each message ends with `crlf`, so the next one starts on the next row, and nothing checks the row count (`crlf` only adds `pitchY`). English rows differ from the Japanese ones: in the translated prologue 4 of the 99 lines would have pushed a page past row 3 (e.g. `PLY_PRO:144-146`, Japanese 1+1+1 rows, English 1+2+2).
- Fix in the engine, not in the text: `TextWindow.pageFor1.asm` (new) counts the rows of the message (its `／` breaks + 1; the build's word wrap writes them) and the rows already used (`(curY - (posY + marginY + pitchY/2)) / pitchY`, the inverse of `erase` and `crlf`), and calls the window's own `clear` (fade 3, erase) when they add up to more than 3 and the page is not empty. `Parson.message1.asm` calls it first. Japanese pages fit as authored, so they never trigger it.
- The alternative, a per-page budget in the checker, would have tied each English line to the length of its Japanese neighbours on the same page, which is not workable for translation.
- Limit: a row added by the engine's overflow wrap (a typed name much wider than the 120 px reserve, a single word wider than the line) is not counted. Not yet seen in the emulator.
- Emulator (2026-10-07, `build/pilot.iso`, `qa/p5b/`): pages that fit still stack as authored (`PLY_PRO:144-145` 1+2 rows, `059`, `065`, `108`); a message that does not fit opens a new page (`146` after 1+2 rows, `098.png`; `153` after 2 rows, `116.png`; `158` after 3 rows, `130.png`). No message ran past row 3 in the 150 shots; no crash.

## D-025: Bulk translation runs per route, in chunks, one translator at a time per route

- 35,043 lines (1.16M Japanese characters) in 220 scenes are split into 46 chunks of at most about 32,000 characters, each a run of whole scenes of one route (ASU, ERI, MAO, MIT, NAR, YUM, MEG, NAN, PLY), plus one chunk of shared and system text. Within a route the scenes go in an assumed story order (PRO, DEA, the short events, DAT, GKD, KOK, KIS, SEV, MW1-3, FEV, ALB); the scene codes are not documented, so the order is a guess that only affects which agent sees a scene first.
- One translator model per chunk, with `tools/translate/TRANSLATOR.md`, `docs/glossary.md` sections 0-2 and the reviewed pilot `PLY_PRO` as references. It exports with `batch.py export --format text`, writes answers in parts of at most 120 records, imports each part with `--normalize`, and must leave no FAIL in `check_translation.py`. Guesses go to `build/batch/<SCENE>.notes.md`.
- Only one chunk per route runs at a time. Each agent appends route decisions (renderings of recurring phrases, nicknames, running jokes) to `build/batch/notes/<ROUTE>.md` for the next agent on the route; glossary changes are proposed there, never made by the translators.
- After each wave: a review of every WARN and a sample of lines per chunk, fixes, then a commit. Concurrent agents never touch the same scene file (`batch.py import` rewrites only the scenes it imports).

## D-026: The rest of the translation goes through the API, not agent sessions

- The agent waves of D-025 cost about 280k model tokens per 950 lines, most of it the agents re-reading their own growing context, and they used up the session's usage limit after 8,400 lines. `tools/translate/api_translate.py` sends one plain request per scene part instead: at most 150 lines to translate, the already translated lines of the scene as `~` context and the six Japanese lines before the part, with a fixed system prompt (`TRANSLATOR.md`, `docs/glossary.md` sections 0-2, the reviewed pilot `PLY_PRO`, the route notes in `docs/route-notes/`) that is cached. Same model family as the agents (Sonnet), effort `medium`.
- Measured on `ASU_GKD_B` (100 lines): 5,005 output tokens, about 0.06 USD of request cost plus the one-time cache write; 2 of 100 lines failed the checker with a dropped `{W..}` and were fixed by the repair pass. Sampled quality matched the agent waves.
- The remaining 26,612 lines go in one Message Batch (244 requests, half price). Answers are imported with `batch.py import --normalize`; `api_translate.py repair` sends every line that FAILs `check_translation.py` back once with the checker's message. Usage and cost per request are logged to `build/api/usage.jsonl`.
- The API key is read from `ANTHROPIC_API_KEY` or a file named by `ANTHROPIC_API_KEY_FILE` outside the repo; it is never written into the repo.
- Outcome (2026-10-07): the batch returned all 244 parts (26,445 lines imported); 4,302 lines failed the checker, 3,924 of them only because short in-word waits were dropped. `tools/translate/fill_waits.py` put those waits back after the English word at the same relative position (no model call); two repair rounds and 18 hand fixes cleared the rest. Result: 35,156 lines checked, 0 FAIL; `build.sh` builds the full ISO and the UDF check passes. API cost 17.05 USD in total. Spot checks find occasional meaning errors (e.g. ERI_FEV:207, a statement read as a question) and inconsistent terms between a choice and the line after it; a read-through review is still needed before release.
