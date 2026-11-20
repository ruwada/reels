#!/usr/bin/env python3
"""Sound design for the Zaur cut: no music and no instruments, only a few quiet whooshes and keyboard taps
on the long scene transitions. usage: sfx.py voice.wav out.wav"""
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


def load(p):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                        capture_output=True, check=True).stdout, np.float32)


# Minimal, by the user's request (2026-10-06): quiet, only on the long scene transitions, never under speech,
# nothing on Zaur's reaction and the CTA at the end.
WHOOSH = [15.45, 19.85, 22.7]           # into the agreement, into the night coding, into the app
TYPING = [(21.8, 22.75, 0.07)]          # night coding: the pause after "Вот что получилось"


def main(voice_path, out):
    v = load(voice_path); n = len(v); mix = np.zeros(n + SR)

    def put(sig, t, g):
        i = int(t * SR); m = min(len(sig), len(mix) - i)
        if m > 0:
            mix[i:i + m] += sig[:m] * g

    for t in WHOOSH:
        put(whoosh(), t - 0.2, 0.07)
    for s, e, g in TYPING:
        put(typing(e - s), s, g)
    mix = mix[:n]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", out],
                   input=mix.astype(np.float32).tobytes(), check=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
