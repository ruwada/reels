# v2: lines 0-13 from TTS take tts/a, line 14 (CTA) from tts/cta2 -> golos.wav + words.json ("_" merges into the previous word)
import json, subprocess
L = json.load(open('lines.json')); D = json.load(open('display.json'))
def words_of(name):
    a = json.load(open(f'tts/{name}.json')); ch, st, en = a['characters'], a['character_start_times_seconds'], a['character_end_times_seconds']
    ws, cur = [], None
    for k, c in enumerate(ch):
        if c.strip():
            if cur is None: cur = [c, st[k], en[k]]
            else: cur[0] += c; cur[2] = en[k]
        elif cur: ws.append(cur); cur = None
    if cur: ws.append(cur)
    return ws
LEAD, GAP = 0.45, 0.28
A = words_of('a'); C = words_of('cta2')
nA = sum(len(l.split()) for l in L[:14]); A = A[:nA]
cut0 = max(0, A[0][1] - 0.03); aend = A[-1][2] + 0.06          # end of «отчёту.» in take a
c0 = max(0, C[0][1] - 0.03); off_c = LEAD + (aend - cut0) + GAP
src = [(w, LEAD - cut0) for w in A] + [(w, off_c - c0) for w in C]
words, j = [], 0
for i, (ln, dl) in enumerate(zip(L, D)):
    for k, w in enumerate(ln.split()):
        ww, off = src[j]; assert ww[0] == w, (ww[0], w)
        s, e = round(off + ww[1], 3), round(off + ww[2], 3)
        dw = dl.split()[k]
        if dw == '_': words[-1]['e'] = e
        else: words.append({"w": dw, "s": s, "e": e, "p": i})
        j += 1
assert j == len(src)
total = round(words[-1]['e'] + 1.4, 2)
ph = [{"p": i, "s": [w for w in words if w['p'] == i][0]['s'], "e": [w for w in words if w['p'] == i][-1]['e']} for i in range(len(L))]
ms = lambda x: int(x * 1000)
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', 'tts/a.mp3', '-i', 'tts/cta2.mp3', '-filter_complex',
    f'[0:a]atrim=start={cut0:.3f}:end={aend:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={aend-cut0-0.04:.3f}:d=0.04,adelay={ms(LEAD)}|{ms(LEAD)}[x];'
    f'[1:a]atrim=start={c0:.3f},asetpts=PTS-STARTPTS,adelay={ms(off_c)}|{ms(off_c)}[y];'
    f'[x][y]amix=inputs=2:normalize=0,apad,atrim=0:{total},loudnorm=I=-14:TP=-1.5[o]', '-map', '[o]', '-ar', '48000', '-ac', '1', 'golos.wav'], check=True)
json.dump({"duration": total, "phrases": ph, "words": words}, open('words.json', 'w'), ensure_ascii=False, indent=1)
print(total, len(words), words[-12:])
