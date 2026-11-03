#!/usr/bin/env python3
"""Reel 22, step 1: tighten pauses and cut the talking head into jump-cut segments.

    python3 cut.py ORIG.mov WORKDIR

Reads ../words.json (word timings of the original), keeps every word, shortens pauses longer than
GAP_MAX down to PAD_AFTER + PAD_BEFORE, and changes the zoom on every sentence so the trims read as
jump cuts. Writes WORKDIR/base.mp4 (1080x1920, 30 fps, GOP 30, no audio), WORKDIR/voice.wav and
timeline.json next to this script (segments + words on the new time axis).
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP_MAX, PAD_AFTER, PAD_BEFORE = 0.40, 0.20, 0.12
W, H = 2160, 3840          # source size
FACE_Y = 0.31              # face centre, share of frame height
# zoom per sentence (index in the sentence list printed by this script); default alternates 1.0 / 1.13
ZOOM = {0: 1.0, 1: 1.0, 2: 1.12, 3: 1.0, 4: 1.08, 5: 1.0, 6: 1.12, 7: 1.12, 8: 1.18, 9: 1.0, 10: 1.1, 11: 1.0}

words = json.load(open(os.path.join(HERE, "words.json")))
orig, work = sys.argv[1], sys.argv[2]
os.makedirs(work, exist_ok=True)

# sentence boundaries: punctuation or a pause
sent, cur = [], []
for i, w in enumerate(words):
    cur.append(i)
    nxt = words[i + 1]["s"] if i + 1 < len(words) else None
    if w["w"][-1] in ".?:!" or (nxt is not None and nxt - w["e"] > 0.45):
        sent.append(cur); cur = []
if cur:
    sent.append(cur)

# kept source intervals: one per sentence, split further where a long pause sits inside it
segs = []
for k, idx in enumerate(sent):
    z = ZOOM.get(k, 1.0 if k % 2 == 0 else 1.13)
    a = max(0.0, words[idx[0]]["s"] - PAD_BEFORE)
    for j in range(len(idx)):
        w = words[idx[j]]
        last = j == len(idx) - 1
        nxt = words[idx[j] + 1]["s"] if idx[j] + 1 < len(words) else None
        if last or (nxt - w["e"] > GAP_MAX):
            if nxt is None:
                b = w["e"] + 0.45
            elif nxt - w["e"] > GAP_MAX:
                b = w["e"] + PAD_AFTER
            else:
                b = (w["e"] + nxt) / 2
            segs.append({"src": [round(a, 3), round(b, 3)], "zoom": z, "sent": k})
            if not last:
                a = nxt - PAD_BEFORE
    # next sentence starts where this one ended unless a pause was trimmed
    if k + 1 < len(sent):
        nxt = words[sent[k + 1][0]]["s"]
        if nxt - words[idx[-1]]["e"] <= GAP_MAX:
            segs[-1]["src"][1] = round((words[idx[-1]]["e"] + nxt) / 2, 3)

# snap to frames and lay out on the new axis; never let two kept intervals overlap
# (an overlap plays the same syllable twice at the join: the "stutter" the user heard in reel 20)
fps = 30
SRC_END = int(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    orig], capture_output=True, text=True).stdout) * fps - 1) / fps
t = 0.0
prev_b = 0.0
for s in segs:
    a, b = (round(x * fps) / fps for x in s["src"])
    a, b = max(a, prev_b), min(b, SRC_END)
    prev_b = b
    s["src"] = [a, b]
    s["out"] = [round(t, 4), round(t + b - a, 4)]
    t += b - a
dur = t


def remap(x):
    for s in segs:
        if s["src"][0] - 1e-6 <= x <= s["src"][1] + 1e-6:
            return round(s["out"][0] + x - s["src"][0], 3)
    best = min(segs, key=lambda s: min(abs(x - s["src"][0]), abs(x - s["src"][1])))
    return round(best["out"][0] if x < best["src"][0] else best["out"][1], 3)


new_words = [{"w": w["w"], "s": remap(w["s"]), "e": remap(w["e"])} for w in words]
for k, idx in enumerate(sent):
    print(k, f'{new_words[idx[0]]["s"]:6.2f}', " ".join(words[i]["w"] for i in idx))
print(f"segments {len(segs)}, {words[-1]['e']:.2f}s -> {dur:.2f}s")
json.dump({"duration": round(dur, 3), "segments": segs, "words": new_words,
           "sentences": [[i[0], i[-1]] for i in sent]},
          open(os.path.join(HERE, "timeline.json"), "w"), ensure_ascii=False, indent=1)

if "--plan" in sys.argv:
    sys.exit()

parts = []
for n, s in enumerate(segs):
    a, b = s["src"]
    z = s["zoom"]
    cw, ch = round(W / z / 2) * 2, round(H / z / 2) * 2
    cx, cy = (W - cw) // 2, round((H - ch) * FACE_Y)
    p = os.path.join(work, f"seg{n:02d}.mp4")
    vf = f"crop={cw}:{ch}:{cx}:{cy},scale=1080:1920:flags=lanczos,eq=contrast=1.05:saturation=1.06,setsar=1,fps={fps}"
    nfr = round((b - a) * fps)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.4f}", "-i", orig, "-frames:v", str(nfr),
                    "-vf", vf, "-an", "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", p], check=True)
    parts.append(p)
lst = os.path.join(work, "segs.txt")
open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-crf", "14",
                "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p", "-r", str(fps), os.path.join(work, "base.mp4")], check=True)

# voice: same intervals, 10 ms fades at every join
fc, labels = [], []
for n, s in enumerate(segs):
    a, b = s["src"]
    fc.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b - a - 0.01:.4f}:d=0.01[a{n}]")
    labels.append(f"[a{n}]")
fc.append("".join(labels) + f"concat=n={len(segs)}:v=0:a=1[out]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", orig, "-filter_complex", ";".join(fc), "-map", "[out]",
                "-ar", "48000", "-ac", "1", os.path.join(work, "voice.wav")], check=True)
print("base.mp4 + voice.wav ready")
