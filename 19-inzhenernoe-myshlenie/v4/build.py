#!/usr/bin/env python3
"""Build the HyperFrames page for one language.

    python3 build.py ru HF_DIR            # words from timeline.json (the trimmed Russian take)
    python3 build.py en HF_DIR words.json  # words of the English voice-over on the same time axis

Scene windows and B-roll slots are shared by both languages (the English voice is laid sentence by
sentence onto the Russian timing); only the texts, subtitle words and in-scene cues differ.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
lang, hf = sys.argv[1], sys.argv[2]
tline = json.load(open(os.path.join(HERE, "timeline.json")))
words = tline["words"] if lang == "ru" else json.load(open(sys.argv[3]))
txt = json.load(open(os.path.join(HERE, f"{lang}.json")))
dur = tline["duration"]
sent_start = [tline["words"][a]["s"] for a, b in tline["sentences"]]


def clean(w):
    return re.sub(r"[^\w\-+#]", "", w.lower())


def cue(key, lo, hi):
    k = clean(key)
    for w in words:
        if lo - 0.6 <= w["s"] <= hi + 0.6 and clean(w["w"]).startswith(k):
            return round(w["s"], 3)
    raise SystemExit(f"cue {key!r} not found in {lo}-{hi}")


W = {"pr": (12.08, 15.74), "found": (50.25, 55.33)}
FX = json.load(open(os.path.join(HERE, "fxspans.json")))   # written by fx19.py: where each effect sits
t = {"hookFlip": round(sent_start[1] - 0.06, 3), "hookEnd": 4.5, "pr": W["pr"], "found": W["found"]}
t["foundTitle"] = cue(txt["found"]["title_cue"], *W["found"])
t["slabCues"] = [cue(k, *W["found"]) for k, _ in txt["found"]["slabs"]]
t["aiDrop"] = round(min(t["slabCues"][-1] + 0.3, W["found"][1] - 0.45), 3)
t["speed"] = [cue(txt["speed"]["l1_cue"], 55.3, 57.2), cue(txt["speed"]["l2_cue"], 57.1, 60.9), FX["vertigo"][1]]
t["cta"] = round(sent_start[22] - 0.05, 3)
assert t["slabCues"] == sorted(t["slabCues"])
HI = [FX["check"]]                                          # subtitles move above the checklist panel

# subtitle groups
MAXC = 15 if lang == "ru" else 17
groups, cur = [], []


def disp(w):
    return re.sub(r"[.,:;]+$", "", w).replace("…", "")


for i, w in enumerate(words):
    d = disp(w["w"])
    if cur:
        prev = words[i - 1]
        chars = sum(len(x["w"]) for x in cur) + len(cur) + len(d)
        if prev["w"][-1] in ".?!:," or chars > MAXC or len(cur) >= 3 or w["s"] - prev["e"] > 0.45:
            groups.append(cur); cur = []
    cur.append({"w": d, "s": round(w["s"], 3), "e": round(w["e"], 3)})
groups.append(cur)
G = []
for k, g in enumerate(groups):
    end = g[-1]["e"] + 0.3
    end = max(end, g[-1]["s"] + 0.2)
    if k + 1 < len(groups):
        end = min(end, groups[k + 1][0]["s"] - 0.07)   # never two groups on screen at once
    s0 = g[0]["s"] - 0.05
    G.append({"s": round(s0, 3), "e": round(end, 3), "words": g, "hi": any(a - 0.1 <= s0 < b for a, b in HI)})

data = {"lang": lang, "dur": dur, "t": t, "text": txt, "groups": G,
        "broll": json.load(open(os.path.join(HERE, "broll.json")))}
src = open(os.path.join(HERE, "index.src.html")).read()
br = "".join(f'<div class="broll full" id="br{k}"><video id="brv{k}" class="clip" src="assets/broll/{c["id"]}.mp4" data-start="{c["at"]}" '
             f'data-duration="{c["dur"]}" data-media-start="0" muted playsinline></video></div>' for k, c in enumerate(data["broll"]))
src = src.replace("/*BROLL*/", br).replace("/*DATA*/", json.dumps(data, ensure_ascii=False)).replace("/*DUR*/", str(dur))
if lang != "ru":
    src = src.replace('<html lang="ru">', f'<html lang="{lang}">')
open(os.path.join(hf, "index.html"), "w").write(src)
json.dump({"dur": dur, "t": t}, sys.stdout, ensure_ascii=False); print()
print(len(G), "subtitle groups")
