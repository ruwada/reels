#!/usr/bin/env python3
"""Voice + three quiet whooshes on the scene entries -> loudnorm -14 LUFS, muxed onto the silent render.
usage: mix.py VIDEO VOICE.wav OUT.mp4"""
import subprocess, sys
import numpy as np
SR = 48000; rng = np.random.default_rng(20)
WHOOSH_AT, GAIN = [3.73, 39.52], 0.07   # rule: minimal, only on long scene transitions


def bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def whoosh(d=0.5):
    n = int(d * SR); x = rng.standard_normal(n); out = np.zeros(n); seg = int(0.02 * SR)
    for j in range(0, n - seg, seg):
        lo = 300 + 2500 * j / n; out[j:j + seg] = bp(x[j:j + seg], lo, lo * 2.2)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return out * e / np.max(np.abs(out * e))


video, voice, out = sys.argv[1:4]
v = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", voice, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                 capture_output=True, check=True).stdout, np.float32).astype(np.float64)
peak = np.max(np.abs(v)) or 1
for t in WHOOSH_AT:
    w = whoosh() * GAIN * peak; i = int((t - 0.3) * SR); v[i:i + len(w)] += w[:len(v) - i]
tmp = out + ".wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", tmp], input=v.astype(np.float32).tobytes(), check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", tmp, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out], check=True)
print(out)
