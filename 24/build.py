#!/usr/bin/env python3
"""Reel 24, step 3: build the HyperFrames page (lead notification, Telegram chat scene with PiP, confirmation
request, B-roll, chat-bubble subtitles, CTA) over WORK/base_fx.mp4.

    python3 build.py HF_DIR       # writes HF_DIR/index.html; HF_DIR/assets needs base.mp4 (= base_fx), broll/, fonts, gsap

Every cue is looked up by word in timeline.json, so the page follows the trimmed take.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOLD = 1.2                       # fx24.py holds the last frame this long
hf = sys.argv[1]
tline = json.load(open(os.path.join(HERE, "timeline.json")))
words, dur = tline["words"], round(tline["duration"] + HOLD, 3)
seg = [s["out"] for s in tline["segments"]]


def clean(w):
    return re.sub(r"[^\w\-]", "", w.lower())


def cue(key, lo, hi, end=False):
    for w in words:
        if lo <= w["s"] <= hi and clean(w["w"]).startswith(clean(key)):
            return round(w["e"] if end else w["s"], 3)
    raise SystemExit(f"cue {key!r} not found in {lo}-{hi}")


br = json.load(open(os.path.join(HERE, "broll.json")))
t = {
    # «… приходят сообщения в Telegram: новый лид» -> a notification drops in over the phone B-roll
    "notif": [cue("telegram", 9.8, 10.3) - 0.1, seg[5][0] + 0.15],
    # «Он открывает карточку … записываются в CRM»: the whole flow inside a Telegram chat, he goes into a PiP
    "chat": [seg[5][0], seg[5][1]],
    "chatCues": {"card": cue("открывает", 11.2, 11.6), "hist": cue("историю", 12.4, 13), "btn": cue("нажимает", 13.4, 13.7),
                 "tap": cue("кнопку", 14, 14.3), "ai": cue("ai", 14.4, 14.8), "sugg": cue("предлагает", 15.9, 16.3),
                 "ok": cue("подтверждает", 17.4, 17.8), "crm": cue("записываются", 19.2, 19.5)},
    # «А если AI хочет выполнить опасное действие, он отправляет вам запрос на подтверждение»
    "alert": [cue("опасное", 26.4, 26.8) - 0.15, cue("запрос", 28, 28.4), cue("подтверждение", 28.5, 28.8, end=True), seg[9][1]],
    "complex": [br[2]["at"] + 0.15, br[2]["at"] + br[2]["dur"]],
    "cta": cue("telegram", 39.8, 40.2) - 0.05,
}
txt = json.load(open(os.path.join(HERE, "ru.json")))

# subtitle groups: up to 3 words / 16 chars, a group ends on punctuation or a pause
groups, cur = [], []


def disp(w):
    return re.sub(r"[.,:;«»]+$", "", w).lstrip("«")


for i, w in enumerate(words):
    d = disp(w["w"])
    if cur:
        prev = words[i - 1]
        chars = sum(len(x["w"]) for x in cur) + len(cur) + len(d)
        if prev["w"][-1] in ".?!:,»" or chars > 16 or len(cur) >= 3 or w["s"] - prev["e"] > 0.45:
            groups.append(cur); cur = []
    cur.append({"w": d, "s": round(w["s"], 3), "e": round(w["e"], 3)})
groups.append(cur)
G = []
for k, g in enumerate(groups):
    end = max(g[-1]["e"] + 0.3, g[-1]["s"] + 0.2)
    if k + 1 < len(groups):
        end = min(end, groups[k + 1][0]["s"] - 0.07)
    else:
        end = dur
    s0 = g[0]["s"] - 0.05
    G.append({"s": round(s0, 3), "e": round(end, 3), "words": g, "low": t["chat"][0] <= s0 < t["chat"][1] - 0.3})

data = {"dur": dur, "t": t, "text": txt, "groups": G, "broll": br}
src = open(os.path.join(HERE, "index.src.html")).read()
brh = "".join(f'<div class="broll full" id="br{k}"><video id="v{k}" class="clip" src="assets/broll/{c["id"]}.mp4" data-start="{c["at"]}" '
              f'data-duration="{c["dur"]}" data-media-start="0" muted playsinline></video></div>' for k, c in enumerate(br))
src = src.replace("/*BROLL*/", brh).replace("/*DATA*/", json.dumps(data, ensure_ascii=False)).replace("/*DUR*/", str(dur))
open(os.path.join(hf, "index.html"), "w").write(src)
json.dump(t, sys.stdout, ensure_ascii=False); print()
print(len(G), "subtitle groups")
