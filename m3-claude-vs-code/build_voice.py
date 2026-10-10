# Joins the TTS phrases into one voice track (trimmed breaths, fixed gaps) and writes word timings.
import json, subprocess
N = len(json.load(open('lines.json')))
BEST = {int(k): v['best'] for k, v in json.load(open('pick.json')).items()}  # take chosen by ear (pick.py)
GAP, LEAD = 0.28, 0.35          # pause between phrases, silence before the first word
FIX = {("Клод", "Код"): "Claude Code", ("Клод", "Код."): "Claude Code.", ("Клодом",): "Claude", ("Клод",): "Claude", ("«код»,",): "«КОД»,"}
words, parts, t = [], [], LEAD
for i in range(N):
    a = json.load(open(f'tts/p{i}_{BEST[i]}.json'))
    ch, st, en = a['characters'], a['character_start_times_seconds'], a['character_end_times_seconds']
    first = next(k for k, c in enumerate(ch) if c.strip())
    last = max(k for k, c in enumerate(ch) if c.strip())
    cut0, cut1 = max(0, st[first] - 0.04), en[last] + 0.12
    ws, cur = [], None
    for k, c in enumerate(ch):
        if c.strip():
            if cur is None: cur = [c, st[k], en[k]]
            else: cur[0] += c; cur[2] = en[k]
        elif cur: ws.append(cur); cur = None
    if cur: ws.append(cur)
    out, j = [], 0
    while j < len(ws):
        for key, rep in FIX.items():
            if tuple(w[0] for w in ws[j:j+len(key)]) == key:
                out.append([rep, ws[j][1], ws[j+len(key)-1][2]]); j += len(key); break
        else:
            out.append(ws[j]); j += 1
    o2 = []
    for w in out:
        if any(ch.isalnum() for ch in w[0]) or not o2: o2.append(w)
        else: o2[-1] = [o2[-1][0] + ' ' + w[0], o2[-1][1], o2[-1][2]]
    out = o2
    for w, s, e in out:
        words.append({"w": w, "s": round(t + s - cut0, 3), "e": round(t + e - cut0, 3), "p": i})
    parts.append((i, cut0, cut1, t)); t += (cut1 - cut0) + (0.06 if i == 0 else GAP)  # the hook question runs straight into its answer
total = t + 0.6
flt, inp = [], []
for n, (i, c0, c1, at) in enumerate(parts):
    inp += ['-i', f'tts/p{i}_{BEST[i]}.mp3']
    flt.append(f"[{n}:a]atrim={c0:.3f}:{c1:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={c1-c0-0.03:.3f}:d=0.03,adelay={int(at*1000)}|{int(at*1000)}[a{n}]")
flt.append(''.join(f'[a{n}]' for n in range(len(parts))) + f"amix=inputs={len(parts)}:normalize=0,apad,atrim=0:{total:.3f},loudnorm=I=-14:TP=-1.5[out]")
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *inp, '-filter_complex', ';'.join(flt), '-map', '[out]', '-ar', '48000', 'golos.wav'], check=True)
json.dump({"duration": round(total, 2), "phrases": [{"p": i, "s": round(at, 3), "e": round(at + c1 - c0, 3)} for i, c0, c1, at in parts], "words": words},
          open('words.json', 'w'), ensure_ascii=False, indent=1)
print(round(total, 2), len(words))
