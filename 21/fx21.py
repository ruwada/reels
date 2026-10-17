#!/usr/bin/env python3
"""Reel 21, step 2: the person-aware effects from tools/fx, rendered on the trimmed base and spliced back in.

    python3 fx21.py WORK          # WORK/base.mp4 -> WORK/fx/*.mp4 -> WORK/base_fx.mp4

Times are on the trimmed axis (timeline.json). Every effect sits inside shots of one zoom, so the
person matte never meets a framing jump.
  checklist  0.00-7.13   «подключил всё»: agent, model, CRM tick in; «продажи» gets a red cross
  glass      9.70-13.50  giant glass word СЦЕНАРИЙ on the wall behind his head
  phone      14.93-16.87 a client's «Сколько стоит?» lands in a phone beside him
  phone_cta  58.83-63.73 the Telegram channel post with guide #4
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "fx"))
import fxlib
from fxlib import Clip, Html, write_video, frost, over, FPS
import importlib

check = importlib.import_module("effects.07_checklist")
glass = importlib.import_module("effects.17_glass_type")
phone = importlib.import_module("effects.06_phone_mockup")

PINK = "#FF3D8B"
work = sys.argv[1]
os.makedirs(os.path.join(work, "fx"), exist_ok=True)
base = os.path.join(work, "base.mp4")

# checklist: magenta ticks, the last row is the punchline (red cross, struck through)
check.CSS = check.CSS.replace("#C8F25A", PINK).replace("top:1060px", "top:930px").replace(
    "rgba(20,22,27,.78)", "rgba(18,12,20,.80)") + """
.row.bad .tx{color:#FF5A5A;text-decoration:line-through;text-decoration-thickness:4px}
.bx.x{background:#FF3B3B;border-color:#FF3B3B}
"""
check.JS = check.JS.replace("const on=t>=tc; bx.className='bx'+(on?' on':''); if(on) done++;",
                            "const on=t>=tc; const bad=it[3]; bx.className='bx'+(on?(bad?' x':' on'):''); "
                            "document.getElementById('r'+j).className='row'+(on&&bad?' bad':''); if(on&&!bad) done++;")
check.JS = check.JS.replace("CFG.items.length;\n  document.getElementById('bar')", "(CFG.items.length-1);\n  document.getElementById('bar')")
check.JS = check.JS.replace("(100*done/CFG.items.length)", "(100*done/(CFG.items.length-1))")


def check_frames(clip, html, t0, enter, title, items):
    rows = ""
    for j, it in enumerate(items):
        mark = ('<path id=c{j} d="M8 8 L22 22 M22 8 L8 22" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" '
                'stroke-dasharray="40" stroke-dashoffset="40"/>' if it[3] else
                '<path id=c{j} d="M6 15 L13 22 L25 8" fill="none" stroke="#14161B" stroke-width="4" stroke-linecap="round" '
                'stroke-dasharray="40" stroke-dashoffset="40"/>').format(j=j)
        rows += (f'<div class=row id=r{j}><div class=bx id=b{j}><svg viewBox="0 0 30 30">{mark}</svg></div>'
                 f'<span class=tx id=t{j}></span><div class=ln id=l{j} style="width:{300 + 60 * (j % 3)}px"></div></div>')
    body = f'<div id=p><div class=hd><span>● {title}</span><b id=n></b></div>{rows}<div class=bar><i id=bar></i></div></div>'
    cfg = json.dumps(dict(enter=enter, items=items), ensure_ascii=False)
    times = [t0 + i / FPS for i in range(len(clip))]
    for i, ui in enumerate(html.frames(body, check.CSS, f"const CFG={cfg};" + check.JS, times)):
        out = frost(clip.frame(i), ui[..., 3])
        over(out, ui)
        yield out


phone.CSS = phone.CSS.replace("#2AABEE", "#2AABEE") + """
.cl{margin:14px 16px 14px 90px;padding:16px 18px;border-radius:20px 20px 6px 20px;background:#2B5278;opacity:0;font:700 26px Manrope}
.cl small{display:block;font:500 15px Manrope;opacity:.6;text-align:right;margin-top:4px}
.ty{margin:6px 16px;display:inline-flex;gap:7px;padding:16px 20px;border-radius:20px;background:#22252C;opacity:0}
.ty i{width:11px;height:11px;border-radius:50%;background:#9aa3b2}
.file{display:flex;gap:14px;align-items:center;margin-top:12px;padding:12px;border-radius:14px;background:rgba(255,255,255,.06)}
.file .ic{width:54px;height:62px;border-radius:10px;background:""" + PINK + """;display:flex;align-items:center;justify-content:center;font:800 15px Unbounded;color:#fff}
.file .fn{font:700 18px Manrope;line-height:1.25}
.file .fs{font:500 15px Manrope;opacity:.55}
"""

# the phone stays put beside his head: a per-frame head track made it jump when he leaned
import numpy as np
_track = phone.head_track
phone.head_track = lambda mattes: [tuple(np.median(np.array(_track(mattes)), axis=0))] * len(mattes)
_body = phone.body
SUBTITLE = {"Клиент": "Instagram · сейчас", "Islam Dev AI": "канал в Telegram"}
phone.body = lambda chat, msgs: _body(chat, msgs).replace("бот · онлайн", SUBTITLE.get(chat, "онлайн"))

JOBS = {
    "checklist": dict(mod=check, frames=check_frames, t0=0.0, t1=7.1333, enter=0.12, title="ПОДКЛЮЧИЛ ВСЁ",
                      items=[("Умный AI-агент", 0.95, 1.6, False), ("Лучшая модель", 3.0, 3.6, False),
                             ("Доступ к CRM", 4.25, 4.8, False), ("Продажи: 0", 5.75, 6.5, True)]),
    "glass": dict(mod=glass, t0=9.70, t1=13.50, word="СЦЕНАРИЙ", appear=10.18, cy=250, size=160, depth=16),
    "phone": dict(mod=phone, t0=14.9333, t1=16.8667, enter=14.98, chat="Клиент",
                  msgs=[dict(t=15.30, html='<span style="opacity:.6;font-size:18px">Новый лид · Instagram</span>'),
                        dict(t=15.86, html='<b style="font-size:30px;margin:0">Сколько стоит?</b>'),
                        dict(t=16.45, html='<span style="opacity:.75">AI-агент печатает…</span>')],
                  tap=99, tap_xy=(0, 0)),
    "phone_cta": dict(mod=phone, t0=58.8333, t1=63.7333, enter=58.88, chat="Islam Dev AI",
                      msgs=[dict(t=59.30, html='<b>Гайд №4</b>Структура сценария AI-агента: этапы воронки, вопросы, '
                                               'ответы на «дорого».'),
                            dict(t=59.95, html='<div class=file style="margin:0"><div class=ic>PDF</div><div><div class=fn>'
                                               'Структура сценария<br>AI-агента.pdf</div><div class=fs>канал · закреп</div></div></div>'),
                            dict(t=61.4, html='<span class=ok>✓ Скачано</span><br>Начните с этапа 1: что спрашивает клиент.')],
                      tap=61.15, tap_xy=(200, 470)),
}

only = sys.argv[2:] or list(JOBS)
for name in only:
    cfg = dict(JOBS[name])
    mod, fr = cfg.pop("mod"), cfg.pop("frames", None)
    t0, t1 = cfg.pop("t0"), cfg.pop("t1")
    clip = Clip(base, t0, t1, size=(fxlib.W, fxlib.H))
    out = os.path.join(work, "fx", f"{name}.mp4")
    with Html() as html:
        gen = (fr or mod.frames)(clip, html, t0=t0, **cfg)
        write_video(gen, out, crf=12)
    print(name, out, len(clip), "frames", flush=True)

# splice: the effect clips replace the same frames of the base
spans = [(JOBS[n]["t0"], JOBS[n]["t1"], os.path.join(work, "fx", f"{n}.mp4")) for n in JOBS
         if os.path.exists(os.path.join(work, "fx", f"{n}.mp4"))]
spans.sort()
parts, t = [], 0.0
for k, (a, b, f) in enumerate(spans):
    if a - t > 1e-3:
        parts.append(("base", t, a))
    parts.append((f, None, None))
    t = b
parts.append(("base", t, None))
lst = os.path.join(work, "fx", "parts.txt")
lines = []
for k, (f, a, b) in enumerate(parts):
    if f == "base":
        p = os.path.join(work, "fx", f"base{k:02d}.mp4")
        n = ["-frames:v", str(round((b - a) * FPS))] if b else []
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", base, "-vf", f"select=gte(n\\,{round(a * FPS)}),setpts=N/{FPS}/TB",
                        *n, "-an", "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", "-r", str(FPS), p],
                       check=True)
        f = p
    lines.append(f"file '{f}'\n")
open(lst, "w").write("".join(lines))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-an", "-c:v", "libx264", "-crf", "13",
                "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p", "-r", str(FPS), os.path.join(work, "base_fx.mp4")], check=True)
print("base_fx.mp4 ready")
