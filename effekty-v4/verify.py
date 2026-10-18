"""Checks a finished reel: frozen/duplicated frames, contact sheets every 0.5 s.
usage: python3 verify.py VIDEO OUTDIR"""
import sys, subprocess, numpy as np, cv2, os

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
w, h = 270, 480
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                     capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
print(f"frames {len(fr)}  ({len(fr) / 30:.2f} s)  median diff {np.median(d):.2f}")
run = 0
for i, v in enumerate(d):
    if v < 0.15:
        run += 1
    else:
        if run >= 2:
            print(f"  still run: {run + 1} frames ending at {i / 30:.2f}s")
        run = 0
if run >= 2:
    print(f"  still run: {run + 1} frames at the end")
big = [(i + 1) / 30 for i, v in enumerate(d) if v > 6 * np.median(d) + 4]
print("  jumps (s):", " ".join(f"{t:.2f}" for t in big))
col = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", "fps=2,scale=216:384,tile=10x2", f"{out}/sheet%02d.jpg", "-y"])
