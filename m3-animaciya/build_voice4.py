# v4 voice: take tts3/s1 (speed 1.0, same settings as the approved b) + breathing pauses at section borders
# + pitch accents (PSOLA, voice kept): questions get a peak on the stressed syllable of the question word and a rise at
# the end; emotional words get a pitch peak. -> golos.wav + words.json
import json, subprocess, numpy as np, parselmouth
from parselmouth.praat import call
TAKE = 'tts3/s1'
L = json.load(open('lines.json')); D = json.load(open('display.json'))
a = json.load(open(TAKE + '.json')); ch, st, en = a['characters'], a['character_start_times_seconds'], a['character_end_times_seconds']
LEAD = 0.35
ws, cur = [], None                       # [text, start, end, firstCharIdx]
for k, c in enumerate(ch):
    if c.strip():
        if cur is None: cur = [c, st[k], en[k], k]
        else: cur[0] += c; cur[2] = en[k]
    elif cur: ws.append(cur); cur = None
if cur: ws.append(cur)
lw = [w for ln in L for w in ln.split()]; assert [w[0] for w in ws] == lw
pidx = [i for i, ln in enumerate(L) for _ in ln.split()]
def wi(phrase, word):                    # index of a word (TTS spelling, w/o punctuation) inside a phrase
    return next(j for j, w in enumerate(ws) if pidx[j] == phrase and w[0].strip('.,?:«»!') == word)
# pauses (s) inserted AFTER a word
PAUSE = {wi(0, 'рисовал'): .12, wi(1, 'Кодом'): .22, wi(2, 'открывал'): .3, wi(5, 'ролик'): .35, wi(6, 'научиться'): .22,
         wi(6, 'шага'): .3, wi(7, 'видео'): .2, wi(8, 'сетка'): .2, wi(9, 'началом'): .15, wi(10, 'кадров'): .3,
         wi(11, 'Эффектс'): .45, wi(11, 'совсем'): .2, wi(12, 'мощно'): .4}
cut0 = max(0, ws[0][1] - .03)
cuts = sorted((round((ws[j][2] + ws[j + 1][1]) / 2, 3), p) for j, p in PAUSE.items())
def T(t):                                # raw take time -> output time
    return LEAD + t - cut0 + sum(p for c, p in cuts if c <= t)
# assemble audio with silences inserted
raw = parselmouth.Sound(TAKE + '.mp3').convert_to_mono() if False else None
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', TAKE + '.mp3', '-ac', '1', '-ar', '48000', '/tmp/v4raw.wav'], check=True)
snd = parselmouth.Sound('/tmp/v4raw.wav'); sr = int(snd.sampling_frequency); y = snd.values[0]
parts, prev = [np.zeros(int(LEAD * sr))], int(cut0 * sr)
for c, p in cuts:
    i = int(c * sr); seg = y[prev:i].copy(); f = int(.012 * sr); seg[-f:] *= np.linspace(1, 0, f)
    parts += [seg, np.zeros(int(p * sr))]; prev = i
seg = y[prev:].copy(); parts.append(seg)
out = np.concatenate(parts)
total = round(T(ws[-1][2]) + .9, 2); out = np.pad(out, (0, max(0, int(total * sr) - len(out))))[:int(total * sr)]
voice = parselmouth.Sound(out, sr)
# ---- pitch accents: (word index, stressed chars, peak multiplier, end-rise multiplier or None) ----
def syl(j, s):                           # output times of substring s inside word j
    k0 = ws[j][3] + ws[j][0].lower().find(s.lower()); assert ws[j][0].lower().find(s.lower()) >= 0, (ws[j][0], s)
    return T(st[k0]), T(en[k0 + len(s) - 1])
ACC = [
    (wi(0, 'никто'), 'то', 1.18, None),
    (wi(6, 'Как'), 'Как', 1.28, (wi(6, 'научиться'), 'ться', 1.25)),            # «Как этому научиться?»
    (wi(6, 'Три'), 'Три', 1.15, None),
    (wi(10, 'сотни'), 'сот', 1.18, None),
    (wi(11, 'Заменяет'), 'ня', 1.35, (wi(11, 'Эффектс'), 'фектс', 1.4)),      # «Заменяет ли это After Effects?»
    (wi(12, 'мощно'), 'мо', 1.3, None),
]
for j, s, peak, endr in ACC:
    t_s, t_e = syl(j, s)
    t_we = T(ws[endr[0]][2]) if endr else T(ws[j][2])
    seg0, seg1 = T(ws[j][1]) - .25, t_we + .25
    part = voice.extract_part(seg0, seg1, parselmouth.WindowShape.RECTANGULAR, 1, True)
    man = call(part, "To Manipulation", 0.01, 70, 320)
    pitch = part.to_pitch(time_step=0.01, pitch_floor=70, pitch_ceiling=320)
    if endr: r_s, r_e = syl(endr[0], endr[1])
    def mult(t):
        m = 1.0
        if t_s - .06 <= t < t_s: m = 1 + (peak - 1) * (t - (t_s - .06)) / .06
        elif t_s <= t < t_e: m = peak
        elif t_e <= t < t_e + .1: m = peak - (peak - 1) * (t - t_e) / .1
        if endr and r_s - .06 <= t <= r_e + .05:
            k = min(1, max(0, (t - (r_s - .06)) / max(.05, r_e - r_s + .06))); m = max(m, 1 + (endr[2] - 1) * k)
        return m
    new = call("Create PitchTier", "new", seg0, seg1)
    for t in np.arange(seg0 + .005, seg1, .01):
        v = call(pitch, "Get value at time", t, "Hertz", "linear")
        if v == v and v > 0: call(new, "Add point", t, v * mult(t))
    call([new, man], "Replace pitch tier")
    res = call(man, "Get resynthesis (overlap-add)").values[0]
    yy = voice.values[0]; i = int(round(seg0 * sr)); n = min(len(res), len(yy) - i)
    w = np.ones(n); fd = int(.015 * sr); w[:fd] = np.linspace(0, 1, fd); w[-fd:] = np.linspace(1, 0, fd)
    yy[i:i + n] = yy[i:i + n] * (1 - w) + res[:n] * w
    if s == 'мо':                        # a touch louder on «мощно»
        a0, a1 = int(T(ws[j][1]) * sr), int(T(ws[j][2]) * sr); g = np.ones(a1 - a0) * 1.25; g[:400] = np.linspace(1, 1.25, 400); g[-400:] = np.linspace(1.25, 1, 400); yy[a0:a1] *= g
    voice = parselmouth.Sound(yy, sr)
voice.save('/tmp/v4acc.wav', 'WAV')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', '/tmp/v4acc.wav', '-af', 'loudnorm=I=-14:TP=-1.5', '-ar', '48000', 'golos.wav'], check=True)
words = [{"w": dw, "s": round(T(ws[j][1]), 3), "e": round(T(ws[j][2]), 3), "p": pidx[j]} for j, dw in enumerate(w for dl in D for w in dl.split())]
ph = [{"p": i, "s": min(w['s'] for w in words if w['p'] == i), "e": max(w['e'] for w in words if w['p'] == i)} for i in range(len(L))]
json.dump({"duration": total, "phrases": ph, "words": words}, open('words.json', 'w'), ensure_ascii=False, indent=1)
print(total, len(words))
