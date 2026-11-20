#!/usr/bin/env python3
"""Reel 21, step 3: build the HyperFrames page (scenes, B-roll, subtitles, CTA) over WORK/base_fx.mp4.

    python3 build.py HF_DIR       # writes HF_DIR/index.html; HF_DIR/assets needs base.mp4, broll/, fonts, gsap

Every cue is looked up by word in timeline.json, so the page follows the trimmed take.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
hf = sys.argv[1]
tline = json.load(open(os.path.join(HERE, "timeline.json")))
words, dur = tline["words"], tline["duration"]


def clean(w):
    return re.sub(r"[^\w\-]", "", w.lower())


def cue(key, lo, hi):
    for w in words:
        if lo <= w["s"] <= hi and clean(w["w"]).startswith(clean(key)):
            return round(w["s"], 3)
    raise SystemExit(f"cue {key!r} not found in {lo}-{hi}")


seg = [s["out"] for s in tline["segments"]]
t = {
    # model chips crossed out: «главная проблема … не в модели»
    "models": [cue("главная", 7, 9), cue("модели", 8.5, 10)],
    # scene 1: one question, three routes
    "map1": [seg[5][0], seg[7][1]],
    "map1Cues": [cue("сразу", 17, 19), cue("выяснить", 19, 21), cue("бюджет", 21, 23), cue("продукт", 22, 24),
                 cue("назвать", 23, 25)],
    # «дорого» bubble, then scene 2: four exits
    "dorogo": cue("дорого", 25, 27),
    "map2": [seg[9][0], seg[9][1]],
    "map2Cues": [cue("предложить", 27, 29), cue("уточнить", 28, 30), cue("рассрочку", 29, 31), cue("передать", 30, 32)],
    # business tags over the three quick clips
    "biz": [cue("для", 32, 33), cue("своя", 33, 34), cue("свои", 33.8, 34.5)],
    # «не бот, а система»
    "sys": [cue("это", 38.5, 39), cue("система", 38.7, 39.2), cue("ведет", 40.5, 41.5), seg[11][1]],
    # scene 3: the scenario file
    "map3": [seg[12][0], seg[12][1]],
    "map3Cues": [cue("какие", 44, 45), cue("какую", 45, 46), cue("когда", 46.5, 47), cue("предлагать", 47.5, 48.5)],
    # three steps
    "steps": [cue("воронку", 53, 54.5), cue("прописать", 54, 55), cue("агенту", 56, 57.5), seg[13][1]],
    "cta": seg[14][0],
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
        if prev["w"][-1] in ".?!:," or chars > 15 or len(cur) >= 3 or w["s"] - prev["e"] > 0.45:
            groups.append(cur); cur = []
    cur.append({"w": d, "s": round(w["s"], 3), "e": round(w["e"], 3)})
groups.append(cur)
G = []
scenes = [t["map1"], t["map2"], t["map3"]]
for k, g in enumerate(groups):
    end = max(g[-1]["e"] + 0.3, g[-1]["s"] + 0.2)
    if k + 1 < len(groups):
        end = min(end, groups[k + 1][0]["s"] - 0.07)
    s0 = g[0]["s"] - 0.05
    ink = any(a + 0.4 <= s0 <= b - 0.4 for a, b in scenes)        # dark text on the light scene sheet
    low = s0 < seg[0][1]                                           # under the checklist panel in the hook
    G.append({"s": round(s0, 3), "e": round(end, 3), "words": g, "ink": ink, "low": low})

data = {"dur": dur, "t": t, "text": txt, "groups": G, "broll": json.load(open(os.path.join(HERE, "broll.json")))}
src = open(os.path.join(HERE, "index.src.html")).read()
br = "".join(f'<div class="broll full" id="br{k}"><video class="clip" src="assets/broll/{c["id"]}.mp4" data-start="{c["at"]}" '
             f'data-duration="{c["dur"]}" data-media-start="0" muted playsinline></video></div>' for k, c in enumerate(data["broll"]))
src = src.replace("/*BROLL*/", br).replace("/*DATA*/", json.dumps(data, ensure_ascii=False)).replace("/*DUR*/", str(dur))
open(os.path.join(hf, "index.html"), "w").write(src)
json.dump(t, sys.stdout, ensure_ascii=False); print()
print(len(G), "subtitle groups")
