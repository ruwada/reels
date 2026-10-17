#!/usr/bin/env python3
"""Reel 20 v2: render the tools/fx effect segments on the trimmed timeline and splice them into base.mp4.

    python3 fxsegs.py ORIG.mp4 WORK [only] [--preview]

Effects (times on the trimmed axis, timeline.json):
  glass   17 glass type   0.00-2.47   «CRM» in thick glass on the wall behind him (hook)
  zoom    05 digital zoom 9.43-12.50  punch-ins on «забирают» / «AI-агенты», cropped from the 4K original
  check   07 checklist    12.50-23.13 what the agent does by itself, ticked on each spoken step
  wall    08 headline wall 32.60-35.60 «какую CRM купить?» notes slap onto the wall behind him
Writes WORK/fx/<name>.mp4 and WORK/base_fx.mp4 (base.mp4 with the segments replaced).
"""
import json, os, subprocess, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools/fx"))
import importlib, numpy as np, cv2
import fxlib
from fxlib import Clip, Html, write_video, FPS

orig, work = sys.argv[1], sys.argv[2]
only = [a for a in sys.argv[3:] if not a.startswith("--")]
preview = "--preview" in sys.argv
T = json.load(open(HERE / "timeline.json"))
segs = T["segments"]
base = os.path.join(work, "base.mp4")
os.makedirs(os.path.join(work, "fx"), exist_ok=True)
ORANGE = "#FF7A2F"


def word(w, lo=0, hi=99):
    for x in T["words"]:
        if lo <= x["s"] <= hi and x["w"].lower().startswith(w.lower()):
            return x["s"]
    raise SystemExit(f"no word {w}")


def mod(n):
    return importlib.import_module(f"effects.{n}")


def src_of(t):
    s = next(s for s in segs if s["out"][0] - 1e-3 <= t <= s["out"][1] + 1e-3)
    return s["src"][0] + t - s["out"][0]


class Recolor:
    """Html wrapper that swaps colours in the effect's own CSS (the templates hard-code their accent)."""
    def __init__(self, html, swap):
        self.h, self.swap = html, swap

    def _c(self, css):
        for a, b in self.swap.items():
            css = css.replace(a, b)
        return css

    def still(self, body, css="", *a, **k):
        return self.h.still(body, self._c(css), *a, **k)

    def frames(self, body, css, *a, **k):
        return self.h.frames(body, self._c(css), *a, **k)


def run(name, m, clip, cfg, swap=None):
    with Html() as html:
        gen = m.frames(clip, Recolor(html, swap or {}), **cfg)
        out = os.path.join(work, "fx", f"{name}.mp4")
        if preview:
            idx = set(np.linspace(0, len(clip) - 1, 6).astype(int))
            shots = [cv2.resize(f, (360, 640)) for i, f in enumerate(gen) if i in idx]
            p = out.replace(".mp4", "-preview.jpg")
            cv2.imwrite(p, (np.clip(np.hstack(shots), 0, 1) * 255).astype(np.uint8))
            print(p); return
        write_video(gen, out, crf=12)
        print(out)


JOBS = {}

# 17 glass type: the hook word stands behind his head
JOBS["glass"] = (0.0, segs[0]["out"][1])
def glass():
    a, b = JOBS["glass"]
    run("glass", mod("17_glass_type"), Clip(base, a, b), dict(t0=a, word="CRM", appear=0.05, cy=390, size=360, depth=22))

# 05 digital zoom from the 4K original (segment 2 is one continuous source span at zoom 1.0)
JOBS["zoom"] = tuple(segs[2]["out"])
def zoom():
    a, b = JOBS["zoom"]
    sa = segs[2]["src"][0]; sb = segs[2]["src"][1]
    off = sa - a
    m = mod("05_digital_zoom")
    beats = [(sa, 1.0, ""), (word("забирают", 9, 13) + off, 1.22, ""), (word("AI-агенты", 9, 13) + off, 1.5, "AI-агенты")]
    clip = Clip(orig, sa, sb, size=(1620, 2880))
    run("zoom", m, clip, dict(t0=sa, beats=beats, word_y=1250), swap={"#FFD84D": ORANGE})

# 07 checklist: the agent's steps, typed on the spoken word, ticked at the end of the phrase
JOBS["check"] = (segs[3]["out"][0], segs[5]["out"][1])
def check():
    a, b = JOBS["check"]
    m = mod("07_checklist")
    m.CSS = (m.CSS.replace("#C8F25A", ORANGE).replace("top:1060px", "top:1000px")
             .replace("rgba(20,22,27,.78)", "rgba(24,16,12,.80)"))
    steps = [("Получает новый лид", "получает", "лид"), ("Понимает, кто перед ним", "понимает", "ним"),
             ("Смотрит историю общения", "смотрит", "общения"), ("Определяет этап сделки", "определяет", "клиент"),
             ("Формирует ответ", "формирует", "ответ"), ("Обновляет данные в CRM", "меняет", "CRM"),
             ("Ставит задачу менеджеру", "ставит", "менеджеру")]
    items = []
    for txt, s, e in steps:
        ts = word(s, 12.4, 23.2)
        te = next(x["e"] for x in T["words"] if x["s"] >= ts and x["w"].lower().startswith(e.lower()))
        items.append((txt, round(ts - 0.05, 3), round(te, 3)))
    run("check", m, Clip(base, a, b), dict(t0=a, enter=a + 0.02, title="AI-АГЕНТ ДЕЛАЕТ САМ", items=items))

# 08 headline wall: everybody still asks which CRM to buy
JOBS["wall"] = tuple(segs[9]["out"])
def wall():
    a, b = JOBS["wall"]
    m = mod("08_headline_wall")
    # close-up: notes go to the free wall on both sides of his head, never behind it (the matte edge of the
    # head over a card reads as a halo), and he keeps his size (shrinking left the shoulders in the plate)
    m.STYLES = [x.replace("width:330px", "width:250px").replace("width:360px", "width:260px").replace("width:320px", "width:250px")
                .replace("44px", "36px").replace("38px", "32px").replace("30px", "26px") for x in m.STYLES]
    heads = ["Какую CRM купить?", "amoCRM или Битрикс24?", "Тариф на 10 менеджеров", "Сравнение CRM 2026"]
    run("wall", m, Clip(base, a, b), dict(t0=a, start=word("вопрос", 32, 34) - 0.05, every=0.32, headlines=heads, person_scale=1.0,
                                            spots=[(170, 360), (900, 330), (175, 690), (895, 660)]),
        swap={"#FFE34D": "#FFB27A"})


names = only or list(JOBS)  # «wall --splice»: re-render one effect, then splice all
for n in names:
    globals()[n]()
if preview or (only and "--splice" not in sys.argv):
    sys.exit()

# splice: base with every effect span replaced (frame-exact, same 30 fps grid)
spans = sorted((round(JOBS[n][0] * FPS), round(JOBS[n][1] * FPS), n) for n in JOBS)
dur_f = round(T["duration"] * FPS)
parts, cur = [], 0
inputs = ["-i", base]
for k, (fa, fb, n) in enumerate(spans):
    if fa > cur:
        parts.append(f"[0:v]trim=start_frame={cur}:end_frame={fa},setpts=PTS-STARTPTS[p{len(parts)}]")
    inputs += ["-i", os.path.join(work, "fx", f"{n}.mp4")]
    eq = ",eq=contrast=1.05:saturation=1.06" if n == "zoom" else ""   # cut.py grade; zoom came from the raw original
    parts.append(f"[{k + 1}:v]trim=end_frame={fb - fa},setpts=PTS-STARTPTS{eq},fps={FPS}[p{len(parts)}]")
    cur = fb
if cur < dur_f:
    parts.append(f"[0:v]trim=start_frame={cur},setpts=PTS-STARTPTS[p{len(parts)}]")
fc = ";".join(parts) + ";" + "".join(f"[p{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[v]"
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-crf", "12",
                "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p", "-r", str(FPS), os.path.join(work, "base_fx.mp4")], check=True)
print("base_fx.mp4 ready")
