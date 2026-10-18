#!/usr/bin/env python3
"""Reel 23, step 3: build the HyperFrames page (night-shift scene, overlays, B-roll, subtitles, CTA) over WORK/base_fx.mp4.

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
    # «Не отвечает вам в чат» -> struck on «чат»; «а реально выполняет задачи» over the running code
    "chat": [seg[1][0], cue("чат", 4.6, 4.9), br[0]["at"]],
    "does": [br[0]["at"], br[0]["at"] + br[0]["dur"]],
    # night shift log: «получает задачу, изучает репозиторий, … готовит результат на проверку»
    "night": [seg[2][0], seg[2][1]],
    "nightCues": [cue("получает", 7, 7.3), cue("изучает", 7.9, 8.1), cue("находит", 9.1, 9.4), cue("вносит", 10.2, 10.5),
                  cue("запускает", 11.1, 11.3), cue("исправляет", 12.4, 12.6), cue("готовит", 13.3, 13.5)],
    "morning": [br[1]["at"] + 0.15, br[2]["at"] + br[2]["dur"]],
    # «уже не вопрос: что мне сегодня написать, а готовую работу, которую осталось перепроверить»
    "q": [cue("что", 17.5, 17.6), cue("а", 19.0, 19.2)],
    "pr": [cue("готовую", 19.1, 19.3), cue("перепроверить", 20.4, 20.6), seg[4][1]],
    # «не автодополнением кода, а исполнителем долгих задач»
    "auto": [cue("автодополнением", 25.1, 25.3), cue("а", 26.3, 26.4)],
    "exec": [cue("исполнителем", 26.4, 26.5), seg[6][1]],
    "code": [br[4]["at"], br[4]["at"] + br[4]["dur"]],
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
DIM = [(15.62, 17.03)]          # the bright morning clip: white words get a dark chip
LOW = [(0.0, 3.83), (6.63, 14.87), (27.63, 34.5)]   # night clock on his chest / the night-shift log: subtitles go under them
for k, g in enumerate(groups):
    end = max(g[-1]["e"] + 0.3, g[-1]["s"] + 0.2)
    if k + 1 < len(groups):
        end = min(end, groups[k + 1][0]["s"] - 0.07)
    else:
        end = dur
    s0 = g[0]["s"] - 0.05
    G.append({"s": round(s0, 3), "e": round(end, 3), "words": g, "low": any(a <= s0 < b for a, b in LOW),
              "dim": any(a - 0.3 <= s0 < b for a, b in DIM)})

data = {"dur": dur, "t": t, "text": txt, "groups": G, "broll": br}
src = open(os.path.join(HERE, "index.src.html")).read()
brh = "".join(f'<div class="broll full" id="br{k}"><video id="v{k}" class="clip" src="assets/broll/{c["id"]}.mp4" data-start="{c["at"]}" '
              f'data-duration="{c["dur"]}" data-media-start="0" muted playsinline></video></div>' for k, c in enumerate(br))
src = src.replace("/*BROLL*/", brh).replace("/*DATA*/", json.dumps(data, ensure_ascii=False)).replace("/*DUR*/", str(dur))
open(os.path.join(hf, "index.html"), "w").write(src)
json.dump(t, sys.stdout, ensure_ascii=False); print()
print(len(G), "subtitle groups")
