#!/usr/bin/env python3
"""Lay each English sentence onto the start of its Russian sentence, tempo-fitted to the Russian span.
usage: sync.py TTS_DIR OUT_DIR  ->  OUT_DIR/voice-en.wav, OUT_DIR/words-en.json"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); tts, out = sys.argv[1], sys.argv[2]; os.makedirs(out + "/fit", exist_ok=True)
T = json.load(open(os.path.join(HERE, "..", "timeline.json"))); RW = T["words"]; END = T["duration"]; SR = 48000
R = [(RW[a]["s"], RW[b]["e"]) for a, b in T["sentences"]]
words, parts, prev_end = [], [], 0.0
for i, (s, e) in enumerate(R):
    a = json.load(open(f"{tts}/s{i:02d}.json"))
    cs, st, en = a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"]
    idx = [k for k, c in enumerate(cs) if c.strip()]
    t0, t1, d = max(0, st[idx[0]] - 0.03), en[idx[-1]] + 0.08, en[idx[-1]] - st[idx[0]]
    nxt = R[i + 1][0] if i + 1 < len(R) else END - 0.1
    span = nxt - s - 0.06
    tempo = min(d / span, 1.18) if d > span else (max(d / (0.92 * (e - s)), 0.92) if d < 0.85 * (e - s) else 1.0)
    start = max(s, prev_end + 0.05)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tts}/s{i:02d}.mp3", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}",
                    "-af", f"atempo={tempo:.4f},aresample={SR}", "-ac", "1", f"{out}/fit/s{i}.wav"], check=True)
    cur = None
    for k, c in enumerate(cs):
        if c.strip():
            if cur is None: cur = {"w": "", "s": st[k], "e": en[k]}
            cur["w"] += c; cur["e"] = en[k]
        elif cur: words.append(dict(cur, s=round(start + (cur["s"] - t0) / tempo, 3), e=round(start + (cur["e"] - t0) / tempo, 3))); cur = None
    if cur: words.append(dict(cur, s=round(start + (cur["s"] - t0) / tempo, 3), e=round(start + (cur["e"] - t0) / tempo, 3)))
    prev_end = start + (en[idx[-1]] - t0) / tempo
    parts.append((start, f"{out}/fit/s{i}.wav"))
    print(f"{i:2} ru {s:6.2f}-{e:6.2f} en {start:6.2f}-{prev_end:6.2f} tempo {tempo:.2f} late {start - s:+.2f}")
json.dump(words, open(f"{out}/words-en.json", "w"), ensure_ascii=False, indent=0)
inp, fc = [], []
for j, (s0, f) in enumerate(parts):
    inp += ["-i", f]; fc.append(f"[{j}]adelay={int(s0 * 1000)}:all=1[d{j}]")
fc.append("".join(f"[d{j}]" for j in range(len(parts))) + f"amix=inputs={len(parts)}:normalize=0,apad,atrim=0:{END}[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", ";".join(fc), "-map", "[a]", "-ar", str(SR), f"{out}/voice-en.wav"], check=True)
