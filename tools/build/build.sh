#!/usr/bin/env bash
# Build a patched disc image from the clean ISO.
#
# Usage: tools/build/build.sh <clean.iso> <out.iso> [text_dir] [trans_dir]
#        tools/build/build.sh --text-only <clean.iso>     only extract the Japanese text into text/
#                                                         (what translators need to run the checks)
#
#   text_dir   Japanese records (default: text/, local, gitignored). May also be a directory that
#              already carries "translation" fields (a prepared or test directory).
#   trans_dir  English translation store (default: translation/en, committed). A line there wins
#              over a "translation" field in text_dir. "none" = use text_dir as it is.
#
# 1. Verifies the clean ISO against tools/build/iso.sha1 (iso_patch.py).
# 2. Extracts the disc once into build/orig (reused while its manifest exists).
# 3. Merges text_dir with the translation store, word-wraps (batch.py prepare),
#    reinserts the text into the scripts, applies the bytecode
#    patches in patches/scripts, repacks SCRIPT.IMG.
# 4. Writes the English glyphs and the redrawn textures into GRAPH0.ARC/PAC
#    (tools/texture/apply_graph0.py; needs Pillow and numpy).
#    Hand-edited textures (D-020): every GRAPHn_NNNN.png in
#    $KIMIKISS_OVERRIDES, else <repo>/texture_overrides (git-ignored), else ../kimikiss-private/texture_overrides
#    replaces that entry of GRAPH0 (instead of the redraw), GRAPH1 or GRAPH2
#    (apply_graph12.py writes GRAPH1.ARC / GRAPH2.ARC only for archives that
#    have overrides). No directory or no PNGs: the build is as without the feature.
# 5. Applies the in-place code patches in patches/elf to the executable (D-027).
# 6. Copies the clean ISO to out.iso and replaces those files (relocating
#    any that outgrew their slot) in both the ISO9660 and the UDF
#    descriptors.
# 7. Runs tools/qa/check_iso_udf.py on the result; the build fails if the
#    ISO9660 and UDF trees disagree or any UDF tag/CRC is invalid.
# 8. Writes out.iso.xdelta (clean ISO -> out.iso) when xdelta3 is installed, and checks that
#    applying it to the clean ISO reproduces out.iso byte for byte. The xdelta is the only
#    artifact meant for distribution (the ISO itself is never published).
# Output: the steps print one line each; everything else goes to build/build.log, whose tail is
# shown when a step fails. Needs Python 3 with Pillow and numpy (pip install -r requirements.txt)
# and xdelta3 on PATH (KIMIKISS_NO_XDELTA=1 skips the distributable patch).
# The clean ISO is only ever read. Nothing here writes inside the repo
# except the gitignored build/ directory.
set -euo pipefail
cd "$(dirname "$0")/../.."

text_only=0
if [[ "${1:-}" == "--text-only" ]]; then text_only=1; shift; set -- "${1:-}" build/unused.iso "${@:2}"; fi
iso="${1:?usage: $0 <clean.iso> <out.iso> [text_dir] [trans_dir]}"
out="${2:?usage: $0 <clean.iso> <out.iso> [text_dir] [trans_dir]}"
text_dir="${3:-text}"
trans_dir="${4:-translation/en}"
work=build/work
mkdir -p build
log=build/build.log
: > "$log"

die() { echo "ERROR: $*" >&2; exit 1; }

# A Python 3 that has Pillow and numpy (on Windows, Git Bash's python3 often has neither).
PY=()
for cand in python3 python "py -3"; do
  # shellcheck disable=SC2086
  if $cand -c 'import PIL, numpy' >/dev/null 2>&1; then read -r -a PY <<< "$cand"; break; fi
done
if [[ ${#PY[@]} -eq 0 ]]; then
  die "no Python 3 with Pillow and numpy found (tried python3, python, py -3). Install Python 3 from python.org, then run: python -m pip install -r requirements.txt"
fi

[[ -f "$iso" ]] || die "source ISO not found: $iso"
for tool in sha1sum cmp; do command -v "$tool" >/dev/null || die "$tool not found (use Git Bash or WSL on Windows)"; done
if (( ! text_only )) && ! command -v xdelta3 >/dev/null && [[ "${KIMIKISS_NO_XDELTA:-}" != 1 ]]; then
  die "xdelta3 not found, so no distributable patch can be written. Install it (Linux: apt install xdelta3; Windows: xdelta3 .exe from https://github.com/jmacd/xdelta-gpl/releases, put it on PATH), or set KIMIKISS_NO_XDELTA=1 to build only the ISO."
fi

# Runs one build step quietly: a title line on screen, the details in build/build.log.
step() {
  local title="$1"; shift
  echo "[$step_n/$step_total] $title"; step_n=$((step_n + 1))
  { echo "### $title"; "$@"; } >> "$log" 2>&1 || {
    echo "ERROR: step failed: $title. Last lines of $log:" >&2; tail -n 15 "$log" >&2; exit 1; }
}
step_n=1; step_total=10

want=$(cut -d' ' -f1 tools/build/iso.sha1)
echo "[0/$step_total] checking the source ISO checksum (a minute for a full dump)"
got=$(sha1sum "$iso" | cut -d' ' -f1)
[[ "$got" == "$want" ]] || die "$iso has SHA-1 $got, expected $want. Only the original dump (see docs/source-iso.md) can be patched."

if [[ ! -f build/orig_manifest.json ]]; then
  step "extracting the disc (first run only)" "${PY[@]}" tools/extract/iso_extract.py "$iso" build/orig build/orig_manifest.json
else
  step_n=$((step_n + 1))
fi

rm -rf "$work"
mkdir -p "$work"
step "unpacking the scripts" "${PY[@]}" tools/extract/img.py unpack build/orig/SCRIPT.IMG "$work/script_orig"
# The Japanese text records are generated from the disc when the default text/ is missing.
if [[ ! -d "$text_dir" ]]; then
  step "extracting the Japanese text into $text_dir/ (first run only)" \
    "${PY[@]}" tools/extract/extract_text.py "$work/script_orig" "$text_dir"
else
  step_n=$((step_n + 1))
fi
if (( text_only )); then
  echo; echo "OK: Japanese text is in $text_dir/ (local only; never commit it). Next: python3 tools/qa/check_translation.py $text_dir"
  exit 0
fi
# Merge Japanese (text_dir) with the English store (D-022) and word-wrap (D-021): dialogue and
# dialog lines get ／ / \n breaks.
step "merging the translation and word-wrapping" "${PY[@]}" tools/translate/batch.py prepare "$text_dir" "$work/text" --trans "$trans_dir"
step "inserting the text and applying the script patches" bash -c '
  set -e
  "$@" tools/reinsert/reinsert_text.py '"$work/script_orig $work/text $work/script"'
  "$@" tools/reinsert/apply_script_patches.py '"$work/script"' patches/scripts
  "$@" tools/reinsert/img_pack.py '"$work/script $work/SCRIPT.IMG"'' _ "${PY[@]}"
# Hand-made textures (D-020) are game art and are not in the repository: say whether any are used.
"${PY[@]}" -c "
import sys; sys.path.insert(0, 'tools/texture')
import overrides
d = overrides.default_dir()
n = sum(len(v) for v in overrides.find().values())
print(f'hand-made textures: {n} PNG(s) from {d}' if n else
      f'hand-made textures: none (put GRAPHn_NNNN.png files in {d}); the release xdelta includes the maintainers set')
"
step "drawing the English font and textures" bash -c '
  set -e
  "$@" tools/texture/apply_graph0.py build/orig/GRAPH/GRAPH0.ARC '"$work/GRAPH0.ARC $work/GRAPH0.PAC"' --report '"$work/graph0_textures.json"'
  "$@" tools/texture/apply_graph12.py build/orig/GRAPH '"$work"'' _ "${PY[@]}"
step "patching the executable" "${PY[@]}" tools/build/elf_patch.py build/orig/SLPS_258.50 "$work/SLPS_258.50" patches/elf
patches=("SLPS_258.50=$work/SLPS_258.50"
         "SCRIPT.IMG=$work/SCRIPT.IMG"
         "GRAPH/GRAPH0.ARC=$work/GRAPH0.ARC"
         "GRAPH/GRAPH0.PAC=$work/GRAPH0.PAC")
for n in GRAPH1 GRAPH2; do
  if [[ -f "$work/$n.ARC" ]]; then patches+=("GRAPH/$n.ARC=$work/$n.ARC"); fi
done
step "writing the patched disc image" "${PY[@]}" tools/build/iso_patch.py "$iso" "$out" "${patches[@]}"
# The ISO9660 and UDF views of the image must agree (decision D-014).
step "checking the disc structure" "${PY[@]}" tools/qa/check_iso_udf.py "$out"

# The distributable: an xdelta from the clean ISO, verified by applying it.
if command -v xdelta3 >/dev/null; then
  step "writing and verifying the xdelta patch" bash -c '
    set -e
    xdelta3 -e -9 -f -A= -s "$1" "$2" "$2.xdelta"
    xdelta3 -d -f -s "$1" "$2.xdelta" "$3/verify.iso"
    cmp "$2" "$3/verify.iso"
    rm -f "$3/verify.iso"' _ "$iso" "$out" "$work"
fi

echo
echo "OK: patched image  $out"
[[ -f "$out.xdelta" ]] && echo "OK: patch for sharing  $out.xdelta ($(stat -c %s "$out.xdelta") bytes; apply it to the original dump)"
echo "Details: $log"
