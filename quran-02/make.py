#!/usr/bin/env python3
"""Build a video and keep it readable: build.py, then contrast.py; every ayah under the limit gets a darker
backing (shade +0.3) and the video is rebuilt, up to 4 rounds.
    python3 make.py <config.json> [limit]"""
import json, subprocess, sys
cfg = sys.argv[1]; limit = sys.argv[2] if len(sys.argv) > 2 else "4.5"
name = json.load(open(cfg))['name']; W = f"work/{name}"
n = len(json.load(open(f"src/{name}/ayat.json"))['ayat'])
shade = [1.0] * n
for rnd in range(5):
    json.dump(shade, open(f"{W}/shade.json", "w"))
    subprocess.run(["python3", "build.py", cfg], check=True, stdout=subprocess.DEVNULL)
    ok = subprocess.run(["python3", "contrast.py", name, limit]).returncode == 0
    worst = json.load(open(f"{W}/contrast.json"))['worst']
    print(f"round {rnd + 1}: shade {shade} -> worst {worst}", flush=True)
    if ok: print("READABLE"); break
    if rnd == 4: print("STILL LOW CONTRAST: change the background clip"); sys.exit(1)
    shade = [s + 0.3 if w < float(limit) else s for s, w in zip(shade, worst)]
