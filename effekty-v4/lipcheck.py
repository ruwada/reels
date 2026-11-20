"""Lip-sync check: his real speech (isolated cafe audio cut exactly like the video) vs the cloned voice in the
final reel. Prints, for every stretch of his real speech, how far the clone's onset/offset sits from it."""
import subprocess, numpy as np, sys
sys.path.insert(0, ".")
from plan import TAKES, FPS
SR = 16000
ISO = "/tmp/fx/v4/{}-iso.mp3"


def load(path, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ss), "-t", str(t)] if ss is not None else []) + \
          ["-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.int16).astype(np.float32) / 32768


def env(x, hop=160):
    n = len(x) // hop
    e = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1))
    return e / (np.percentile(e, 98) + 1e-9)


real = np.concatenate([load(ISO.format(k), round(a * FPS) / FPS, (round(b * FPS) - round(a * FPS)) / FPS) for k, a, b, *_ in TAKES])
final = load(sys.argv[1] if len(sys.argv) > 1 else "work/tight-voice.wav")
er, ef = env(real), env(final)
n = min(len(er), len(ef)); er, ef = er[:n], ef[:n]
sm = lambda e: np.convolve(e, np.ones(5) / 5, "same")
on_r, on_f = sm(er) > 0.12, sm(ef) > 0.12


def spans(m, mingap=12, minlen=8):
    out, s = [], None
    for i, v in enumerate(np.r_[m, False]):
        if v and s is None: s = i
        if not v and s is not None: out.append([s, i]); s = None
    merged = []
    for a, b in out:
        if merged and a - merged[-1][1] < mingap: merged[-1][1] = b
        else: merged.append([a, b])
    return [(a / 100, b / 100) for a, b in merged if b - a >= minlen]


R, F = spans(on_r), spans(on_f)
print("real speech spans vs clone (s): start diff / end diff")
for a, b in R:
    ov = [(c, d) for c, d in F if d > a and c < b]
    if not ov:
        print(f"  {a:6.2f}-{b:6.2f}  NO CLONE VOICE"); continue
    c, d = ov[0][0], ov[-1][1]
    flag = "  <-- check" if abs(c - a) > 0.15 or abs(d - b) > 0.25 else ""
    print(f"  {a:6.2f}-{b:6.2f}  clone {c:6.2f}-{d:6.2f}  {c - a:+.2f} / {d - b:+.2f}{flag}")
for c, d in F:
    if not any(b > c and a < d for a, b in R):
        print(f"  clone voice with closed lips: {c:.2f}-{d:.2f}")
