"""v8: the approved clone voice is kept natural (its usual speed, no stretching: stretching made it sound
"through a radio"), and HIS PICTURE is retimed to the voice instead: word by word, his footage (60 fps source)
is sped up / slowed down so that each word's lips land on the clone's word. No colour filter.
Writes work/warp.json (source-time -> reel-time map per take), work/tight-v8.mp4 and work/tight-voice.wav."""
import difflib, hashlib, json, os, subprocess, wave
import numpy as np
from plan import FPS
from voice_phr import PHRASES, SPEED, CACHE, load, onset, trim, SR

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = f"{HERE}/work"
W, H, SRC_FPS = 1080, 1920, 60
DROP = {"0349", "0356"}            # he dragged these words far slower than any natural voice
LEAD, TAIL = 0.13, 0.15
TAIL_OF = {"0368": 0.95}           # the CTA holds on the phone a little
GAP = (0.18, 0.40)                 # pause between his phrases inside a take, clamped
SPEED_LIM = (0.65, 1.75)           # how fast his picture may play locally (source s per reel s)


def norm(w):
    return w.lower().replace("ё", "е").strip(".,!?—-:; ")


def match(his, clone):
    """Pairs (his word, clone word) in order, by spelling similarity (ASR misspells both sides)."""
    a, b = [norm(x["w"]) for x in his], [norm(x["w"]) for x in clone]
    n, m = len(a), len(b)
    D = np.zeros((n + 1, m + 1)); P = {}
    D[:, 0] = np.arange(n + 1) * 0.6; D[0, :] = np.arange(m + 1) * 0.6
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = difflib.SequenceMatcher(None, a[i - 1], b[j - 1]).ratio()
            opts = [(D[i - 1, j - 1] + (1 - s), "m"), (D[i - 1, j] + 0.6, "u"), (D[i, j - 1] + 0.6, "l")]
            D[i, j], P[i, j] = min(opts)
    out, i, j = [], n, m
    while i > 0 and j > 0:
        mv = P[i, j]
        if mv == "m":
            if difflib.SequenceMatcher(None, a[i - 1], b[j - 1]).ratio() >= 0.5:
                out.append((his[i - 1], clone[j - 1]))
            i, j = i - 1, j - 1
        elif mv == "u": i -= 1
        else: j -= 1
    return out[::-1]


def clone_file(take, ph, i):
    text = ph[i][0]
    prev = " ".join(p[0] for p in ph[:i]); nxt = " ".join(p[0] for p in ph[i + 1:])
    return f"{CACHE}/{hashlib.md5(f'{text}|{SPEED:.2f}|{prev}|{nxt}'.encode()).hexdigest()[:12]}.mp3"


def clean(src, out):
    """Keep the map monotonic and every local speed inside SPEED_LIM (drop anchors that break it)."""
    pts = sorted(zip(src, out))
    keep = [pts[0]]
    for s, o in pts[1:]:
        ds, do = s - keep[-1][0], o - keep[-1][1]
        if do > 0.02 and SPEED_LIM[0] <= ds / do <= SPEED_LIM[1]:
            keep.append((s, o))
    return [p[0] for p in keep], [p[1] for p in keep]


def build_take(take):
    ph = PHRASES[take]
    iso = load(f"/tmp/fx/v4/{take}-iso.mp3")
    hop = SR // 100; n = len(iso) // hop
    ref = np.percentile(np.convolve(np.sqrt((iso[: n * hop].reshape(n, hop) ** 2).mean(1)), np.ones(5) / 5, "same"), 98)
    his_words = json.load(open(f"/tmp/fx/v4/tri-{take}/words.json"))
    src, out, clips = [], [], []
    t = LEAD
    for i, (text, s0, s1) in enumerate(ph):
        x = load(clone_file(take, ph, i))
        y = trim(x)
        c_on = onset(y, SR); c_len = len(y) / SR
        h_on = onset(iso, SR, s0 - 0.2, s0 + 0.4, ref)
        if i == 0:
            src.append(h_on - LEAD); out.append(0.0)
        else:
            gap = float(np.clip(h_on - prev_off, *GAP))
            t = out[-1] + gap
        o0 = t                                    # clone onset lands here (reel-of-take seconds)
        src.append(h_on); out.append(o0)
        cw = json.load(open(f"{WORK}/clonew/{take}-{i}/words.json"))
        y_shift = (np.where(np.abs(x) > 0.006)[0][0] - int(0.03 * SR)) / SR   # trim() start inside x
        hw = [w for w in his_words if s0 - 0.25 <= w["s"] <= s1 + 0.1]
        for hwd, cwd in match(hw, cw)[1:]:        # first word = the onset anchor already
            src.append(hwd["s"]); out.append(o0 + (cwd["s"] - y_shift - c_on))
        src.append(s1); out.append(o0 + (c_len - c_on) - 0.04)
        clips.append((o0 - c_on, y))
        prev_off = s1
    src.append(prev_off + TAIL_OF.get(take, TAIL)); out.append(out[-1] + TAIL_OF.get(take, TAIL))
    src, out = clean(src, out)
    return src, out, clips


def decode(take, s_a, s_b):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, s_a - 0.1):.3f}", "-t", f"{s_b - s_a + 0.3:.3f}",
                          "-i", f"/tmp/fx/v4/{take}.mov", "-vf", f"fps={SRC_FPS},scale={W}:{H}:flags=lanczos",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return max(0, s_a - 0.1), np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


if __name__ == "__main__":
    takes = [t for t in PHRASES if t not in DROP]
    warp, parts, acc = {}, [], 0.0
    voice = []
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "12", "-preset", "fast",
                            "-pix_fmt", "yuv420p", f"{WORK}/tight-v8.mp4"], stdin=subprocess.PIPE)
    for take in takes:
        src, out, clips = build_take(take)
        nfr = round(out[-1] * FPS)
        t0, fr = decode(take, src[0], src[-1])
        for k in range(nfr):
            s = float(np.interp(k / FPS, out, src))
            enc.stdin.write(fr[min(len(fr) - 1, max(0, round((s - t0) * SRC_FPS)))].tobytes())
        warp[take] = dict(start=acc, src=src, out=out, frames=nfr)
        for o, y in clips:
            voice.append((acc + o, y))
        sp = np.diff(src) / np.diff(out)
        print(f"{take} {nfr / FPS:5.2f}s  picture speed {sp.min():.2f}..{sp.max():.2f}  anchors {len(src)}", flush=True)
        acc += nfr / FPS
    enc.stdin.close(); enc.wait()
    warp["_end"] = acc
    json.dump(warp, open(f"{WORK}/warp.json", "w"), indent=1)
    track = np.zeros(int((acc + 1) * SR), np.float32)
    for o, y in voice:
        y = y.copy(); f = int(0.008 * SR); y[:f] *= np.linspace(0, 1, f); y[-4 * f:] *= np.linspace(1, 0, 4 * f)
        i0 = int(o * SR)
        if i0 < 0: y, i0 = y[-i0:], 0
        track[i0:i0 + len(y)] += y
    wv = wave.open(f"{WORK}/tight-voice.wav", "wb"); wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR)
    wv.writeframes((np.clip(track[: int(acc * SR)], -1, 1) * 32767).astype(np.int16).tobytes()); wv.close()
    print(f"total {acc:.2f}s")
