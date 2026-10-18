#!/usr/bin/env python3
"""Reel 24: cut every B-roll clip of broll.json to its slot: 1080x1920 cover crop, 30 fps, GOP 30, light grade.

    python3 prep_broll.py CANDIDATES_DIR OUT_DIR

CANDIDATES_DIR holds <id>.mp4 as saved by tools/pexels.py / tools/pixabay.py.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
src_dir, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
for c in json.load(open(os.path.join(HERE, "broll.json"))):
    d = c["dur"] + 0.2      # one handle for the transition
    vf = "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,fps=30"
    if c.get("reverse"):
        vf = "reverse," + vf
    vf += ",eq=contrast=1.04:saturation=0.95"
    out = os.path.join(out_dir, f"{c['id']}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(c["from"]), "-t", f"{d:.3f}", "-i",
                    os.path.join(src_dir, f"{c['id']}.mp4"), "-vf", vf, "-an", "-c:v", "libx264", "-crf", "15",
                    "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p", out], check=True)
    print(out)
