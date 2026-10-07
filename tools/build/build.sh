#!/usr/bin/env bash
# Build a patched disc image from the clean ISO.
#
# Usage: tools/build/build.sh <clean.iso> <out.iso> [text_dir]
#
# 1. Verifies the clean ISO against tools/build/iso.sha1 (iso_patch.py).
# 2. Extracts the disc once into build/orig (reused while its manifest exists).
# 3. Reinserts text from text_dir (default: text/), applies the bytecode
#    patches in patches/scripts, repacks SCRIPT.IMG.
# 4. Writes the English glyphs and the redrawn textures into GRAPH0.ARC/PAC
#    (tools/texture/apply_graph0.py; needs Pillow and numpy).
#    Hand-edited textures (D-020): every GRAPHn_NNNN.png in
#    $KIMIKISS_OVERRIDES (default ../kimikiss-private/texture_overrides)
#    replaces that entry of GRAPH0 (instead of the redraw), GRAPH1 or GRAPH2
#    (apply_graph12.py writes GRAPH1.ARC / GRAPH2.ARC only for archives that
#    have overrides). No directory or no PNGs: the build is as without the feature.
# 5. Copies the clean ISO to out.iso and replaces those files (relocating
#    any that outgrew their slot) in both the ISO9660 and the UDF
#    descriptors.
# 6. Runs tools/qa/check_iso_udf.py on the result; the build fails if the
#    ISO9660 and UDF trees disagree or any UDF tag/CRC is invalid.
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
# Word-wrap translations (D-013): dialogue and dialog lines get ／ / \n breaks.
python3 tools/translate/batch.py prepare "$text_dir" "$work/text"
python3 tools/reinsert/reinsert_text.py "$work/script_orig" "$work/text" "$work/script"
python3 tools/reinsert/apply_script_patches.py "$work/script" patches/scripts
python3 tools/reinsert/img_pack.py "$work/script" "$work/SCRIPT.IMG"
python3 tools/texture/apply_graph0.py build/orig/GRAPH/GRAPH0.ARC "$work/GRAPH0.ARC" "$work/GRAPH0.PAC" \
  --report "$work/graph0_textures.json"
python3 tools/texture/apply_graph12.py build/orig/GRAPH "$work"
patches=("SCRIPT.IMG=$work/SCRIPT.IMG"
         "GRAPH/GRAPH0.ARC=$work/GRAPH0.ARC"
         "GRAPH/GRAPH0.PAC=$work/GRAPH0.PAC")
for n in GRAPH1 GRAPH2; do
  if [[ -f "$work/$n.ARC" ]]; then patches+=("GRAPH/$n.ARC=$work/$n.ARC"); fi
done
python3 tools/build/iso_patch.py "$iso" "$out" "${patches[@]}"

# 6. The ISO9660 and UDF views of the image must agree (decision D-014).
python3 tools/qa/check_iso_udf.py "$out"
