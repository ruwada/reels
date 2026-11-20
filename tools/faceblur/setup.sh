#!/usr/bin/env bash
# Face-blur toolchain for a fresh container (~3 min). Models download on first use:
# insightface buffalo_l (~280 MB, GitHub releases) and yolo11x-pose.pt (~113 MB, GitHub releases).
set -e
command -v ffmpeg >/dev/null || { apt-get update -q && apt-get install -y -q ffmpeg; }
python3 -m pip install -q opencv-python-headless pillow-heif insightface onnxruntime ultralytics numpy pillow
