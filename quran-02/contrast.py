#!/usr/bin/env python3
"""Check that the subtitles stand out from the background in a rendered video.

    python3 contrast.py <name>

For every ayah, frames are sampled every 0.5 s while its text is fully shown. In each frame the glyph pixels
(where text-k.png is opaque) are compared with the pixels right around them (within ~24 px, where the text
layer is transparent). The score is the WCAG contrast ratio between the glyphs and the brighter quarter of
their surroundings. Below the limit (default 4.5, WCAG AA for normal text; 3.0 is the floor for large text) the ayah is FAIL.
    python3 contrast.py <name> [limit]
"""
import json, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter

name = sys.argv[1]; W = f"work/{name}"
tm = json.load(open(f"{W}/timing-used.json")); rel = tm['edges_rel']
n = len(rel) - 1; LIMIT = float(sys.argv[2]) if len(sys.argv) > 2 else 4.5
scores = []


def lum(rgb):
    c = rgb / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


worst_all, fails = 99, 0
for k in range(n):
    alpha = Image.open(f"{W}/text-{k + 1}.png").getchannel('A')
    glyph = np.array(alpha) > 235
    small = alpha.point(lambda v: 255 if v > 235 else 0).resize((270, 480), Image.BOX).point(lambda v: 255 if v else 0)
    near = np.array(small.filter(ImageFilter.MaxFilter(13)).resize((1080, 1920))) > 0
    ring = near & (np.array(alpha) < 230)  # surroundings as seen: background, shadow or panel
    s, e = rel[k] + 0.4, rel[k + 1] - 0.35
    worst = 99
    for t in np.arange(s, max(s + 0.01, e), 0.5):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", f"{W}/{name}.mp4", "-frames:v", "1",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        f = np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3).astype(float)
        L = lum(f)
        lt, lb = np.median(L[glyph]), np.percentile(L[ring], 75)
        hi, lo = max(lt, lb), min(lt, lb)
        worst = min(worst, (hi + 0.05) / (lo + 0.05))
    flag = "OK" if worst >= LIMIT else "FAIL"
    fails += flag == "FAIL"; worst_all = min(worst_all, worst); scores.append(round(worst, 2))
    print(f"ayah {k + 1}: worst contrast {worst:4.1f}  {flag}")
print(f"{name}: worst {worst_all:.1f}, {'all OK' if not fails else f'{fails} ayah(s) FAIL'}")
json.dump(dict(limit=LIMIT, worst=scores), open(f"{W}/contrast.json", "w"))
sys.exit(1 if fails else 0)
