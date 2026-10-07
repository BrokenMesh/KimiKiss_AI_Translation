# Pipeline commands

For a plain build use `tools/build/build.sh` (or `build.bat` on Windows); it does steps 1-3 and the texture, executable and disc steps below itself, creating `build/orig` and `text/` when missing. Requirements: Python 3 with Pillow and numpy (`requirements.txt`), xdelta3, and a Unix shell (Git Bash on Windows). The Inter font weights the texture redraw needs are in `tools/font/`. Player instructions: `docs/GETTING_STARTED.md`.

All paths are relative to the repo root. `build/` and `text/` are gitignored because they contain game data.

```sh
# 0. Fetch the user's ISO outside the repo (verifies the recorded SHA-1)
tools/build/fetch_iso.sh '<url-or-path>'

# 1. Extract the disc
python3 tools/extract/iso_extract.py ../kimikiss-private/kimikiss.iso build/orig build/orig_manifest.json

# 2. Scripts -> JSON
python3 tools/extract/img.py unpack build/orig/SCRIPT.IMG build/script
python3 tools/extract/extract_text.py build/script text

# 3. JSON -> scripts -> SCRIPT.IMG ("translation" field wins over "text")
python3 tools/reinsert/reinsert_text.py build/script text build/out/script
python3 tools/reinsert/img_pack.py build/out/script build/out/SCRIPT.IMG

# Textures
python3 tools/extract/arc.py unpack build/orig/GRAPH/GRAPH0.ARC build/graph0
python3 tools/extract/tim2.py topng build/graph0/0077_ffc76f47.tm2 font.png
python3 tools/extract/tim2.py totim2 font.png build/graph0/0077_ffc76f47.tm2
python3 tools/reinsert/arc_pack.py build/graph0 build/out/GRAPH0.ARC
python3 tools/extract/font.py build/orig/GRAPH/GRAPH0.ARC build/font.png

# Gate G3 and size budget
python3 tools/qa/test_text_roundtrip.py build/orig/SCRIPT.IMG
python3 tools/qa/test_texture_roundtrip.py build/texrt build/orig/GRAPH/*.ARC build/orig/SOUND/MUSIC.ARC
python3 tools/qa/size_report.py build/orig_manifest.json build/orig build/out
```

## Phase 0 tooling (the maintainer's own environment: not needed to build or translate; paths are examples)

```sh
# Ghidra: headless import + analysis, then the MCP server and the G1 smoke test
$GHIDRA/support/analyzeHeadless /home/user/kimikiss-private/ghidra kimikiss \
    -import build/orig/SLPS_258.50 -processor r5900:LE:32:default
/home/user/kimikiss-tools/start_ghidra_mcp.sh &
/home/user/kimikiss-tools/venv/bin/python tools/qa/ghidra_mcp_smoke.py /home/user/kimikiss-tools/venv/bin/bridge-mcp-ghidra
/home/user/kimikiss-tools/venv/bin/python tools/re/ghidra_call.py /home/user/kimikiss-tools/venv/bin/bridge-mcp-ghidra \
    get_xrefs_to '{"address": "0x002b16e0"}'

# PCSX2: boot, capture, PINE check (G0)
XDG_RUNTIME_DIR=/tmp/pcsx2-runtime \
PROBE_CMD="/home/user/kimikiss-tools/venv/bin/python tools/qa/pine_check.py \
    /home/user/kimikiss-tools/mcp-pine/dist/index.js build/orig/SLPS_258.50 /tmp/pcsx2-runtime/pcsx2.sock" \
tools/qa/boot_capture.sh ../kimikiss-private/kimikiss.iso qa/boot 30 60 90
```
