#!/usr/bin/env bash
# Build a patched disc image from the clean ISO.
#
# Usage: tools/build/build.sh <clean.iso> <out.iso> [text_dir]
#
# 1. Verifies the clean ISO against tools/build/iso.sha1 (iso_patch.py).
# 2. Extracts the disc once into build/orig (reused while its manifest exists).
# 3. Reinserts text from text_dir (default: text/), applies the bytecode
#    patches in patches/scripts, repacks SCRIPT.IMG.
# 4. Writes the English glyphs into GRAPH0.ARC/PAC.
# 5. Copies the clean ISO to out.iso and replaces those files (relocating
#    any that outgrew their slot).
# The clean ISO is only ever read. Nothing here writes inside the repo
# except the gitignored build/ directory.
set -euo pipefail
cd "$(dirname "$0")/../.."

iso="${1:?usage: $0 <clean.iso> <out.iso> [text_dir]}"
out="${2:?usage: $0 <clean.iso> <out.iso> [text_dir]}"
text_dir="${3:-text}"
work=build/work

want=$(cut -d' ' -f1 tools/build/iso.sha1)
got=$(sha1sum "$iso" | cut -d' ' -f1)
[[ "$got" == "$want" ]] || { echo "error: $iso SHA-1 $got != recorded $want" >&2; exit 1; }

if [[ ! -f build/orig_manifest.json ]]; then
  python3 tools/extract/iso_extract.py "$iso" build/orig build/orig_manifest.json
fi

rm -rf "$work"
mkdir -p "$work"
python3 tools/extract/img.py unpack build/orig/SCRIPT.IMG "$work/script_orig"
python3 tools/reinsert/reinsert_text.py "$work/script_orig" "$text_dir" "$work/script"
python3 tools/reinsert/apply_script_patches.py "$work/script" patches/scripts
python3 tools/reinsert/img_pack.py "$work/script" "$work/SCRIPT.IMG"
python3 tools/font/apply_en_font.py build/orig/GRAPH/GRAPH0.ARC "$work/GRAPH0.ARC" "$work/GRAPH0.PAC"
python3 tools/build/iso_patch.py "$iso" "$out" \
  "SCRIPT.IMG=$work/SCRIPT.IMG" \
  "GRAPH/GRAPH0.ARC=$work/GRAPH0.ARC" \
  "GRAPH/GRAPH0.PAC=$work/GRAPH0.PAC"
