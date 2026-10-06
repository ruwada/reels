#!/usr/bin/env python3
"""Sound design for the Zaur cut: no music and no instruments, only keyboard, whooshes, pops and a stamp.
Whooshes on scene changes, keyboard where Islam types (and quietly in every pause of the voice),
pops when list items / chips appear. usage: sfx.py voice.wav out.wav"""
import subprocess, sys
import numpy as np

SR = 48000
rng = np.random.default_rng(5)


def env(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def key(heavy=False):
    n = int(0.06 * SR); c = bp(rng.standard_normal(n), 1800, 7000) * env(n, 0.004)
    th = np.sin(2 * np.pi * rng.uniform(170, 260) * np.arange(n) / SR) * env(n, 0.012) * 0.6
    up = np.zeros(n); k = int(rng.uniform(0.025, 0.04) * SR)
    up[k:] = bp(rng.standard_normal(n - k), 2500, 8000) * env(n - k, 0.003) * 0.35
    s = c + th + up
    if heavy:
        s = s * 1.4 + np.sin(2 * np.pi * 120 * np.arange(n) / SR) * env(n, 0.02) * 0.8
    return s / np.max(np.abs(s)) * rng.uniform(0.55, 1.0)


def typing(dur, rate=9):
    out = np.zeros(int(dur * SR) + SR); t = 0.02
    while t < dur:
        k = key(); i = int(t * SR); out[i:i + len(k)] += k
        t += rng.uniform(0.6, 1.4) / rate
        if rng.random() < 0.07:
            t += rng.uniform(0.12, 0.3)
    return out[:int(dur * SR)]


def whoosh(d=0.45):
    n = int(d * SR); x = rng.standard_normal(n); out = np.zeros(n); seg = int(0.02 * SR)
    for j in range(0, n - seg, seg):
        lo = 300 + 2500 * j / n; out[j:j + seg] = bp(x[j:j + seg], lo, lo * 2.2)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return out * e / np.max(np.abs(out * e))


def stamp():
    n = int(0.35 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (90 - 40 * t) * t) * env(n, 0.06) + bp(rng.standard_normal(n), 200, 3000) * env(n, 0.01) * 0.7
    return s / np.max(np.abs(s))


def pop():
    n = int(0.09 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (700 - 3000 * t) * t) * env(n, 0.018)
    return s / np.max(np.abs(s))


def load(p):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                        capture_output=True, check=True).stdout, np.float32)


# scene changes on the reel timeline (same as build.py / edit.json)
CUTS = [5.1, 11.7, 15.6, 20.0, 22.9, 24.9, 30.75, 35.2, 36.9, 42.0, 48.3, 50.2, 56.55, 60.55]
TYPING = [(15.9, 20.0, 0.10), (20.0, 22.85, 0.22), (60.7, 65.35, 0.12)]  # Islam / the CTA guy at the keyboard
POPS = [0.15, 15.85, 16.4, 16.95, 17.5, 20.1, 35.62, 36.22]  # hook plate, contract items, "Разработка", braces chips
STAMP = 60.85  # CTA plate lands


def main(voice_path, out):
    v = load(voice_path); n = len(v); mix = np.zeros(n + SR)

    def put(sig, t, g):
        i = int(t * SR); m = min(len(sig), len(mix) - i)
        if m > 0:
            mix[i:i + m] += sig[:m] * g

    for t in CUTS:
        put(whoosh(), t - 0.25, 0.16)
    for s, e, g in TYPING:
        put(typing(e - s), s, g)
    for t in POPS:
        put(pop(), t, 0.14)
    put(stamp(), STAMP, 0.3)
    # quiet keyboard taps in every pause of the voice longer than 0.35 s, so no silence is left
    hop = int(0.05 * SR); rms = np.array([np.sqrt(np.mean(v[i:i + hop] ** 2)) for i in range(0, n - hop, hop)])
    silent = rms < 0.02; i = 0
    while i < len(silent):
        if silent[i]:
            j = i
            while j < len(silent) and silent[j]:
                j += 1
            s, e = i * 0.05 + 0.05, j * 0.05 - 0.05
            if e - s > 0.25 and not any(a <= s <= b for a, b, _ in TYPING):
                put(typing(e - s, rate=8), s, 0.11)
            i = j
        else:
            i += 1
    mix = mix[:n]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", out],
                   input=mix.astype(np.float32).tobytes(), check=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
