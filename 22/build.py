#!/usr/bin/env python3
"""Reel 22, step 3: build the HyperFrames page (funnel scene, overlays, B-roll, subtitles, CTA) over WORK/base_fx.mp4.

    python3 build.py HF_DIR       # writes HF_DIR/index.html; HF_DIR/assets needs base.mp4 (= base_fx), broll/, fonts, gsap

Every cue is looked up by word in timeline.json, so the page follows the trimmed take.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOLD = 1.2                       # fx22.py holds the last CTA frame this long
hf = sys.argv[1]
tline = json.load(open(os.path.join(HERE, "timeline.json")))
words, dur = tline["words"], round(tline["duration"] + HOLD, 3)


def clean(w):
    return re.sub(r"[^\w\-]", "", w.lower())


def cue(key, lo, hi):
    for w in words:
        if lo <= w["s"] <= hi and clean(w["w"]).startswith(clean(key)):
            return round(w["s"], 3)
    raise SystemExit(f"cue {key!r} not found in {lo}-{hi}")


seg = [s["out"] for s in tline["segments"]]
br = json.load(open(os.path.join(HERE, "broll.json")))
t = {
    "offer": [br[0]["at"], br[0]["at"] + br[0]["dur"]],
    "manager": [br[1]["at"], br[1]["at"] + br[1]["dur"]],
    # funnel: «Это автоматизация целого процесса: поиск, анализ, квалификация и передача лида человеку»
    "funnel": [seg[6][0], seg[7][1]],
    "funnelCues": [cue("поиск", 28, 29), cue("анализ", 29, 29.6), cue("квалификация", 29.3, 30), cue("передача", 30.2, 30.6)],
    # «Но полностью автоматизировать продажи … не советовал»
    "auto": [cue("продажи", 33, 33.6), cue("советовал", 34.6, 35), seg[8][1]],
    "deal": [br[2]["at"], br[2]["at"] + br[2]["dur"]],
    "role": [cue("готовить", 39.5, 40), cue("ускорять", 40, 40.4), cue("а", 40.8, 41), cue("бесконтрольно", 41, 41.3), cue("в", 42.85, 43)],
    "cta": seg[11][0],
}
txt = json.load(open(os.path.join(HERE, "ru.json")))

# subtitle groups: up to 3 words / 15 chars, a group ends on punctuation or a pause
groups, cur = [], []


def disp(w):
    return re.sub(r"[.,:;]+$", "", w)


for i, w in enumerate(words):
    d = disp(w["w"])
    if cur:
        prev = words[i - 1]
        chars = sum(len(x["w"]) for x in cur) + len(cur) + len(d)
        if prev["w"][-1] in ".?!:,»" or chars > 15 or len(cur) >= 3 or w["s"] - prev["e"] > 0.45:
            groups.append(cur); cur = []
    cur.append({"w": d, "s": round(w["s"], 3), "e": round(w["e"], 3)})
groups.append(cur)
G = []
UI = (4.95, 10.9)               # the agent's screen fills the top, he sits lower: subtitles go under him
for k, g in enumerate(groups):
    end = max(g[-1]["e"] + 0.3, g[-1]["s"] + 0.2)
    if k + 1 < len(groups):
        end = min(end, groups[k + 1][0]["s"] - 0.07)
    else:
        end = dur
    s0 = g[0]["s"] - 0.05
    G.append({"s": round(s0, 3), "e": round(end, 3), "words": g, "low": UI[0] <= s0 < UI[1]})

data = {"dur": dur, "t": t, "text": txt, "groups": G, "broll": br}
src = open(os.path.join(HERE, "index.src.html")).read()
brh = "".join(f'<div class="broll full" id="br{k}"><video id="v{k}" class="clip" src="assets/broll/{c["id"]}.mp4" data-start="{c["at"]}" '
              f'data-duration="{c["dur"]}" data-media-start="0" muted playsinline></video></div>' for k, c in enumerate(br))
src = src.replace("/*BROLL*/", brh).replace("/*DATA*/", json.dumps(data, ensure_ascii=False)).replace("/*DUR*/", str(dur))
open(os.path.join(hf, "index.html"), "w").write(src)
json.dump(t, sys.stdout, ensure_ascii=False); print()
print(len(G), "subtitle groups")
