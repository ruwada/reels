#!/usr/bin/env python3
"""Reel 19 v4, step 2: tools/fx effects rendered on the trimmed base (timeline.json axis) and spliced back in.

    python3 fx19.py ORIG.mov WORK [name ...] [--preview] [--splice]

  cover   16 cover story   0.00-3.43   magazine cover «СЕНЬОРЫ» rises behind his head (hook)
  glass   17 glass type    7.40-10.07  «ЧЕЛОВЕК» in thick glass on the wall behind him
  zoom    05 digital zoom  10.07-12.03 punch-ins on «разработку» / «быстрее», cropped from the 4K original
  check   07 checklist     15.77-25.77 what AI can do, ticked on each word; «подходит ли проекту?» gets a red cross
  wall    08 headline wall 31.70-39.07 the engineer's four questions slap onto the wall beside his head
  orbit   01 orbit         45.90-50.20 AI tool chips circle him («не пытался изучить каждый»)
  vertigo 15 vertigo       57.13-60.83 dolly zoom on «куда именно эту скорость направлять»
  phone   06 phone mockup  60.83-end   the Telegram post with guide №11

Every effect sits inside shots of one zoom; mattes are computed shot by shot, so the temporal smoothing of the
matte never carries one shot's silhouette into the next (a one-frame ghost at a jump cut).
"""
import importlib, json, math, os, random, subprocess, sys
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools", "fx"))
import fxlib
from fxlib import (Clip, Html, write_video, frost, over, transform, with_alpha, clean_plate, shadow, person_mattes,
                   prog, ease_out, lerp, FPS, W, H)

LIME = "#C8F25A"


def _clip_init(self, path, t0, t1, size=(W, H)):
    """fxlib.Clip with the seek written to 4 decimals, as cut.py writes it: «-ss 11.333» for 11.3333 landed one
    source frame early (zoom, vertigo), «-ss 15.767» for 15.7667 one frame late (checklist)."""
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
orig, work = sys.argv[1], sys.argv[2]
only = [a for a in sys.argv[3:] if not a.startswith("--")]
preview = "--preview" in sys.argv
T = json.load(open(os.path.join(HERE, "timeline.json")))
segs = T["segments"]
base = os.path.join(work, "base.mp4")
os.makedirs(os.path.join(work, "fx"), exist_ok=True)
mod = lambda n: importlib.import_module(f"effects.{n}")


def word(w, lo=0, hi=99, end=False):
    for x in T["words"]:
        if lo <= x["s"] <= hi and x["w"].lower().startswith(w.lower()):
            return x["e"] if end else x["s"]
    raise SystemExit(f"no word {w} in {lo}-{hi}")


def seg_at(t):
    return next(s for s in segs if s["out"][0] - 1e-3 <= t < s["out"][1] - 1e-3)


def warm_mattes(path, a, b, size=(W, H)):
    """Fill the matte cache shot by shot for [a, b) of the trimmed axis."""
    for s in segs:
        x, y = max(a, s["out"][0]), min(b, s["out"][1])
        if y - x > 1e-3:
            person_mattes(BClip(x, y))


def run(name, gen, n):
    out = os.path.join(work, "fx", f"{name}.mp4")
    if preview:
        idx = set(np.linspace(0, n - 1, 6).astype(int))
        shots = [cv2.resize(f, (360, 640)) for i, f in enumerate(gen) if i in idx]
        p = out.replace(".mp4", "-preview.jpg")
        cv2.imwrite(p, (np.clip(np.hstack(shots), 0, 1) * 255).astype(np.uint8))
        print(p, flush=True); return
    write_video(gen, out, crf=12)
    print(out, flush=True)


JOBS = {}

# ---- 16 cover story: the hook is a magazine cover ---------------------------------------------------------
JOBS["cover"] = (0.0, segs[0]["out"][1])
def cover():
    a, b = JOBS["cover"]
    m = mod("16_cover_story")
    m.CSS = (m.CSS.replace("#FFD84D", LIME).replace("font:900 200px/1 'Playfair Display'", "font:900 172px/1 'Playfair Display'")
             .replace("width:300px", "width:330px")
             .replace("#mast{position:absolute;left:0;right:0;top:250px", "#mast{position:absolute;left:0;right:0;top:165px")
             .replace("#kick{position:absolute;left:0;right:0;top:215px", "#kick{position:absolute;left:0;right:0;top:128px"))
    # the masthead sits high so his cap hides only the lower part of the middle letter
    clip = BClip(a, b)
    with Html() as html:
        run("cover", m.frames(clip, html, t0=a, mast_text="СЕНЬОРЫ", mast=0.0, kick=0.35, kicker="IT · ВЫПУСК № 19",
                              issue="ОКТЯБРЬ 2026",
                              lines=[("Главная тема", "AI заменит опытных?", word("опытных", 0, 3) - 0.1, 60, 1290),
                                     ("Прогноз", "Сеньоры больше не нужны", word("менее", 0, 3) - 0.1, 640, 1250)],
                              bar=2.4), len(clip))

# ---- 17 glass type: «ЧЕЛОВЕК» behind his head on the spoken word -------------------------------------------
JOBS["glass"] = (7.40, segs[2]["out"][1])
def glass():
    a, b = JOBS["glass"]
    clip = BClip(a, b)
    with Html() as html:
        run("glass", mod("17_glass_type").frames(clip, html, t0=a, word="ЧЕЛОВЕК", appear=word("человек", 7, 8) - 0.05,
                                                 cy=215, size=190, depth=18), len(clip))

# ---- 05 digital zoom from the 4K original (segment 3 is one continuous span at zoom 1.0) -------------------
JOBS["zoom"] = tuple(segs[3]["out"])
def zoom():
    a, b = JOBS["zoom"]
    sa, sb = segs[3]["src"]
    off = sa - a
    m = mod("05_digital_zoom")
    beats = [(sa, 1.0, ""), (word("разработку", 10, 12) + off, 1.22, ""), (word("быстрее", 10, 12) + off, 1.5, "")]
    clip = Clip(orig, sa, sb, size=(1620, 2880))
    with Html() as html:
        gen = m.frames(clip, html if not hasattr(m, "CSS") else html, t0=sa, beats=beats, word_y=1300)
        run("zoom", (np.clip((f - 0.5) * 1.05 + 0.5, 0, 1) for f in gen), len(clip))   # cut.py grade (contrast 1.05)

# ---- 07 checklist: AI can do it all, but does it fit THIS project? -----------------------------------------
JOBS["check"] = (segs[5]["out"][0], segs[7]["out"][1])
chk = mod("07_checklist")
chk.CSS = chk.CSS.replace("#C8F25A", LIME).replace("top:1060px", "top:990px").replace(
    "rgba(20,22,27,.78)", "rgba(12,16,10,.80)") + """
.row.bad .tx{color:#FF5A5A}
.bx.x{background:#FF3B3B;border-color:#FF3B3B}
"""
chk.JS = chk.JS.replace("const on=t>=tc; bx.className='bx'+(on?' on':''); if(on) done++;",
                        "const on=t>=tc; const bad=it[3]; bx.className='bx'+(on?(bad?' x':' on'):''); "
                        "document.getElementById('r'+j).className='row'+(on&&bad?' bad':''); if(on&&!bad) done++;")
chk.JS = chk.JS.replace("CFG.items.length;\n  document.getElementById('bar')", "(CFG.items.length-1);\n  document.getElementById('bar')")
chk.JS = chk.JS.replace("(100*done/CFG.items.length)", "(100*done/(CFG.items.length-1))")


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
    for i, ui in enumerate(html.frames(body, chk.CSS, f"const CFG={cfg};" + chk.JS, times)):
        out = frost(clip.frame(i), ui[..., 3])
        over(out, ui)
        yield out


def check():
    a, b = JOBS["check"]
    lo, hi = a, b
    items = [("Архитектура", word("архитектуру", lo, hi) - 0.05, word("архитектуру", lo, hi, True), False),
             ("Сервис", word("сервис", lo, hi) - 0.05, word("сервис", lo, hi, True), False),
             ("API", word("API", lo, hi) - 0.05, word("API", lo, hi, True), False),
             ("SQL-запросы", word("SQL", lo, hi) - 0.05, word("SQL", lo, hi, True), False),
             ("Тесты", word("тесты", lo, hi) - 0.05, word("тесты", lo, hi, True), False),
             ("Подходит ЭТОМУ проекту?", word("подходит", lo, hi) - 0.05, word("проекту", lo, hi, True), True)]
    clip = BClip(a, b)
    with Html() as html:
        run("check", check_frames(clip, html, t0=a, enter=a + 0.05, title="AI УМЕЕТ", items=items), len(clip))

# ---- 08 headline wall: each question slaps onto the wall on its own word, he keeps his size ----------------
JOBS["wall"] = (segs[11]["out"][0], segs[14]["out"][1])
W08 = mod("08_headline_wall")


def wall_frames(clip, html, t0, notes, spots):
    imgs = [W08.note(html, h, W08.STYLES[j % 4].replace("#FFE34D", LIME).replace("width:330px", "width:290px")
                     .replace("width:360px", "width:300px").replace("width:320px", "width:290px")
                     .replace("600 28px/1.3", "700 34px/1.25"), j % 4)
            for j, (h, _) in enumerate(notes)]
    rnd = random.Random(19)
    cards = [(spots[j], imgs[j], rnd.uniform(-6, 6), ts) for j, (_, ts) in enumerate(notes)]
    start = notes[0][1]
    mattes = person_mattes(clip)                     # read from the cache warm_mattes filled shot by shot
    for i in range(len(clip)):
        t = t0 + i / FPS
        f = clip.frame(i)
        k0 = ease_out(prog(t, start - 0.05, start + 0.35))
        back = f * (1 - 0.25 * k0)
        shake = 0.0
        for (px, py), img, ang, ts in cards:
            k = prog(t, ts, ts + 0.16)
            if k <= 0:
                continue
            sc = lerp(1.7, 1.0, ease_out(k, 2))
            if t - ts < 0.22:
                shake = max(shake, 1 - (t - ts) / 0.22)
            layer = transform(img, sc * 0.98, ang, tx=px, ty=py)
            over(back, shadow(layer, blur=lerp(30, 10, k), opacity=0.5, dx=6, dy=lerp(40, 12, k)))
            over(back, layer, opacity=min(1, k * 2))
        out = back
        over(out, with_alpha(f, mattes[i]))           # he stays in front, full size
        if shake > 0:
            dx, dy = 9 * shake * math.sin(t * 90), 7 * shake * math.cos(t * 77)
            out = cv2.warpAffine(out, np.float32([[1.01, 0, dx - 5.4], [0, 1.01, dy - 9.6]]), (W, H),
                                 borderMode=cv2.BORDER_REFLECT)
        yield out


def wall():
    a, b = JOBS["wall"]
    notes = [("Рост нагрузки?", word("росте", a, b) - 0.05), ("Сервис упал?", word("недоступен", a, b) - 0.05),
             ("Кто поддержит через полгода?", word("поддерживаться", a, b) - 0.05), ("Что с данными?", word("данными", a, b) - 0.05)]
    clip = BClip(a, b)
    with Html() as html:
        run("wall", wall_frames(clip, html, a, notes, spots=[(185, 370), (890, 340), (190, 720), (905, 580)]), len(clip))

# ---- 01 orbit: AI tools circle him, «каждый» lands on the wall -------------------------------------------
JOBS["orbit"] = (45.90, segs[17]["out"][1])
def orbit():
    a, b = JOBS["orbit"]
    m = mod("01_orbit")
    names = ["ChatGPT", "Claude", "Cursor", "Copilot", "Gemini", "Windsurf", "Lovable", "Devin"]
    m.card = lambda html, nm: html.still(
        f'<div style="padding:18px 34px;border-radius:60px;background:{"#F4F7EE" if hash(nm) % 3 else LIME};color:#10140C;'
        f'font:800 44px Manrope;box-shadow:0 18px 40px rgba(0,0,0,.45);white-space:nowrap">{nm}</div>',
        "body{display:flex;align-items:center;justify-content:center;height:100vh}", size=(420, 170))
    clip = BClip(a, b)
    with Html() as html:
        run("orbit", m.frames(clip, html, t0=a, start=word("активно", a, b) - 0.05, items=names,
                              title=[], title_y=300), len(clip))   # no wall title: here it hides behind his cap

# ---- 15 vertigo: the room slides away on «куда именно эту скорость направлять» ----------------------------
JOBS["vertigo"] = tuple(segs[23]["out"])
def vertigo():
    a, b = JOBS["vertigo"]
    sa, sb = segs[23]["src"]
    off = sa - a
    m = mod("15_vertigo")
    clip = Clip(orig, sa, sb, size=(1620, 2880))
    with Html() as html:
        gen = m.frames(clip, html, t0=sa, person_zoom=1.35, start=word("понять", a, b) + off, dur=1.8, text=("", 999))
        run("vertigo", (np.clip((f - 0.5) * 1.05 + 0.5, 0, 1) for f in gen), len(clip))

# ---- 06 phone mockup: the Telegram post with guide №11 ---------------------------------------------------
JOBS["phone"] = (segs[24]["out"][0], T["duration"])
def phone():
    a, b = JOBS["phone"]
    m = mod("06_phone_mockup")
    m.CSS += """
.file{display:flex;gap:14px;align-items:center;margin-top:12px;padding:12px;border-radius:14px;background:rgba(255,255,255,.06)}
.file .ic{width:54px;height:62px;border-radius:10px;background:""" + LIME + """;display:flex;align-items:center;justify-content:center;font:800 15px Unbounded;color:#10140C}
.file .fn{font:700 18px Manrope;line-height:1.25}
.file .fs{font:500 15px Manrope;opacity:.55}
"""
    _track = m.head_track
    m.head_track = lambda mattes: [tuple(np.median(np.array(_track(mattes)), axis=0))] * len(mattes)
    _body = m.body
    m.body = lambda chat, msgs: _body(chat, msgs).replace("бот · онлайн", "канал в Telegram")
    msgs = [dict(t=a + 0.35, html='<b>Гайд №11</b>На чём строится инженерное мышление: вопросы, которые не задаст AI.'),
            dict(t=a + 1.0, html='<div class=file style="margin:0"><div class=ic>PDF</div><div><div class=fn>'
                                 'Инженерное<br>мышление.pdf</div><div class=fs>канал · закреп</div></div></div>')]
    clip = BClip(a, b)
    with Html() as html:
        run("phone", m.frames(clip, html, t0=a, enter=a + 0.05, chat="Islam Dev AI", msgs=msgs, tap=99, tap_xy=(0, 0)), len(clip))


json.dump({k: [round(a, 4), round(b, 4)] for k, (a, b) in JOBS.items()},
          open(os.path.join(HERE, "fxspans.json"), "w"), indent=1)   # build.py reads it
names = only or list(JOBS)
for n in names:
    a, b = JOBS[n]
    if n not in ("zoom", "vertigo", "check"):
        warm_mattes(base, a, b)
    globals()[n]()
if preview or (only and "--splice" not in sys.argv):
    sys.exit()

# splice: base with every effect span replaced, frame-exact on the 30 fps grid
spans = sorted((round(JOBS[n][0] * FPS), round(JOBS[n][1] * FPS), n) for n in JOBS)
dur_f = round(T["duration"] * FPS)
parts, cur, inputs = [], 0, ["-i", base]
for k, (fa, fb, n) in enumerate(spans):
    if fa > cur:
        parts.append(f"[0:v]trim=start_frame={cur}:end_frame={fa},setpts=PTS-STARTPTS[p{len(parts)}]")
    inputs += ["-i", os.path.join(work, "fx", f"{n}.mp4")]
    parts.append(f"[{k + 1}:v]trim=end_frame={fb - fa},setpts=PTS-STARTPTS,fps={FPS},tpad=stop_mode=clone:stop={fb - fa}"
                 f",trim=end_frame={fb - fa}[p{len(parts)}]")
    cur = fb
if cur < dur_f:
    parts.append(f"[0:v]trim=start_frame={cur},setpts=PTS-STARTPTS[p{len(parts)}]")
fc = ";".join(parts) + ";" + "".join(f"[p{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[v]"
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-crf", "12",
                "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p", "-r", str(FPS), os.path.join(work, "base_fx.mp4")], check=True)
print("base_fx.mp4 ready")
