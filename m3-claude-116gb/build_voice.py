# TTS take tts/a -> golos.wav + words.json (display spellings by word index; "_" merges into the previous word)
import json, subprocess
L = json.load(open('lines.json')); D = json.load(open('display.json'))
a = json.load(open('tts/a.json'))
ch, st, en = a['characters'], a['character_start_times_seconds'], a['character_end_times_seconds']
LEAD = 0.45
ws, cur = [], None
for k, c in enumerate(ch):
    if c.strip():
        if cur is None: cur = [c, st[k], en[k]]
        else: cur[0] += c; cur[2] = en[k]
    elif cur: ws.append(cur); cur = None
if cur: ws.append(cur)
cut0 = max(0, ws[0][1] - 0.03)
words, j = [], 0
for i, (ln, dl) in enumerate(zip(L, D)):
    lw, dw = ln.split(), dl.split()
    for k, w in enumerate(lw):
        assert ws[j][0] == w, (ws[j][0], w)
        s, e = round(LEAD + ws[j][1] - cut0, 3), round(LEAD + ws[j][2] - cut0, 3)
        if dw[k] == '_': words[-1]['e'] = e
        else: words.append({"w": dw[k], "s": s, "e": e, "p": i})
        j += 1
assert j == len(ws)
total = round(words[-1]['e'] + 1.2, 2)
ph = []
for i in range(len(L)):
    pw = [w for w in words if w['p'] == i]; ph.append({"p": i, "s": pw[0]['s'], "e": pw[-1]['e']})
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', 'tts/a.mp3', '-af',
    f'atrim=start={cut0:.3f},asetpts=PTS-STARTPTS,adelay={int(LEAD*1000)}|{int(LEAD*1000)},apad,atrim=0:{total},loudnorm=I=-14:TP=-1.5',
    '-ar', '48000', '-ac', '1', 'golos.wav'], check=True)
json.dump({"duration": total, "phrases": ph, "words": words}, open('words.json', 'w'), ensure_ascii=False, indent=1)
print(total, len(words))
for i, w in enumerate(words): print(i, w['w'], w['s'], end=' | ')
