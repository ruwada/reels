#!/usr/bin/env bash
# Contact sheet of a rendered reel with the Instagram Reels safe zones drawn on top:
# top 200 px, bottom 320 px, right 130 px (icons), yellow line at 1190 px (handle + caption below).
# Usage: bash tools/code-video/preview.sh video.mp4 [t1 t2 ...]  ->  video.sheet.png
set -eu
v=$1; shift
times=${*:-"1 4 7 10"}
tmp=$(mktemp -d); inputs=(); n=0
zones="drawbox=x=0:y=0:w=1080:h=200:color=red@0.35:t=fill,drawbox=x=0:y=1600:w=1080:h=320:color=red@0.35:t=fill,drawbox=x=950:y=200:w=130:h=1400:color=red@0.35:t=fill,drawbox=x=0:y=1190:w=950:h=3:color=yellow@0.8:t=fill"
for t in $times; do
  ffmpeg -loglevel error -y -ss "$t" -i "$v" -frames:v 1 -vf "$zones,scale=360:-1" "$tmp/$n.png"
  inputs+=(-i "$tmp/$n.png"); n=$((n+1))
done
ffmpeg -loglevel error -y "${inputs[@]}" -filter_complex "hstack=$n" "${v%.*}.sheet.png"
echo "${v%.*}.sheet.png"
