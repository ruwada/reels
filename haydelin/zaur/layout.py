#!/usr/bin/env python3
"""Lay the re-voiced app phrases back to back at natural pace and fit the phone screens to them.

Reads work/zaur/tts2/pNN.wav (tts_app.py output, silence trimmed), writes:
  work/zaur/app-tts.wav    the narration, starting at APP0 on the reel timeline
  zaur/timeline.json       app end + positions build.py / sfx.py need
  zaur/edit.json, en.json  screens, English lines, CTA moved to the new timing
"""
import json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, "..", "work", "zaur")
APP0 = 22.9          # the app part starts here (after "Вот что получилось")
LEAD, GAP = 0.15, 0.22
EN = ["An alarm rings morning and evening.", "Tap Start, and a character copies your face.",
      "Open your mouth, it opens too.", "A timer guides you through 6 zones.", "Two minutes, no zone missed.",
      "Braces or elastics?", "Special modes remind you to brush and wear them.", "Kids earn coins and buy rewards.",
      "Brushing becomes a game.", "Parents see on their phone if the child brushed.", "Missed it? A notification comes.",
      "Even if the phone is off."]
# screen -> first phrase it covers (screens follow each other, each runs until the next one)
SCREENS = [("../work/p_alarm.mp4", 0, 0), ("../work/p_start.mp4", 1, 0), ("../work/p_timer.mp4", 3, 0),
           ("../work/zaur/brekety.mp4", 5, 0), ("../work/p_modes.mp4", 6, 0), ("../work/p_coins.mp4", 7, 0),
           ("../broll/7171041.mp4", 9, 2.0), ("../work/p_parent.mp4", None, 0)]


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True, check=True).stdout)


def main():
    files = [f"{W}/tts2/p{i:02d}.wav" for i in range(len(EN))]
    starts, t = [], APP0 + LEAD
    for f in files:
        starts.append(round(t, 3)); t += dur(f) + GAP
    app_end = round(round((t - GAP + 0.35) * 30) / 30, 3)  # on the frame grid, so build.py cuts match

    args, fc = ["ffmpeg", "-v", "error", "-y"], []
    for i, f in enumerate(files):
        args += ["-i", f]; fc.append(f"[{i}:a]aresample=48000,adelay={round((starts[i] - APP0) * 1000)}:all=1[a{i}]")
    fc.append("".join(f"[a{i}]" for i in range(len(files))) +
              f"amix=inputs={len(files)}:normalize=0,apad,atrim=0:{app_end - APP0:.3f}[a]")
    subprocess.run(args + ["-filter_complex", ";".join(fc), "-map", "[a]", "-ac", "1", f"{W}/app-tts.wav"], check=True)

    # screens: each starts 0.1 s before its first phrase, the broll covers the first 1.9 s of phrase 9
    cut = []
    for f, ph, fr in SCREENS:
        if ph is None:
            cut.append(round(starts[9] - 0.1 + 1.9, 2))
        else:
            cut.append(APP0 if ph == 0 else round(starts[ph] - 0.1, 2))
    cut.append(app_end)
    cut = [round(round(c * 30) / 30, 3) for c in cut]  # on the frame grid
    plan = json.load(open(f"{HERE}/edit.json"))
    keep = [c for c in plan["cards"] if c["start"] < APP0]  # the contract list before the app part
    for k, (f, ph, fr) in enumerate(SCREENS):
        keep.append({"start": cut[k], "end": cut[k + 1], "kind": "clip", "file": f, "from": fr,
                     "transition": "cut", "grade": False})
    plan["cards"] = keep
    cta = app_end + 4.0
    plan["cta"]["start"] = round(cta + 0.05, 2)
    plan["out"] = "../work/zaur/reel-zaur-v6.mp4"
    json.dump(plan, open(f"{HERE}/edit.json", "w"), ensure_ascii=False, indent=1)

    en = [x for x in json.load(open(f"{HERE}/en.json")) if x["e"] <= APP0]
    for i, s in enumerate(starts):
        en.append({"s": s, "e": round(s + dur(files[i]) + 0.1, 2), "t": EN[i]})
    en += [{"s": round(app_end + 2.05, 2), "e": round(app_end + 3.5, 2), "t": "That's exactly what I wanted."},
           {"s": round(cta + 0.35, 2), "e": round(cta + 2.05, 2), "t": "Need an app for your business?"},
           {"s": round(cta + 2.05, 2), "e": round(cta + 4.55, 2), "t": "Comment “APP” and let's talk."}]
    json.dump(en, open(f"{HERE}/en.json", "w"), ensure_ascii=False, indent=0)
    json.dump({"app0": APP0, "app_end": app_end, "cta": cta, "phrases": starts}, open(f"{HERE}/timeline.json", "w"), indent=1)
    print("app", APP0, "->", app_end, "cta", cta, "total", round(cta + 4.8, 2))


if __name__ == "__main__":
    main()
