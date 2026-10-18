#!/usr/bin/env python3
"""Reel 23, step 2: the person-aware effects from tools/fx, rendered on the trimmed base and spliced back in.

    python3 fx23.py WORK ORIG [name ...] [--preview]   # WORK/base.mp4 -> WORK/fx/*.mp4 -> WORK/base_fx.mp4

Times are on the trimmed axis (timeline.json); every effect sits inside one shot of one zoom.
  night    0.00-3.83   «вы легли спать, а ваш AI продолжает работать»: the room's light goes out (stars, moon),
                       a night clock on his chest runs 23:47 -> 03:12, «AI · работает» blinks under it
  zoom    24.23-27.04  «не автодополнением кода, а исполнителем»: punch in on the small role, punch out on the big one
                       (cut from the 4K original, not upscaled from the base)
  doodle1 27.63-31.20  «чем дольше агент работает сам, тем важнее контроль»: a hand-drawn outline traces him
  doodle2 31.20-34.50  «планы, тесты, ограничения, точки проверки»: the four controls are scribbled around him
  chart   21.10-24.23  «AI-разработка в 2026 году»: how long an agent works alone, minutes -> hours, on the wall
  screen  38.33-41.67  «правильно управлять AI»: he stands in front of a board of agents he runs
  phone   41.67-45.33  CTA: the Telegram post with guide #16 (held 1.2 s at the end)
"""
import json, math, os, subprocess, sys
import numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "fx"))
import fxlib
from fxlib import (Clip, Html, write_video, over, transform, person_mattes, head_track, person_over, prog, ease_out,
                   ease_out_back, lerp, FPS, W, H)
import importlib

zoom = importlib.import_module("effects.05_digital_zoom")
doodle = importlib.import_module("effects.14_doodle_boil")
chart = importlib.import_module("effects.10_chart_grow")
green = importlib.import_module("effects.12_green_screen")
phone = importlib.import_module("effects.06_phone_mockup")

HERE = os.path.dirname(os.path.abspath(__file__))
LAV, NIGHT = "#A99BFF", "#0B1030"          # reel 23: night indigo + lavender (22 was navy + emerald)
work, orig = sys.argv[1], sys.argv[2]
names = [a for a in sys.argv[3:] if not a.startswith("--")]
preview = "--preview" in sys.argv
os.makedirs(os.path.join(work, "fx"), exist_ok=True)
base = os.path.join(work, "base.mp4")
tline = json.load(open(os.path.join(HERE, "timeline.json")))


def _clip_init(self, path, t0, t1, size=(W, H)):
    """fxlib.Clip with a 4-decimal seek (3 decimals landed a frame off on reel 19)."""
    self.path, self.t0, self.t1, self.size = str(path), t0, t1, size
    w, h = size
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t0:.4f}", "-t", f"{t1 - t0:.4f}", "-i", self.path,
           "-vf", f"scale={w}:{h}:flags=lanczos,fps={FPS}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = len(raw) // (w * h * 3)
    self.u8 = np.frombuffer(raw, np.uint8)[: n * w * h * 3].reshape(n, h, w, 3)
    self.n = n


Clip.__init__ = _clip_init


def BClip(a, b):
    """Frames [a, b) of base.mp4: the seek sits a quarter frame before a, so frame a is the first one kept."""
    c = Clip(base, a - 0.008, b - 0.008)
    c.t0, c.t1 = a, b
    return c


# ---------------------------------------------------------------- night (new for this reel)
NIGHT_CSS = f"""
body{{width:1080px;height:1920px;overflow:hidden}}
#pan{{position:absolute;left:150px;right:150px;top:930px;height:420px;border-radius:44px;background:rgba(9,12,38,.62);
      border:2px solid rgba(169,155,255,.45);box-shadow:0 30px 80px rgba(0,0,0,.5)}}
#clk{{position:absolute;left:0;right:0;top:985px;text-align:center;font:900 220px/1 Unbounded;letter-spacing:-.04em;
      color:{LAV};text-shadow:0 0 50px rgba(169,155,255,.65),0 0 120px rgba(120,100,255,.35)}}
#clk i{{font-style:normal;display:inline-block;width:.42em}}
#st{{position:absolute;left:0;right:0;top:1235px;text-align:center}}
#st span{{display:inline-flex;align-items:center;gap:16px;padding:14px 30px;border-radius:40px;background:rgba(11,16,48,.75);
         border:2px solid rgba(169,155,255,.6);color:#fff;font:800 38px Manrope}}
#st b{{width:18px;height:18px;border-radius:50%;background:{LAV};box-shadow:0 0 18px {LAV}}}
.s{{position:absolute;border-radius:50%;background:#fff}}
#moon{{position:absolute;left:800px;top:250px;width:110px;height:110px;border-radius:50%;
       box-shadow:-26px 14px 0 0 #F4EFD8;filter:drop-shadow(0 0 22px rgba(244,239,216,.55))}}
"""
NIGHT_JS = """
const E=t=>1-Math.pow(1-Math.min(1,Math.max(0,t)),3);
const pad=n=>String(n).padStart(2,'0');
window.seek=t=>{
  const a=E((t-CFG.clock)/0.5); const c=document.getElementById('clk');
  c.style.opacity=a; c.style.transform=`translateY(${(1-a)*60}px) scale(${0.9+0.1*a})`;
  const pn=document.getElementById('pan'); if(pn){pn.style.opacity=a; pn.style.transform=`scale(${0.92+0.08*a})`;}
  const k=Math.min(1,Math.max(0,(t-CFG.clock)/(CFG.end-CFG.clock)));
  const m=CFG.m0+Math.round((CFG.m1-CFG.m0)*k*k*(3-2*k)); const hh=Math.floor(m/60)%24, mm=m%60;
  const blink=(Math.floor(t*2)%2)?'1':'.25';
  c.innerHTML=pad(hh)+`<i style="opacity:${blink}">:</i>`+pad(mm);
  const s=E((t-CFG.status)/0.4), st=document.getElementById('st');
  st.style.opacity=s; st.style.transform=`translateY(${(1-s)*30}px)`;
  st.querySelector('b').style.opacity=0.35+0.65*Math.abs(Math.sin(t*5));
  const n=E((t-CFG.off)/0.3);
  document.querySelectorAll('.s').forEach((e,j)=>{e.style.opacity=n*(0.35+0.65*Math.abs(Math.sin(t*2+j*1.7)));});
  const mo=document.getElementById('moon'); if(mo) mo.style.opacity=n;
};
"""


def night_frames(clip, html, t0, off, clock, status, end, m0, m1):
    rnd = np.random.default_rng(23)
    stars = "".join(f'<i class=s style="left:{int(rnd.uniform(40, 1040))}px;top:{int(rnd.uniform(210, 1000))}px;'
                    f'width:{(sz := rnd.choice([3, 4, 6]))}px;height:{sz}px"></i>' for _ in range(46))
    back = f'{stars}<div id=moon></div>'                    # behind him
    front = '<div id=pan></div><div id=clk></div><div id=st><span><b></b>AI · работает</span></div>'   # over his chest
    times = [t0 + i / FPS for i in range(len(clip))]
    cfg = json.dumps(dict(off=off, clock=clock, status=status, end=end, m0=m0, m1=m1))
    backs = list(html.frames(back + '<div id=clk style="display:none"></div><div id=st style="display:none"><b></b></div>', NIGHT_CSS,
                             f"const CFG={cfg};" + NIGHT_JS, times))
    layers = zip(backs, html.frames(front, NIGHT_CSS, f"const CFG={cfg};" + NIGHT_JS, times))
    mattes = person_mattes(clip)
    night = np.float32([0.19, 0.06, 0.03])          # BGR of a deep indigo
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    for i, (ui, fr) in enumerate(layers):
        t = times[i]
        f = clip.frame(i)
        k = ease_out(prog(t, off, off + 0.28), 2)    # the lights go off on «спать»
        if k <= 0:
            yield f
            continue
        # room: dark indigo, a little lighter at the top where the window light would be
        room = f * lerp(1, 0.22, k) + night * (0.55 + 0.25 * (1 - yy)) * k
        over(room, ui)
        # he stays readable: dimmed a bit, cool tint, a lavender rim from the clock above
        lit = f * lerp(1, 0.86, k)
        lit = lit * (1 - 0.12 * k) + np.float32([0.42, 0.24, 0.20]) * 0.12 * k
        m = mattes[i]
        edge = np.clip(cv2.GaussianBlur(m, (0, 0), 4) - cv2.erode(m, np.ones((9, 9), np.uint8)), 0, 1)
        top = (1 - yy[..., 0]) ** 2
        lit = lit + np.float32([1.0, 0.61, 0.66])[None, None] * (0.35 * k * edge * top)[..., None]
        out = np.clip(person_over(room, lit, m), 0, 1)
        over(out, fr)
        yield out


# ---------------------------------------------------------------- zoom from the 4K original
def zoom_clip(t_out0, t_out1):
    """The segment of ORIG under [t_out0, t_out1) of the trimmed axis, at 1620x2880 for a lossless punch-in."""
    for s in tline["segments"]:
        if s["out"][0] - 1e-3 <= t_out0 < s["out"][1]:
            a = s["src"][0] + t_out0 - s["out"][0]
            c = Clip(orig, a - 0.008, a + t_out1 - t_out0 - 0.008, size=(1620, 2880))
            c.t0, c.t1 = t_out0, t_out1
            return c
    raise SystemExit("no segment")


# ---------------------------------------------------------------- doodles: the four controls, in Russian
DCSS = ("body{display:flex;align-items:center;justify-content:center;height:100vh;font:700 120px Caveat;color:#fff;"
        "text-shadow:0 3px 0 rgba(11,16,48,.8),0 0 18px rgba(0,0,0,.7)}")
_doodle_frames = doodle.frames


def doodle_frames(clip, html, t0, **kw):
    LV = (1.0, 0.61, 0.66)            # BGR of LAV
    doodle.PINK = LV
    orig_still = html.still
    html.still = lambda body, css="", size=(W, H), scale=1: orig_still(body, DCSS, size=(560, 190), scale=scale)
    try:
        yield from _doodle_frames(clip, html, t0, **kw)
    finally:
        html.still = orig_still


# ---------------------------------------------------------------- chart: minutes -> hours on the wall
chart.CSS = chart.CSS.replace("#E9FF57", LAV).replace("#121212", NIGHT) + \
    ".ax{font:800 36px Manrope}#tag{font:800 40px Unbounded;padding:14px 26px}" \
    f"#mn{{position:absolute;left:100px;top:530px;font:800 30px Manrope;color:#C9C2FF}}" \
    f"#cap{{position:absolute;left:0;right:0;top:225px;text-align:center;font:800 50px/1.15 Manrope;color:#fff;" \
    f"text-shadow:0 3px 14px rgba(0,0,0,.7)}}#cap b{{color:{LAV}}}"
_chart_frames = chart.frames


def chart_frames(clip, html, t0, caption, **kw):
    orig_frames = html.frames

    def frames(body, css, js, times, size=(W, H), scale=1):
        body = (body.replace("#E9FF57", LAV).replace('stroke-width="7"', 'stroke-width="11"').replace('stroke-width="18"', 'stroke-width="28"')
                + f'<div id=cap>{caption}</div><div id=mn>минуты</div>')
        return orig_frames(body, css, js, times, size, scale)
    html.frames = frames
    try:
        yield from _chart_frames(clip, html, t0, **kw)
    finally:
        html.frames = orig_frames


# ---------------------------------------------------------------- green screen: the board of agents he runs
green.CSS = f"""
body{{width:1080px;height:1920px;background:radial-gradient(1200px 1300px at 50% 20%,#1B2150 0%,{NIGHT} 70%);font-family:Manrope;overflow:hidden}}
#app{{position:absolute;left:50px;right:50px;top:272px;border-radius:30px;background:#11163A;border:2px solid rgba(169,155,255,.35);
     box-shadow:0 30px 70px rgba(0,0,0,.45);overflow:hidden}}
.top{{display:flex;align-items:center;gap:14px;padding:16px 30px;background:#181E4C;color:#fff;font:800 32px Manrope}}
.top b{{margin-left:auto;padding:6px 16px;border-radius:20px;background:{LAV};color:{NIGHT};font:800 24px Unbounded}}
.it{{display:flex;gap:20px;align-items:center;padding:9px 30px;border-bottom:1px solid rgba(255,255,255,.07);opacity:0}}
.ic{{width:64px;height:64px;border-radius:18px;flex:none;display:flex;align-items:center;justify-content:center;font:800 24px Unbounded;color:{NIGHT};background:{LAV}}}
.tx{{flex:1;min-width:0}}.nm{{font:800 30px Manrope;color:#fff}}.q{{font:600 25px Manrope;color:#9DA3C7;white-space:nowrap}}
.bar{{height:10px;border-radius:5px;background:rgba(255,255,255,.1);margin-top:8px;overflow:hidden}}
.bar i{{display:block;height:100%;background:{LAV};border-radius:5px}}
.tg{{font:800 22px Unbounded;padding:8px 14px;border-radius:12px;white-space:nowrap}}
.ok{{background:#2BD576;color:#0B1030}} .run{{background:rgba(169,155,255,.18);color:{LAV}}} .you{{background:#FFC857;color:#0B1030}}
#cap{{position:absolute;left:0;right:0;top:196px;text-align:center;font:800 46px Unbounded;color:#fff;opacity:0}}
#cap span{{background:{LAV};color:{NIGHT};padding:0 14px;border-radius:12px}}
"""
AGENTS = [("01", "Агент · миграция базы", "шаг 7 из 9", 0.78, "run", "работает"),
          ("02", "Агент · тесты оплаты", "214 из 214 прошли", 1.0, "ok", "готово"),
          ("03", "Агент · новый экран", "ждёт вашего решения", 0.6, "you", "вам"),
          ("04", "Агент · ревью кода", "проверил 12 файлов", 0.92, "run", "работает")]
GREEN_JS = """
const E=t=>1-Math.pow(1-Math.min(1,Math.max(0,t)),3);
window.seek=t=>{
  document.querySelectorAll('.it').forEach((e,j)=>{const p=E((t-CFG.flood-j*CFG.every)/0.35);
    e.style.opacity=p; e.style.transform=`translateX(${(1-p)*-60}px)`;
    const b=e.querySelector('.bar i'); b.style.width=(100*CFG.v[j]*Math.min(1,0.8+0.2*E((t-CFG.flood)/2)))+'%';});
  const c=document.getElementById('cap'), k=E((t-CFG.cap)/0.3); c.style.opacity=k; c.style.transform=`scale(${0.85+0.15*k})`;
};
"""


def screen_frames(clip, html, t0, swap, flood, every, cap, caption, person_scale):
    rows = "".join(f'<div class=it><div class=ic>{n}</div><div class=tx><div class=nm>{nm}</div><div class=q>{q}</div>'
                   f'<div class=bar><i></i></div></div><div class="tg {c}">{tg}</div></div>' for n, nm, q, v, c, tg in AGENTS)
    body = f'<div id=app><div class=top>Мои AI-агенты <b>4 в работе</b></div>{rows}</div><div id=cap>{caption}</div>'
    cfg = json.dumps(dict(flood=flood, every=every, cap=cap, v=[a[3] for a in AGENTS]))
    orig_frames = html.frames
    html.frames = lambda b, css, js, times, size=(W, H), scale=1: orig_frames(body, green.CSS, f"const CFG={cfg};" + GREEN_JS,
                                                                                times, size, scale)
    try:
        yield from green.frames(clip, html, t0, swap=swap, flood=flood, every=every, cap=cap, questions=[], names=[],
                                colors=[], caption=caption, person_scale=person_scale)
    finally:
        html.frames = orig_frames


# ---------------------------------------------------------------- phone CTA
phone.CSS += f"""
.file{{display:flex;gap:14px;align-items:center;margin-top:12px;padding:12px;border-radius:14px;background:rgba(255,255,255,.06)}}
.file .ic{{width:54px;height:62px;border-radius:10px;background:{LAV};display:flex;align-items:center;justify-content:center;font:800 15px Unbounded;color:{NIGHT}}}
.file .fn{{font:700 18px Manrope;line-height:1.25}}
.file .fs{{font:500 15px Manrope;opacity:.55}}
"""
_track = phone.head_track
phone.head_track = lambda mattes: [tuple(np.median(np.array(_track(mattes)), axis=0))] * len(mattes)
_body = phone.body
phone.body = lambda chat, msgs: _body(chat, msgs).replace("бот · онлайн", "канал в Telegram")

LV_BGR = (1.0, 0.61, 0.66)
WHITE = (1.0, 1.0, 1.0)
JOBS = {
    "night": dict(gen=night_frames, t0=0.0, t1=3.8333, off=1.22, clock=1.70, status=2.13, end=3.80, m0=23 * 60 + 47,
                  m1=24 * 60 + 3 * 60 + 12),
    "chart": dict(gen=chart_frames, t0=21.10, t1=24.2333, grid=21.15, labels=["2023", "2024", "2025", "2026"],
                  values=[0.05, 0.14, 0.40, 1.0], times=[21.3, 21.75, 22.2, 22.75], tag=23.0, tag_text="часы ↗",
                  box=(150, 400, 930, 610), person_scale=0.80,
                  caption="Сколько агент работает<br><b>без человека</b>"),
    "zoom": dict(gen=zoom.frames, t0=24.2333, t1=27.0333, word_y=-999,
                 beats=[(24.2333, 1.1, ""), (25.20, 1.34, ""), (26.40, 1.0, "")]),
    "doodle1": dict(gen=doodle_frames, t0=27.6333, t1=31.20, trace=27.70,
                    doodles=[("spark", 28.75, (-1.2, 0.25), 60, WHITE), ("star", 29.10, (1.2, 0.1), 70, LV_BGR),
                             ("bolt", 29.86, (1.25, 1.1), 80, WHITE)],
                    words=[("контроль!", 30.66, (0.0, 2.3))]),
    "doodle2": dict(gen=doodle_frames, t0=31.20, t1=34.50, trace=31.21,
                    doodles=[("doc", 31.31, (-1.25, 0.35), 80, WHITE), ("star", 31.63, (1.2, 0.15), 70, LV_BGR),
                             ("spark", 32.07, (-1.2, 1.3), 56, LV_BGR), ("crown", 33.27, (-1.2, 1.3), 60, WHITE)],
                    words=[("план", 31.31, (-0.55, 2.1)), ("тесты", 31.63, (0.55, 2.1)),
                           ("лимиты", 32.07, (-0.55, 2.6)), ("проверка", 33.27, (0.55, 2.6))]),
    "screen": dict(gen=screen_frames, t0=38.3333, t1=41.6667, swap=38.40, flood=38.65, every=0.3, cap=39.91,
                   caption='вы <span>управляете</span> агентами', person_scale=0.7),
    "phone": dict(gen=phone.frames, t0=41.6667, t1=45.3333, enter=41.80, chat="Islam Dev AI",
                  msgs=[dict(t=42.35, html='<b>Гайд №16</b>Workflow с AI-агентом: от задачи вечером до готового PR утром.'),
                        dict(t=43.6, html='<div class=file style="margin:0"><div class=ic>PDF</div><div><div class=fn>'
                                          'От задачи<br>до готового PR.pdf</div><div class=fs>канал · закреп</div></div></div>')],
                  tap=99, tap_xy=(0, 0)),
}
HOLD = 1.2          # seconds the last CTA frame is held after he stops talking

for name in ([] if "--splice" in sys.argv else names or list(JOBS)):   # --splice: reuse rendered effects
    cfg = dict(JOBS[name])
    gen, t0, t1 = cfg.pop("gen"), cfg.pop("t0"), cfg.pop("t1")
    fxlib.MATTE_MODEL = cfg.pop("matte", "human")
    clip = zoom_clip(t0, t1) if name == "zoom" else BClip(t0, t1)
    out = os.path.join(work, "fx", f"{name}.mp4")
    with Html() as html:
        frames = gen(clip, html, t0=t0, **cfg)
        if preview:
            n = len(clip); idx = set(np.linspace(0, n - 1, 6).astype(int))
            shots = [cv2.resize(f, (360, 640)) for i, f in enumerate(frames) if i in idx]
            p = out.replace(".mp4", "-preview.jpg")
            cv2.imwrite(p, (np.clip(np.hstack(shots), 0, 1) * 255).astype(np.uint8))
            print(p, flush=True)
            continue
        write_video(frames, out, crf=12)
    print(name, out, len(clip), "frames", flush=True)

if preview or names:
    sys.exit()

# splice: the effect clips replace the same frames of the base, then the last frame is held
spans = sorted((JOBS[n]["t0"], JOBS[n]["t1"], os.path.join(work, "fx", f"{n}.mp4")) for n in JOBS)
parts, t = [], 0.0
for a, b, f in spans:
    if a - t > 1e-3:
        parts.append(("base", t, a))
    parts.append((f, a, b))
    t = b
dur = tline["duration"]
if dur - t > 1e-3:
    parts.append(("base", t, None))
lines = []
for k, (f, a, b) in enumerate(parts):
    if f == "base":
        p = os.path.join(work, "fx", f"base{k:02d}.mp4")
        n = ["-frames:v", str(round((b - a) * FPS))] if b else []
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", base, "-vf", f"select=gte(n\\,{round(a * FPS)}),setpts=N/{FPS}/TB",
                        *n, "-an", "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", "-r", str(FPS), p],
                       check=True)
        f = p
    else:   # Clip can decode one frame more than the span: cut every effect to its exact frame count
        p = f.replace(".mp4", "-exact.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-frames:v", str(round(b * FPS) - round(a * FPS)), "-an", "-c:v", "libx264",
                        "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", "-r", str(FPS), p], check=True)
        f = p
    lines.append(f"file '{f}'\n")
lst = os.path.join(work, "fx", "parts.txt")
open(lst, "w").write("".join(lines))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-an",
                "-vf", f"tpad=stop_mode=clone:stop_duration={HOLD}", "-c:v", "libx264", "-crf", "13",
                "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p", "-r", str(FPS), os.path.join(work, "base_fx.mp4")], check=True)
print("base_fx.mp4 ready")
