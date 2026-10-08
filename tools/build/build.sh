#!/usr/bin/env bash
# Build a patched disc image from the clean ISO.
#
# Usage: tools/build/build.sh <clean.iso> <out.iso> [text_dir] [trans_dir]
#        tools/build/build.sh --text-only <clean.iso>     only extract the Japanese text into text/
#                                                         (what translators need to run the checks)
#
#   out.iso    default build/KimiKiss_EN.iso; a bare name is put in build/. The patch is written next
#              to it as <out.iso>.xdelta. --no-xdelta (or KIMIKISS_NO_XDELTA=1) skips the patch.
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
# 8. Writes out.iso.xdelta (clean ISO -> out.iso) unless --no-xdelta, and checks that
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
no_xdelta=0
[[ "${KIMIKISS_NO_XDELTA:-}" == 1 ]] && no_xdelta=1
args=()
for a in "$@"; do
  case "$a" in
    --text-only) text_only=1 ;;
    --no-xdelta|KIMIKISS_NO_XDELTA=1) no_xdelta=1 ;;
    -*|*=*) echo "ERROR: unexpected argument '$a'. Options: --no-xdelta (skip the .xdelta), --text-only." >&2; exit 2 ;;
    *) args+=("$a") ;;
  esac
done
usage="usage: $0 [--no-xdelta] <clean.iso> [out.iso] [text_dir] [trans_dir]   |   $0 --text-only <clean.iso>"
iso="${args[0]:?$usage}"
if (( text_only )); then
  out=build/unused.iso
  text_dir="${args[1]:-text}"
  trans_dir="translation/en"
else
  out="${args[1]:-KimiKiss_EN.iso}"
  text_dir="${args[2]:-text}"
  trans_dir="${args[3]:-translation/en}"
  # A bare file name goes into build/, so the ISO and its .xdelta always land together there.
  case "$out" in */*|*\\*) ;; *) out="build/$out" ;; esac
  case "$(printf %s "$out" | tr 'A-Z' 'a-z')" in *.iso) ;; *) echo "ERROR: the output name '$out' must end in .iso (a second argument that is not a file name?). $usage" >&2; exit 2 ;; esac
fi
work=build/work
mkdir -p build "$(dirname "$out")"
rm -f "$out.xdelta"     # never leave a patch from an earlier build next to a new image
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
if (( ! text_only && ! no_xdelta )) && ! command -v xdelta3 >/dev/null; then
  die "xdelta3 not found, so no distributable patch can be written. Install it (Linux: apt install xdelta3; Windows: xdelta3 .exe from https://github.com/jmacd/xdelta-gpl/releases, put it on PATH), or add --no-xdelta to build only the ISO."
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
      f'hand-made textures: none found in {d} (the project set is the texture_overrides/ folder of the repository)')
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
if (( ! no_xdelta )); then
  step "writing and verifying the xdelta patch" bash -c '
    set -e
    xdelta3 -e -9 -f -A= -s "$1" "$2" "$2.xdelta"
    xdelta3 -d -f -s "$1" "$2.xdelta" "$3/verify.iso"
    cmp "$2" "$3/verify.iso"
    rm -f "$3/verify.iso"' _ "$iso" "$out" "$work"
fi

echo
mib() { echo $(( $1 / 1048576 )); }
echo "OK: created the ISO     $out ($(stat -c %s "$out") bytes, $(mib "$(stat -c %s "$out")") MiB)"
if [[ -f "$out.xdelta" ]]; then
  echo "OK: created the patch   $out.xdelta ($(stat -c %s "$out.xdelta") bytes; share this file, never the ISO)"
else
  echo "(no .xdelta written: --no-xdelta)"
fi
echo "Details: $log"
