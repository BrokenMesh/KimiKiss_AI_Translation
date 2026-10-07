# KimiKiss (PS2) English Translation: original project plan

> History. This is the brief the project started from (written for AI agents that did part of the work); the current state is in `docs/decisions.md` and the README.

## Objective

Produce an English translation patch for **KimiKiss** (キミキス, Enterbrain, PS2, 2006). Deliverables:

- An xdelta patch.
- The tooling to rebuild that patch from a clean disc image.

This is **not** a full decompilation. Decompile only the code paths that handle text: the script interpreter, glyph lookup, text drawing, line wrapping, and character advance width.

## Hard constraints

- Work only from the disc image the user provides, which they dumped from their own copy. Never download game images, BIOS files, or assets.
- Never commit or publish the ISO, the BIOS, extracted game files, or a patched ISO. Ship xdelta patches and tools only.
- Never edit the original ISO. Every build starts from a clean copy, and the build fails if the input ISO's checksum does not match the recorded value.
- Each phase ends at a gate. If a gate fails, stop, write up the findings, and report them to the user. Do not work around a failed gate silently.
- Log every decision and every reverse-engineered format to `docs/` as you go. Treat this documentation as a deliverable, not an afterthought.

## Reference material

| Resource | Use |
|---|---|
| https://github.com/21-ko/AMAGAMI-translation-tools | MIT. Tools for Amagami (same developer, 2009); folders `scf/`, `tm2/`, `img/`. It has no README, so read the code. This is the primary hypothesis for the formats. |
| Ni-shi-shi Translations' Amagami English patch (PS2/PSP, v1.0.0, Dec 2023) | Strategic reference. It was split into 3 patches because of space limits, and it has known backlog crashes on PS2. Expect the same pressures here. |
| Amagami Vita English patch (Spazzery's Temple, 2025) | It ported Ni-shi-shi's documentation and code changes, which is evidence that code-level patches exist in this engine family. |
| https://github.com/bethington/ghidra-mcp | Ghidra over MCP. Use it for string search, cross-references, decompilation, renaming, and commenting. |
| PCSX2 (Qt build) | Emulator for runtime verification. |
| https://github.com/dmang-dev/mcp-pine | MCP wrapper over PCSX2's PINE IPC. Provides memory read/write and save-state load/save. |

## Model delegation

| Work | Model |
|---|---|
| File signature classification, directory surveys, running known extractors in bulk | Haiku |
| Byte-budget, control-code, and glossary compliance checks on translated lines | Haiku |
| Screenshot triage: "contains Japanese / overflow / garbled? yes/no + location" | Haiku |
| Batch application of decided names and comments in Ghidra | Haiku |
| Format reverse engineering, parser and reinserter code | Sonnet or stronger |
| Renderer and font patch design and implementation | Strongest available |
| Translation | Strongest available |
| Review of anything Haiku flags | Sonnet or stronger |

Rule: Haiku gets pass/fail checks and mechanical bulk work with an explicit spec. Anything that needs judgment about code or prose goes to a stronger model.

## Repository layout

```
kimikiss-en/
  docs/            formats, decisions, findings, ghidra notes
  tools/           extract/, reinsert/, font/, build/, qa/
  text/            extracted JSON (gitignored if it contains original text)
  translation/     translated JSON + glossary
  patches/         asm/code-cave patches for the ELF
  build/           gitignored: working ISO copies, outputs
  qa/              screenshots, logs (gitignored)
```

## Phase 0: environment and gates

1. Install PCSX2 (Qt). Enable PINE under Settings > Advanced (port 28011). Install `mcp-pine`.
2. Boot the unpatched ISO with `pcsx2-qt -batch -nogui -fastboot -- <iso>`.
   - `-nogui` hides the main window but still needs a display, so on Linux use a virtual display (Xvfb).
3. Find a screenshot path. Candidates: PCSX2's built-in screenshot hotkey sent via xdotool, or window capture of the Xvfb display.
4. Check the PINE connection: read EE memory and read run status.
5. Install Ghidra 12.1.3 with bethington/ghidra-mcp. Find and install a PS2 Emotion Engine (MIPS R5900) processor/loader extension, and verify it works with Ghidra 12.1.3.

**Gate G0:** a script boots the game, waits, captures a PNG of the title screen, and exits cleanly. If impossible, report the options to the user: a visible desktop capture, or manual screenshots.

**Gate G1:** the main ELF (`SLPS_xxx.xx`) loads in Ghidra, auto-analysis completes, and one function decompiles through MCP.

**Note on save states:** a save state restores old RAM, including code. After patching the ELF, never test from a state saved on an older build. Use scripted input from boot, or after Phase 2 a test scene injected via the script format.

## Phase 1: recon

1. Extract the ISO to `build/orig/`, then record its SHA-1 and the file list.
2. Use Haiku to classify every file by magic bytes, size, and probable role.
3. Run the 21-ko tools unmodified against the matching KimiKiss files.
4. Document every container and format in `docs/formats/<name>.md`.

**Gate G2:** do the Amagami tools parse KimiKiss files and produce readable Shift-JIS?

- Yes: adapt them.
- No: reverse the formats from scratch, and note how far they differ.

## Phase 2: text pipeline round trip

1. **Extractor.** Write every script line to JSON records:

   ```json
   {"file": "...", "offset": 0, "id": "...", "speaker": "...", "text": "...",
    "control_codes": [...], "byte_budget": 0, "route": "...", "context_prev": "...", "context_next": "..."}
   ```

2. **Reinserter.** Rebuild script files and archives with pointer and offset recalculation, so text is not limited to the original length.
3. **Round trip test.** Extract, reinsert unchanged, and rebuild.

**Gate G3:** every rebuilt file is byte-identical to the original. Do not proceed until this passes.

4. Do the same round trip for textures (TM2 or whatever Phase 1 found).
5. Build the size budget report and run it on every build: free space per archive, in the ELF, and on the disc.

## Phase 3: targeted executable work (Ghidra MCP)

1. Use string search and cross-references to find the script interpreter, the text draw path, the glyph table lookup, line wrap, and character advance.
2. Rename and comment everything found. Delegate the bulk application of these names to Haiku once the names are decided.
3. Design the font patch:
   - Use variable-width (or at least half-width) glyphs.
   - Build a new font texture and a width table.
   - Change wrap logic to work on spaces and word boundaries instead of fixed character counts.
4. Implement it as minimal assembly patches, plus a code cave if needed. Record every patch in `patches/` with its address, the original bytes, the new bytes, and the reason.
5. Verify in the emulator: show a forced English test line and check rendering, wrapping, and the backlog.

## Phase 4: non-script text

- Menus, the calendar, help screens, name entry, save/load screens, and hardcoded strings in the ELF.
- Text baked into textures: export, edit, and reimport. Flag art-heavy cases for a human.
- Coverage pass: walk every screen, capture it, and have Haiku triage the captures for leftover Japanese.

## Phase 5: translation

1. **Glossary.** Cover character names (consistent romanization), honorifics policy, school and place names, and recurring terms. The user approves the glossary before bulk translation starts.
2. **Translate** scene by scene, with speaker, route, and surrounding lines as context. Preserve control codes exactly.
3. **Haiku compliance pass** on every line:
   - Byte budget.
   - Control codes intact.
   - Glossary terms used.
   - No untranslated Japanese.
4. **Strong-model review** of everything Haiku flags and of a random sample.

## Phase 6: build and QA loop

1. A single `tools/build/build.sh` takes the clean ISO, verifies its checksum, extracts, reinserts, applies the ELF patches, rebuilds the ISO, and creates the xdelta.
2. **QA run:**
   - Boot the build.
   - Drive scripted input through representative scenes: dialogue, choices, the backlog, the calendar, menus, and save/load.
   - Capture screenshots at each checkpoint.
   - Check PINE run status and the PCSX2 log for crashes and hangs.
3. Haiku triages the screenshots. A stronger model reviews the failures and fixes the cause.
4. Repeat until the QA run is clean. Then test every heroine route at least to its first branch.

## Phase 7: release

- Ship only the xdelta patch(es), a README with the required source ISO checksum and apply instructions, and the tools.
- If space forces a split, as with Amagami, document which content each patch contains.

## Known risks

| Risk | Mitigation |
|---|---|
| KimiKiss engine differs from Amagami | Detected at G2; budget extra reverse-engineering time |
| No headless capture path | Detected at G0; fall back to visible capture or user screenshots |
| ELF, RAM, or disc space too tight | Size report from Phase 2; code caves; split patches as a last resort |
| PCSX2 PINE wedges | Restart PCSX2; issue PINE calls serially, never pipelined |
| Stale save states mask patched code | Never test patched code from an old-build state |
| Text in images | Manual art pass, flagged early |

## Reporting

At the end of each phase, report:

- Gate result.
- What was learned, with links to `docs/` files.
- Blockers.
- The next concrete step.

Never mark a phase complete while its gate is failing.
