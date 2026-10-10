# Quiet transition sounds under the voice (synthesized, no music) -> code/assets/mix.wav
import json, subprocess, numpy as np
SR = 48000; rng = np.random.default_rng(7)
d = json.load(open('words.json')); W, PH, DUR = d['words'], d['phrases'], d['duration']
T = lambda i: W[i]['s']; P0 = lambda p: PH[p]['s']
def env(n, tau): return np.exp(-np.arange(n) / (tau * SR))
def bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x))
def whoosh(dur=.4, lo0=300, span=2500, rise=True):
    n = int(dur * SR); x = rng.standard_normal(n); out = np.zeros(n); seg = int(.02 * SR)
    for j in range(0, n - seg, seg):
        p = j / n if rise else 1 - j / n; lo = lo0 + span * p; out[j:j + seg] = bp(x[j:j + seg], lo, lo * 2.2)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2; o = out * e; return o / np.max(np.abs(o))
def hit():
    n = int(.4 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (85 - 35 * t) * t) * env(n, .07) + bp(rng.standard_normal(n), 300, 4000) * env(n, .012) * .5
    return s / np.max(np.abs(s))
def pop(f0=700):
    n = int(.08 * SR); t = np.arange(n) / SR; s = np.sin(2 * np.pi * (f0 - 2500 * t) * t) * env(n, .016); return s / np.max(np.abs(s))
def key():
    n = int(.05 * SR); c = bp(rng.standard_normal(n), 1800, 7000) * env(n, .004) + np.sin(2 * np.pi * rng.uniform(170, 260) * np.arange(n) / SR) * env(n, .01) * .6
    return c / np.max(np.abs(c)) * rng.uniform(.6, 1)
out = np.zeros(int((DUR + 1) * SR))
def put(sig, at, g):
    i = max(0, int(at * SR)); out[i:i + len(sig)] += sig[:len(out) - i] * g
put(whoosh(1.0, 150, 1800), .3, .16)                         # zoom into the laptop
for p in range(1, 14):
    if p == 11: put(hit(), P0(p) - .02, .2); continue        # hard cut to the question
    dur = .36 if p % 2 else .44
    put(whoosh(dur, 250 + 120 * (p % 3), 2400, rise=p % 2 == 1), P0(p) - dur * .6, .11)
for at, g in [(T(45), .17), (T(119) - .1, .2)]: put(hit(), at, g)   # «mp4» and «мощно»
for k in range(3): put(pop(650 + 120 * k), T(51) - .02 + k * .12, .08)  # 1 2 3
t = T(54)
while t < T(54) + .75: put(key(), t, .05); t += rng.uniform(.045, .09)  # typed command
for k in range(9): put(pop(900 + 40 * k), T(125) - .05 + k * .06, .045)   # CTA letters
for i in (85, 86, 88): put(pop(560), T(i) - .02, .06)                     # edit bubbles
out = np.clip(out, -1, 1)
import wave
with wave.open('sfx.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', 'golos.wav', '-i', 'sfx.wav', '-filter_complex',
    '[0:a][1:a]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89[o]',
    '-map', '[o]', '-ar', '48000', 'code/assets/mix.wav'], check=True)
print('ok')
