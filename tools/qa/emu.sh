#!/usr/bin/env bash
# Interactive PCSX2 driver on a virtual display, for scripted QA walks.
#
#   tools/qa/emu.sh start <iso>          start Xvfb + PCSX2 (background)
#   tools/qa/emu.sh key <key> [hold_ms] [count]
#                                         press a key (X keysym) in the game window
#   tools/qa/emu.sh spam <key> <seconds> [out.png] [interval_ms]
#                                         press <key> repeatedly for <seconds>
#                                         (default every 80 ms), then optionally
#                                         capture; for skipping long text runs
#   tools/qa/emu.sh turbo                toggle PCSX2 turbo (unthrottled speed)
#   tools/qa/emu.sh shot <out.png>       capture the 640x480 game area
#   tools/qa/emu.sh stop                 stop PCSX2 and Xvfb
#
# Pad 1 bindings (PCSX2 defaults): Circle=l Cross=k Triangle=i Square=j
# Start=Return Select=BackSpace, d-pad = arrow keys. State lives in $EMU_DIR.
set -euo pipefail
EMU_DIR="${EMU_DIR:-/tmp/kimikiss-emu}"
DISPLAY_NUM="${DISPLAY_NUM:-98}"
PCSX2_BIN="${PCSX2_BIN:-/home/user/kimikiss-tools/pcsx2/usr/bin/pcsx2-qt}"
export DISPLAY=":$DISPLAY_NUM" XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/pcsx2-runtime}"
mkdir -p "$EMU_DIR" "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"

win() {  # the viewable game window (Qt also creates unmapped helper windows)
  for w in $(xdotool search --name 'PCSX2|キミキス|SLPS' 2>/dev/null); do
    xwininfo -id "$w" | grep -q 'IsViewable' && { echo "$w"; return; }
  done
}

case "${1:?command}" in
  start)
    iso="${2:?iso}"
    Xvfb "$DISPLAY" -screen 0 1280x800x24 -nolisten tcp > "$EMU_DIR/xvfb.log" 2>&1 &
    echo $! > "$EMU_DIR/xvfb.pid"
    sleep 2
    setsid "$PCSX2_BIN" -batch -nogui -fastboot -- "$iso" > "$EMU_DIR/pcsx2.log" 2>&1 &
    echo $! > "$EMU_DIR/pcsx2.pid"
    echo "started pcsx2 pid $(cat "$EMU_DIR/pcsx2.pid") on $DISPLAY"
    ;;
  key)
    k="${2:?key}"; hold="${3:-120}"; n="${4:-1}"
    w=$(win); [[ -n "$w" ]] || { echo "error: no PCSX2 window" >&2; exit 1; }
    for _ in $(seq 1 "$n"); do
      xdotool windowfocus "$w" 2>/dev/null || true  # no window manager: focus directly
      xdotool keydown --window "$w" "$k"; sleep "$(awk "BEGIN{print $hold/1000}")"
      xdotool keyup --window "$w" "$k"; sleep 0.25
    done
    ;;
  spam)
    k="${2:?key}"; secs="${3:?seconds}"; out="${4:-}"; gap="${5:-80}"
    w=$(win); [[ -n "$w" ]] || { echo "error: no PCSX2 window" >&2; exit 1; }
    xdotool windowfocus "$w" 2>/dev/null || true
    end=$(( $(date +%s%N) + secs * 1000000000 )); n=0
    while (( $(date +%s%N) < end )); do
      xdotool keydown --window "$w" "$k"; sleep 0.04
      xdotool keyup --window "$w" "$k"; sleep "$(awk "BEGIN{print $gap/1000}")"
      n=$((n + 1))
    done
    echo "pressed $k $n times"
    [[ -z "$out" ]] || "$0" shot "$out"
    ;;
  turbo)  # PCSX2 default hotkey for Toggle Turbo / Fast Forward
    w=$(win); [[ -n "$w" ]] || { echo "error: no PCSX2 window" >&2; exit 1; }
    xdotool windowfocus "$w" 2>/dev/null || true
    xdotool key --window "$w" Tab
    echo "turbo toggled"
    ;;
  shot)
    out="${2:?out.png}"
    xwd -root -silent | convert xwd:- -crop 640x480+0+0 +repage "$out"
    echo "$out"
    ;;
  stop)
    for p in pcsx2 xvfb; do
      if [[ -f "$EMU_DIR/$p.pid" ]]; then
        pid=$(cat "$EMU_DIR/$p.pid")
        kill -TERM "$pid" 2>/dev/null || true
        for _ in $(seq 1 20); do kill -0 "$pid" 2>/dev/null || break; sleep 0.5; done
        kill -KILL "$pid" 2>/dev/null || true
        rm -f "$EMU_DIR/$p.pid"
      fi
    done
    echo stopped
    ;;
  *) echo "unknown command $1" >&2; exit 2 ;;
esac
