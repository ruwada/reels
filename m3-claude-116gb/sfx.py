# Hook + transition sounds (synthesized, no music) mixed under the voice -> code/assets/mix.wav
import json, subprocess, wave, numpy as np
SR = 48000; rng = np.random.default_rng(116)
d = json.load(open('words.json')); W, PH, DUR = d['words'], d['phrases'], d['duration']
T = lambda i: W[i]['s']; P0 = lambda p: PH[p]['s']
def env(n, tau): return np.exp(-np.arange(n) / (tau * SR))
def bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0; return np.fft.irfft(X, len(x))
def nz(s): return s / (np.max(np.abs(s)) + 1e-9)
def whoosh(dur=.4, lo0=300, span=2500, rise=True):
    n = int(dur * SR); x = rng.standard_normal(n); out = np.zeros(n); seg = int(.02 * SR)
    for j in range(0, n - seg, seg):
        p = j / n if rise else 1 - j / n; lo = lo0 + span * p; out[j:j + seg] = bp(x[j:j + seg], lo, lo * 2.2)
    return nz(out * np.sin(np.pi * np.linspace(0, 1, n)) ** 2)
def boom(f0=80, f1=32, dur=1.1):
    n = int(dur * SR); t = np.arange(n) / SR; f = f1 + (f0 - f1) * np.exp(-t * 4)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .35) + bp(rng.standard_normal(n), 200, 3000) * env(n, .015) * .6
    return nz(np.tanh(s * 1.6))
def hit():
    n = int(.4 * SR); t = np.arange(n) / SR
    return nz(np.sin(2 * np.pi * (85 - 35 * t) * t) * env(n, .07) + bp(rng.standard_normal(n), 300, 4000) * env(n, .012) * .5)
def key(big=False):
    n = int(.06 * SR); c = bp(rng.standard_normal(n), 1500, 7000) * env(n, .005 if not big else .009) + np.sin(2 * np.pi * rng.uniform(150, 240) * np.arange(n) / SR) * env(n, .012) * (.6 if not big else 1.2)
    return nz(c) * (rng.uniform(.6, 1) if not big else 1)
def glitch(dur=.18):
    n = int(dur * SR); x = rng.standard_normal(n); hold = int(SR / 900)
    x = np.repeat(x[::hold], hold)[:n]; x = np.round(x * 3) / 3                     # sample-and-hold + bitcrush
    gate = (np.floor(np.arange(n) / (SR * .022)) % 2 == 0).astype(float)
    return nz(bp(x, 400, 9000) * gate * env(n, dur * .6))
def ding(f=(1318.5, 1760.0)):
    n = int(.9 * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for k, fr in enumerate(f):
        o = int(k * .11 * SR); tt = t[:n - o]
        s[o:] += (np.sin(2 * np.pi * fr * tt) + .3 * np.sin(2 * np.pi * fr * 2.01 * tt)) * np.exp(-tt * 5) * np.minimum(1, tt / .004)
    return nz(s)
def tick():
    n = int(.03 * SR); return nz(bp(rng.standard_normal(n), 2500, 9000) * env(n, .003))
def crunch():
    n = int(.25 * SR); x = bp(rng.standard_normal(n), 800, 6000); g = (rng.random(n) < .02).astype(float)
    return nz(np.convolve(x * g, env(int(.004 * SR), .001), 'same') * env(n, .08) + x * env(n, .03) * .2)
out = np.zeros(int((DUR + 1) * SR))
def put(sig, at, g):
    i = max(0, int(at * SR)); out[i:i + len(sig)] += sig[:len(out) - i] * g
# HOOK: Enter clack, drop and glitch before the first word, then files ticking away
put(key(True), 0.0, .5); put(boom(), .02, .55); put(glitch(.24), .02, .22)
t, gap = .3, .11
while t < 2.15: put(tick(), t, .035); t += gap; gap = max(.035, gap * .93)
put(hit(), T(3) + .02, .2)                                        # «116»
put(ding(), T(8) - .05, .16)                                      # «всё цело» ✓ (irony)
put(whoosh(.45, 300, 2400), P0(2) - .25, .07)                     # cut to the report
t = T(14)
for k in range(3): put(key(True), t + k * .16 + .12, .07)          # labels stamped
t = T(36) - .2
while t < T(36) + .4: put(key(), t, .03); t += rng.uniform(.04, .07)
put(glitch(.16), T(38) + .02, .09)                                # the extra rm -rf
put(key(True), T(47), .12)                                        # «стоп»
put(ding(), T(49) - .05, .16)                                     # «успешно остановлена» (same ding)
t = P0(7) + .1
while t < P0(8) - .1: put(tick(), t, .06); t += .25                # clock keeps running
put(boom(70, 30, .9), T(56), .3)                                  # «50 минут»
for i in (58, 59, 60): put(crunch(), T(i) + .02, .06)             # icons crumble
put(whoosh(.7, 150, 1400, rise=False), P0(10) - .35, .06)         # turn to the rules
put(key(True), T(91) + .1, .08)                                   # bypass toggle OFF
out = np.clip(out, -1, 1)
with wave.open('sfx.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', 'golos.wav', '-i', 'sfx.wav', '-filter_complex',
    '[0:a][1:a]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89:level=disabled[o]', '-map', '[o]', '-ar', '48000', 'mix.wav'], check=True)
print('ok')
