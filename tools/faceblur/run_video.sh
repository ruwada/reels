#!/usr/bin/env bash
# Full automatic pipeline for ONE vertical video (iPhone HLG or SDR, portrait).
#   tools/faceblur/run_video.sh SRC.MOV WORKDIR
# Result: WORKDIR/blur.mp4 (1080x1920, 30 fps, CRF 10) + WORKDIR/mask.json + review sheets in WORKDIR/sheets*/.
# Then CHECK the sheets by eye (README «Проверка») and add manual boxes for misses.
set -e
D=$(cd "$(dirname "$0")" && pwd); SRC=$1; W=$2; mkdir -p "$W"
export OMP_NUM_THREADS=1
N=$(ffprobe -v error -select_streams v:0 -show_entries format=duration -of csv=p=0 "$SRC" | awk '{printf "%d", $1*30+5}')
python3 "$D/det.py"  "$SRC" "$W/d0.json" 0 2 & python3 "$D/det.py" "$SRC" "$W/d1.json" 1 2 &
python3 "$D/det.py"  "$SRC" "$W/p0.json" 0 2 --pad & python3 "$D/det.py" "$SRC" "$W/p1.json" 1 2 --pad &
wait
python3 "$D/pose.py" "$SRC" "$W/q0.json" 0 4 & python3 "$D/pose.py" "$SRC" "$W/q2.json" 2 4 &
wait
python3 "$D/filt.py" "$W/p0.json" "$W/pf0.json"; python3 "$D/filt.py" "$W/p1.json" "$W/pf1.json"
python3 "$D/track.py" "$W/mask.json" "$N" "$W"/d0.json "$W"/d1.json "$W"/pf0.json "$W"/pf1.json "$W"/q0.json "$W"/q2.json
[ -f "$W/manual.json" ] && python3 "$D/manual.py" "$W/mask.json" "$W/manual.json" video
python3 "$D/render_blur.py" "$SRC" "$W/mask.json" "$W/blur.mp4"
python3 "$D/sheets.py" "$W/blur.mp4" "$W/sheets" 15 0
python3 "$D/sheets.py" "$W/blur.mp4" "$W/sheets7" 15 7
echo "done: $W/blur.mp4 — now review $W/sheets*/"
