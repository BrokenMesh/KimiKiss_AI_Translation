#!/usr/bin/env bash
# Gate G0: boot an ISO in PCSX2 on a virtual display, capture PNGs, exit cleanly.
#
# Usage: tools/qa/boot_capture.sh <iso> <out_dir> [seconds...]
# Env:   PCSX2_BIN     pcsx2-qt from the extracted AppImage (portable mode)
#        DISPLAY_NUM   Xvfb display number (default 99)
#        PROBE_CMD     optional command run after the last capture while the
#                      game is still running (e.g. the PINE check); its exit
#                      status becomes the script's
#
# Captures the whole virtual screen at each listed second after launch
# (default: 20 40 60) as <out_dir>/boot_<s>.png, then stops PCSX2 and Xvfb.
# PCSX2 must be configured beforehand (BIOS, PINE, renderer); see
# docs/phase-0-status.md.
set -euo pipefail

iso="${1:?usage: $0 <iso> <out_dir> [seconds...]}"
out="${2:?usage: $0 <iso> <out_dir> [seconds...]}"
shift 2
times=("${@:-20 40 60}")
read -r -a times <<< "${times[*]}"
pcsx2="${PCSX2_BIN:-pcsx2-qt}"
disp=":${DISPLAY_NUM:-99}"

mkdir -p "$out"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/pcsx2-runtime}"
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

Xvfb "$disp" -screen 0 1280x800x24 -nolisten tcp > "$out/xvfb.log" 2>&1 &
xvfb_pid=$!
pcsx2_pid=""
cleanup() {
  if [[ -n "$pcsx2_pid" ]] && kill -0 "$pcsx2_pid" 2>/dev/null; then
    kill -TERM "$pcsx2_pid"
    for _ in $(seq 1 20); do kill -0 "$pcsx2_pid" 2>/dev/null || break; sleep 0.5; done
    kill -KILL "$pcsx2_pid" 2>/dev/null || true
  fi
  kill "$xvfb_pid" 2>/dev/null || true
}
trap cleanup EXIT
sleep 2

DISPLAY="$disp" "$pcsx2" -batch -nogui -fastboot -- "$iso" > "$out/pcsx2.log" 2>&1 &
pcsx2_pid=$!

elapsed=0
for t in "${times[@]}"; do
  sleep $((t - elapsed))
  elapsed=$t
  if ! kill -0 "$pcsx2_pid" 2>/dev/null; then
    echo "error: PCSX2 exited before ${t}s; see $out/pcsx2.log" >&2
    exit 1
  fi
  xwd -root -display "$disp" -silent | convert xwd:- "$out/boot_${t}.png"
  echo "captured $out/boot_${t}.png"
done

if [[ -n "${PROBE_CMD:-}" ]]; then
  echo "probe: $PROBE_CMD"
  bash -c "$PROBE_CMD"
fi
