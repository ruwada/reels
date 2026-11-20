"""Speech spans per take from the ElevenLabs-isolated audio (energy VAD): where his lips move."""
import subprocess, numpy as np, json, sys
SR = 16000


def env(path):
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                                     capture_output=True).stdout, np.int16).astype(np.float32) / 32768
    hop = SR // 100
    n = len(x) // hop
    e = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1))
    return np.convolve(e / (np.percentile(e, 99) + 1e-9), np.ones(5) / 5, "same")


def spans(e, th=0.10, mingap=18, minlen=8):
    m = e > th
    out, s = [], None
    for i, v in enumerate(np.r_[m, False]):
        if v and s is None: s = i
        if not v and s is not None: out.append([s, i]); s = None
    merged = []
    for a, b in out:
        if merged and a - merged[-1][1] < mingap: merged[-1][1] = b
        else: merged.append([a, b])
    return [(round(a / 100, 2), round(b / 100, 2)) for a, b in merged if b - a >= minlen]


if __name__ == "__main__":
    res = {}
    for n in sys.argv[1:]:
        res[n] = spans(env(f"/tmp/fx/v4/{n}-iso.mp3"))
        print(n, res[n])
    json.dump(res, open("work/spans.json", "w"), indent=1)
