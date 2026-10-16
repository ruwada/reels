#!/usr/bin/env bash
# One-time setup for tools/fx in a fresh container (installs are lost with the container).
set -e
pip install -q onnxruntime playwright opencv-python-headless numpy fonttools brotli
mkdir -p /tmp/fx/models /tmp/fx/cache
# person segmentation model (u2net_human_seg, 176 MB, from the rembg releases on GitHub)
[ -f /tmp/fx/models/u2net_human_seg.onnx ] || \
  curl -sSL -o /tmp/fx/models/u2net_human_seg.onnx \
  https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx
# Chromium: the pre-installed Playwright browser is used (FX_CHROME overrides the path)
ls "${FX_CHROME:-/opt/pw-browsers/chromium-1194/chrome-linux/chrome}" >/dev/null
echo "fx ready"
