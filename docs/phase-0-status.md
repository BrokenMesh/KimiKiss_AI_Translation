# Phase 0 status

> History. The paths below are the maintainer's cloud environment at the time; nothing here is needed to build the patch or to translate.

The user supplied the tools through their Google Drive (GitHub release downloads are blocked in this cloud session): Ghidra 12.1.3, ghidra-emotionengine-reloaded built for 12.1.3, GhidraMCP 7.0.0-rc.1, PCSX2 v2.9.108 (Linux AppImage), and their own BIOS dumps (Japanese 77000, European 70004).

## Layout outside the repo

| Path | Content |
|---|---|
| `/home/user/kimikiss-tools/ghidra_12.1.3_PUBLIC` | Ghidra, with both extensions in `Ghidra/Extensions/` |
| `/home/user/kimikiss-tools/ghidra-mcp` | GhidraMCP source at tag `v7.0.0-rc.1`, for the Python bridge (not in the release zip) |
| `/home/user/kimikiss-tools/venv` | Python venv with `ghidra-mcp-bridge` 7.0.0 and `mcp` |
| `/home/user/kimikiss-tools/start_ghidra_mcp.sh` | Starts the GhidraMCP headless server on `127.0.0.1:8089` |
| `/home/user/kimikiss-tools/pcsx2` | Extracted PCSX2 AppImage, portable mode (`usr/bin/portable.txt`, `usr/bin/inis/`) |
| `/home/user/kimikiss-tools/mcp-pine` | mcp-pine, built with `npm ci && npm run build` |
| `/home/user/kimikiss-private/bios/` | BIOS dumps, mode 700 |
| `/home/user/kimikiss-private/ghidra/` | Ghidra project `kimikiss` (derived from the game binary, so private) |

The container is ephemeral, so all of this has to be recreated in a new session.

## Gate G1 (Ghidra loads the ELF, analysis completes, one function decompiles through MCP): **pass**

1. The extension ships `r5900.slaspec` without a compiled `.sla`. Compile it once with `support/sleigh r5900.slaspec` in the extension's `data/languages`.
2. Import and analyze: `analyzeHeadless /home/user/kimikiss-private/ghidra kimikiss -import build/orig/SLPS_258.50 -processor r5900:LE:32:default`. This takes 48 s. Result: 3,136 functions. The only errors are null LSDA pointers in GCC exception frames, which are harmless.
3. `start_ghidra_mcp.sh` runs `com.xebyte.headless.GhidraMCPHeadlessServer` with the Ghidra jars on the classpath. Its `--program` flag fails to open the program, so the program is loaded through the MCP tool `load_program_from_project` instead.
4. `tools/qa/ghidra_mcp_smoke.py` drives the bridge over MCP stdio: 233 tools, then `load_program_from_project /SLPS_258.50`, `list_functions`, and `decompile_function entry` returns C. Output: `PASS: decompiled through MCP`.

The MCP server is not registered with this Claude Code session; registering it requires a session restart. The tools above reach it from scripts, and `claude mcp add` can register `venv/bin/bridge-mcp-ghidra` in a new session.

## Gate G0 (script boots the game, captures the title screen, exits cleanly): **pass**

`tools/qa/boot_capture.sh <iso> <out_dir> [seconds...]` starts Xvfb, runs `pcsx2-qt -batch -nogui -fastboot -- <iso>`, captures the virtual screen with `xwd` at each listed second, optionally runs `PROBE_CMD` while the game is still running, then stops PCSX2 (SIGTERM, then SIGKILL after 10 s) and Xvfb.

- The title screen ("Press Start Button", © 2006–2008 Enterbrain) is up at 90 s. The 640 × 480 game window sits at the top left of the 1280 × 800 virtual screen.
- **PINE** (slot 28011, socket `$XDG_RUNTIME_DIR/pcsx2.sock`): `tools/qa/pine_check.py` goes through mcp-pine over MCP stdio. `pine_ping` returns `PCSX2 v2.9.108`, `pine_get_status` returns `running`, and four `pine_read32` reads at `0x00100000` match the ELF's first load-segment words. A raw socket probe also returned the title キミキス [eb!コレ+], serial `SLPS-25850` and disc CRC `2818e08b`.
- Shots and logs go to `qa/` (gitignored).

### PCSX2 setup (once per container)

1. Extract the AppImage (`--appimage-extract`) and create `usr/bin/portable.txt`.
2. Install `xvfb x11-utils x11-apps xdotool imagemagick libopengl0` with apt.
3. Run PCSX2 once with the ISO so it writes its own default `inis/PCSX2.ini`, then stop it. A hand-written ini is rejected with "Settings failed to load".
4. `tools/qa/pcsx2_configure.py <ini> /home/user/kimikiss-private/bios/japan_console 77000_BIOS_JAP.BIN` sets: no setup wizard or shutdown prompt, PINE on, fast boot, software renderer (13), null audio, and the Japanese BIOS. Without null audio, Cubeb raises a modal error because the container has no sound device.

### PINE pitfalls found

- mcp-pine calls timed out (10 s, no reply) in 3 of the first 4 probe runs:
  - once on the very first call while PCSX2 showed the modal audio error, which suggests PINE is serviced on the UI thread;
  - once at a call the truncated log did not record;
  - once on `pine_get_info`, right after `pine_ping` and `pine_get_status` had succeeded.
- `pine_get_info` pipelines five opcodes, and after a dropped reply mcp-pine's reply queue stays misaligned for every later call. QA scripts therefore never use it.
- With serial calls only (`pine_ping`, `pine_get_status`, `pine_read32`) and no modal dialogs, the full G0 run passed twice in a row. A raw socket client made 3 serial calls on one connection without a drop.
- This matches the brief's rule: PINE calls serially, never pipelined. Treat any PINE timeout as possibly leaving the bridge desynced, and restart mcp-pine.
- `pine_read_range` is serial by default (`PINE_PIPELINE_BATCH` unset). Keep it that way.
- `pkill -f pcsx2-qt` also matches the shell that runs it. Use `pkill -x pcsx2-qt`.
