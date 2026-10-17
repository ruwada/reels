#!/usr/bin/env bash
# Thumbnails for 01 orbit and 02 couch wall: one frame (at 35 %) from each given video -> /tmp/fx/thumbs/tNN.jpg
# usage: bash tools/fx/make_thumbs.sh reel1.mp4 reel2.mp4 ...
# Check every frame by eye before use (channel rules: no women, nothing haram).
set -e
mkdir -p /tmp/fx/thumbs
i=0
for f in "$@"; do
  i=$((i+1))
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  ffmpeg -v error -y -ss "$(python3 -c "print($d*0.35)")" -i "$f" -frames:v 1 -vf scale=540:960 \
    "/tmp/fx/thumbs/t$(printf %02d $i).jpg"
done
ls /tmp/fx/thumbs
