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
# typing in the police form
t = .05
while t < 1.55: put(key(), t, .035); t += rng.uniform(.04, .08)
put(hit(), T(6) + .06, .2)                                     # stamp ОТПРАВЛЕНО
put(whoosh(.5, 300, 2400), P0(2) - .3, .08)                    # swarm launches
put(pop(500), T(24), .06)                                      # red X
put(hit(), T(36), .1)                                          # through the crack
t = T(37) - .05
while t < T(37) + .85: put(key(), t, .03); t += rng.uniform(.04, .08)
put(hit(), T(51), .14)                                         # БЕСПЛАТНО
put(whoosh(.36, 400, 2600, rise=False), T(57) + .1, .06)       # link slips through
put(hit(), T(67) + .06, .26)                                   # internet OFF
put(whoosh(.8, 150, 1200, rise=False), P0(8) - .4, .06)        # calm turn
out = np.clip(out, -1, 1)
import wave
with wave.open('sfx.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', 'golos.wav', '-i', 'sfx.wav', '-filter_complex',
    '[0:a][1:a]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89[o]',
    '-map', '[o]', '-ar', '48000', 'mix.wav'], check=True)
print('ok')
