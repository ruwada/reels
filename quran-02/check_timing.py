#!/usr/bin/env python3
"""For each ayah boundary from the timing file: loudness at the boundary vs the quietest point within +-0.8 s.
A boundary that sits in a pause is quiet; a boundary inside a word is loud."""
import json, sys, subprocess, numpy as np
d = json.load(open(f"src/{sys.argv[1]}/ayat.json")); mp3 = f"src/{sys.argv[1]}/{d['surah']:03d}.mp3"
t0 = max(0, d['ayat'][0]['start'] - 1); t1 = d['ayat'][-1]['stop'] + 1
a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-to", str(t1), "-i", mp3, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout, np.int16).astype(float)
h = 800  # 50 ms
db = np.array([20 * np.log10(np.sqrt(np.mean(a[i:i + h] ** 2)) + 1) for i in range(0, len(a) - h, h)])
peak = np.percentile(db, 95)
for x in d['ayat']:
    for edge in ('start', 'stop'):
        i = int((x[edge] - t0) / 0.05); w = db[max(0, i - 16):i + 16]
        print(f"{x['key']:>6} {edge:5} {x[edge]:9.2f}s  at edge {db[i] - peak:6.1f} dB  quietest nearby {w.min() - peak:6.1f} dB at {(w.argmin() - min(i, 16)) * 0.05:+.2f}s")
