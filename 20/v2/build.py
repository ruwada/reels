#!/usr/bin/env python3
"""Reel 20 v2: build the HyperFrames page.

    python3 build.py HF_DIR TAIL

Words come from timeline.json (trimmed take), texts from ru.json, B-roll slots from broll.json.
TAIL = seconds of frozen last frame added after the last word for the CTA (base_fx.mp4 is padded the same).
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
hf, tail = sys.argv[1], float(sys.argv[2])
tline = json.load(open(os.path.join(HERE, "timeline.json")))
words = tline["words"]
txt = json.load(open(os.path.join(HERE, "ru.json")))
dur = round(tline["duration"] + tail, 3)
seg = [s["out"] for s in tline["segments"]]


def clean(w):
    return re.sub(r"[^\w\-+#]", "", w.lower())


def cue(key, lo=0, hi=99):
    k = clean(key)
    for w in words:
        if lo <= w["s"] <= hi and clean(w["w"]).startswith(k):
            return round(w["s"], 3)
    raise SystemExit(f"cue {key!r} not found in {lo}-{hi}")


t = {"hookPill": cue(txt["hook"]["pill_cue"], 0, 3), "hookEnd": seg[0][1]}
t["crm"] = [cue(v, 3, 9.5) for v in txt["crm"]["cues"].values()]
t["crmA"], t["crmB"] = round(t["crm"][0] - 0.12, 3), seg[1][1]
t["q"] = [seg[10][0], cue(txt["q"]["cue"], txt["q"]["lo"], 37), seg[10][1]]
t["split"] = [39.02, cue(txt["split"]["agent_cue"], 39, 42), cue(txt["split"]["human_cue"], 41, 43), seg[11][1]]
t["cta"] = round(seg[12][0] - 0.02, 3)

# subtitle groups: 1-3 words, never two groups at once, hidden where an effect carries the words
MAXC = 15
hide = txt["hide_subs"]
groups, cur = [], []


def disp(w):
    return re.sub(r"[.,:;]+$", "", w)


for i, w in enumerate(words):
    if any(a <= w["s"] < b for a, b in hide):
        if cur:
            groups.append(cur); cur = []
        continue
    d = disp(w["w"])
    if cur:
        prev = words[i - 1]
        chars = sum(len(x["w"]) for x in cur) + len(cur) + len(d)
        if prev["w"][-1] in ".?!:," or chars > MAXC or len(cur) >= 3 or w["s"] - prev["e"] > 0.45:
            groups.append(cur); cur = []
    cur.append({"w": d, "s": round(w["s"], 3), "e": round(w["e"], 3)})
if cur:
    groups.append(cur)
G = []
for k, g in enumerate(groups):
    end = max(g[-1]["e"] + 0.3, g[-1]["s"] + 0.2)
    if k + 1 < len(groups):
        end = min(end, groups[k + 1][0]["s"] - 0.07)
    for a, b in hide:                       # a group never runs into a hidden span
        if g[0]["s"] < a < end:
            end = a
    G.append({"s": round(g[0]["s"] - 0.05, 3), "e": round(end, 3), "words": g})

data = {"dur": dur, "t": t, "text": txt, "groups": G, "broll": json.load(open(os.path.join(HERE, "broll.json")))}
src = open(os.path.join(HERE, "index.src.html")).read()
br = "".join(f'<div class="broll full" id="br{k}"><video class="clip" src="assets/broll/{c["id"]}.mp4" data-start="{c["at"]}" '
             f'data-duration="{c["dur"]}" data-media-start="0" muted playsinline></video></div>' for k, c in enumerate(data["broll"]))
src = src.replace("/*BROLL*/", br).replace("/*DATA*/", json.dumps(data, ensure_ascii=False)).replace("/*DUR*/", str(dur))
open(os.path.join(hf, "index.html"), "w").write(src)
json.dump(t, sys.stdout, ensure_ascii=False); print()
print(len(G), "subtitle groups")
