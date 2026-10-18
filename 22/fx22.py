#!/usr/bin/env python3
"""Reel 22, step 2: the person-aware effects from tools/fx, rendered on the trimmed base and spliced back in.

    python3 fx22.py WORK [name ...] [--preview]     # WORK/base.mp4 -> WORK/fx/*.mp4 -> WORK/base_fx.mp4

Times are on the trimmed axis (timeline.json); every effect sits inside one shot of one zoom.
  radar   0.00-4.83   «AI сам находит клиентов»: a radar behind his head, companies blip, three turn into leads
  ui      4.83-10.90  «получает список компаний, изучает сайты»: the agent's screen on top, he goes down
  wall    15.93-20.07 «анализирует ответы, кому написать повторно»: replies land on the wall behind him
  zoom    20.07-23.37 «интересным именно для бизнеса»: two punch-ins
  paper   23.37-26.30 «давайте поставим чат-бота на сайт»: paper cut-out, ransom letters, struck out
  orbit   37.40-39.07 «человек должен оставаться в контуре»: AI steps orbit around him
  phone   42.93-45.23 CTA: the Telegram channel post with guide #15 (held 1.2 s at the end)
"""
import json, math, os, subprocess, sys
import numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "fx"))
import fxlib
from fxlib import (Clip, Html, write_video, over, transform, person_mattes, head_track, person_over, prog, ease_out,
                   ease_out_back, lerp, FPS, W, H)
import importlib

ui = importlib.import_module("effects.03_ui_world")
wall = importlib.import_module("effects.02_couch_wall")
zoom = importlib.import_module("effects.05_digital_zoom")
paper = importlib.import_module("effects.13_paper_cut")
orbit = importlib.import_module("effects.01_orbit")
phone = importlib.import_module("effects.06_phone_mockup")

HERE = os.path.dirname(os.path.abspath(__file__))
GREEN, NAVY = "#1ED68F", "#0E1726"
work = sys.argv[1]
names = [a for a in sys.argv[2:] if not a.startswith("--")]
preview = "--preview" in sys.argv
os.makedirs(os.path.join(work, "fx"), exist_ok=True)
base = os.path.join(work, "base.mp4")


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


# ---------------------------------------------------------------- radar (new for this reel)
def chip(html, text, green):
    bg = "rgba(30,214,143,.95)" if green else "rgba(14,23,38,.86)"
    fg = NAVY if green else "#fff"
    dot = NAVY if green else GREEN
    return html.still(f'<div style="display:inline-flex;align-items:center;gap:12px;padding:12px 22px;border-radius:18px;'
                      f'background:{bg};color:{fg};font:800 36px Manrope;white-space:nowrap;'
                      f'box-shadow:0 12px 30px rgba(0,0,0,.45);border:2px solid rgba(255,255,255,.18)">'
                      f'<i style="width:14px;height:14px;border-radius:50%;background:{dot}"></i>{text}</div>',
                      "body{display:flex;align-items:center;justify-content:center;height:100vh}", size=(560, 120))


def radar_frames(clip, html, t0, start, blips, lead_at, turn=1.7):
    """blips: (name, angle_deg, radius_share, appear_t, is_lead). Leads turn green and get a «лид» tag at lead_at."""
    mattes = person_mattes(clip)
    heads = head_track(mattes)
    hx = float(np.median([h[0] for h in heads])); hy = float(np.median([h[1] for h in heads]))
    hw = float(np.median([h[2] for h in heads]))
    cx, cy = hx, hy + 0.75 * hw
    R = 600
    g = tuple(float(c) / 255 for c in (0x8F, 0xD6, 0x1E))     # BGR of GREEN
    ga = np.float32(g)
    chips = [(chip(html, n, False), chip(html, n + " · лид", True)) for n, *_ in blips]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    dist = np.sqrt(dx * dx + dy * dy)
    ang = (np.degrees(np.arctan2(dy, dx)) + 360) % 360
    for i in range(len(clip)):
        t = t0 + i / FPS
        f = clip.frame(i)
        k = ease_out(prog(t, start, start + 0.6))
        if k <= 0:
            yield f
            continue
        r = R * k
        inside = np.clip((r - dist) / 6, 0, 1)
        bg = f * (1 - 0.55 * inside[..., None]) + np.float32([0.15, 0.09, 0.05]) * 0.55 * inside[..., None]
        layer = np.zeros((H, W, 4), np.float32)
        for q in (0.25, 0.5, 0.75, 1.0):
            cv2.circle(layer, (int(cx), int(cy)), int(r * q), (*g, 0.55 if q == 1 else 0.28), 3 if q == 1 else 2, cv2.LINE_AA)
        cv2.line(layer, (int(cx - r), int(cy)), (int(cx + r), int(cy)), (*g, 0.18), 2, cv2.LINE_AA)
        cv2.line(layer, (int(cx), int(cy - r)), (int(cx), int(cy + r)), (*g, 0.18), 2, cv2.LINE_AA)
        sweep = (360 * (t - start) / turn) % 360
        lag = (sweep - ang) % 360                      # degrees behind the sweep line
        wedge = np.where((lag < 70) & (dist < r), (1 - lag / 70) ** 2 * 0.55, 0).astype(np.float32)
        bg = bg * (1 - wedge[..., None]) + ga * wedge[..., None]
        out = bg
        over(out, layer)
        tags = []
        for j, (name, a_deg, rs, ta, lead) in enumerate(blips):
            if t < ta:
                continue
            bx, by = cx + R * rs * math.cos(math.radians(a_deg)), cy + R * rs * math.sin(math.radians(a_deg))
            p = prog(t, ta, ta + 0.35)
            is_lead = lead and t >= lead_at + 0.12 * j
            col = (0.98, 0.98, 0.98) if not is_lead else g
            rad = int(10 + 6 * is_lead)
            cv2.circle(out, (int(bx), int(by)), rad, col, -1, cv2.LINE_AA)
            if p < 1:   # ping ring
                cv2.circle(out, (int(bx), int(by)), int(12 + 50 * p), col, 3, cv2.LINE_AA)
            tags.append((chips[j][1 if is_lead else 0], bx, by, p, is_lead))
        out = person_over(out, f, mattes[i])
        for img, bx, by, p, is_lead in tags:   # chips sit over him so the names stay readable
            s = lerp(0.6, 1.0 if not is_lead else 1.08, ease_out_back(min(1, p)))
            over(out, transform(img, s, 0, tx=min(max(bx, 290), 790), ty=max(by - 66, 250)), opacity=min(1, p * 2))
        yield out


# ---------------------------------------------------------------- ui world: the agent studies company sites
ui.CSS = (ui.CSS.replace("#D9622B", GREEN).replace("#FFE34D", GREEN).replace("#2BB673", GREEN)
          + ".res{font-size:31px}.res em.no{background:#FF4D4D}.brand{font-family:Unbounded;font-weight:800;font-size:34px}")
_ui_body = ui.body
ui.body = lambda files, results: (_ui_body(files, results)
                                  .replace("<b>✳</b> AI-ассистент", "<b>◎</b> AI-агент · поиск клиентов")
                                  .replace("Перетащите файлы сюда", "Список компаний").replace(">МАТЕРИАЛЫ<", ">САЙТЫ<")
                                  .replace("<em>✓</em>Зерно", "<em class=no>✕</em>Зерно"))

# ---------------------------------------------------------------- wall: replies sorted by the second agent
wall.CSS = wall.CSS


def reply_tile(html, path=None, note=None):
    who, txt, tag, col = note
    body = (f'<div style="width:250px;padding:20px 20px 18px;border-radius:18px;background:#fff;color:#14161B;'
            f'box-shadow:0 14px 30px rgba(0,0,0,.5);font:700 25px/1.25 Manrope">'
            f'<div style="font:800 17px Manrope;color:#8A93A3;margin-bottom:8px">{who}</div>{txt}'
            f'<div style="margin-top:12px;display:inline-block;padding:6px 12px;border-radius:10px;background:{col};'
            f'color:{"#0E1726" if col == GREEN else "#fff"};font:800 18px Manrope">{tag}</div></div>')
    return html.still(body, wall.CSS, size=(300, 480))


wall.tile = reply_tile

# ---------------------------------------------------------------- paper cut: strike out instead of circling
_letter = paper.letter
paper.letter = lambda html, ch, j, rnd: (np.zeros((220, 200, 4), np.float32) if ch == " " else _letter(html, ch, j, rnd))
_paper_frames = paper.frames


def _photo_mattes(clip):
    """The whole frame as a torn photo pasted on the page: a person matte lost the mic arm (grey ghosts) and
    ISNet pulled in a block of the shelf, so the scrapbook gets a photo cut-out instead of a silhouette."""
    m = np.zeros((H, W), np.float32)
    m[60:H - 10, 40:W - 40] = 1
    return [m] * len(clip)


def paper_frames(clip, html, t0, strike, **kw):
    paper.person_mattes = _photo_mattes
    for i, out in enumerate(_paper_frames(clip, html, t0, circle=1e9, **kw)):
        t = t0 + i / FPS
        if t >= strike:
            r = np.random.default_rng(i // 3)
            for j, y in enumerate((kw.get("lines_y", 330) + 10, kw.get("lines_y", 330) + 170)):  # one stroke per line
                p = min(1, (t - strike - 0.1 * j) / 0.18)
                if p <= 0:
                    continue
                x0, x1 = 150, 150 + int(820 * p)
                cv2.line(out, (x0, int(y + 30 + r.normal(0, 1.5))), (x1, int(y - 10 + r.normal(0, 1.5))), (0.18, 0.1, 0.88), 16,
                         cv2.LINE_AA)
        yield out


# ---------------------------------------------------------------- orbit: AI steps around the human
def step_card(html, text):
    num, label = text
    return html.still(
        f'<div style="width:230px;padding:20px 18px;border-radius:22px;background:rgba(14,23,38,.92);border:3px solid {GREEN};'
        f'color:#fff;font:800 28px/1.15 Manrope;text-align:center;box-shadow:0 18px 40px rgba(0,0,0,.45)">'
        f'<div style="font:900 22px Unbounded;color:{GREEN};margin-bottom:6px">AI · {num}</div>{label}</div>',
        "body{display:flex;align-items:center;justify-content:center;height:100vh}", size=(300, 470))


orbit.card = step_card
_orbit_title = orbit.title_img
orbit.title_img = lambda html, parts: [im for im in _orbit_title(html, parts)]

# ---------------------------------------------------------------- phone CTA
phone.CSS += f"""
.file{{display:flex;gap:14px;align-items:center;margin-top:12px;padding:12px;border-radius:14px;background:rgba(255,255,255,.06)}}
.file .ic{{width:54px;height:62px;border-radius:10px;background:{GREEN};display:flex;align-items:center;justify-content:center;font:800 15px Unbounded;color:{NAVY}}}
.file .fn{{font:700 18px Manrope;line-height:1.25}}
.file .fs{{font:500 15px Manrope;opacity:.55}}
"""
_track = phone.head_track
phone.head_track = lambda mattes: [tuple(np.median(np.array(_track(mattes)), axis=0))] * len(mattes)
_body = phone.body
phone.body = lambda chat, msgs: _body(chat, msgs).replace("бот · онлайн", "канал в Telegram")

JOBS = {
    "radar": dict(gen=radar_frames, t0=0.0, t1=4.8333, start=0.05, lead_at=3.30,
                  blips=[("Дента+", 200, 0.62, 0.55, True), ("АвтоМотор", 330, 0.78, 0.95, True),
                         ("Кофе «Зерно»", 155, 0.62, 1.35, False), ("СтройДом", 20, 0.62, 1.75, True),
                         ("Логистик", 120, 0.86, 2.15, False)]),
    "ui": dict(gen=ui.frames, t0=4.8333, t1=10.9, split=4.95,
               files=[("Дента+", "WEB", "#2F6BFF", 6.40), ("АвтоМотор", "WEB", "#2F6BFF", 6.55),
                      ("Зерно", "WEB", "#2F6BFF", 6.70), ("СтройДом", "WEB", "#2F6BFF", 6.85)],
               tag=7.19, type=7.25, cmd="/изучи сайты: кому нужен наш продукт?",
               results=[("Дента+ · 3 филиала, нет онлайн-записи", 8.0), ("АвтоМотор · заявки теряются в WhatsApp", 8.75),
                        ("Зерно · не наш клиент", 9.6), ("СтройДом · растёт, нанимает продажников", 10.2)]),
    "wall": dict(gen=wall.frames, t0=15.9333, t1=20.0667, start=17.0, every=0.11, tiles=[],
                 notes=[("Дента+", "Интересно, пришлите КП", "горячий", GREEN),
                        ("АвтоМотор", "Не сейчас, после праздников", "повтор через 7 дней", "#F2A93B"),
                        ("СтройДом", "Сколько стоит внедрение?", "горячий", GREEN),
                        ("Логистик", "Без ответа 3 дня", "написать ещё раз", "#F2A93B"),
                        ("ТехноСклад", "Нам не подходит", "закрыть", "#8A93A3")],
                 words=[("", 1e9, "s")], words_y=1330),
    "zoom": dict(gen=zoom.frames, t0=20.0667, t1=23.3667, word_y=-999,
                 beats=[(20.0667, 1.0, ""), (21.62, 1.22, ""), (22.74, 1.45, "")]),
    "paper": dict(gen=paper_frames, t0=23.3667, t1=26.3, person_scale=0.8, lines_y=240, letter_dt=0.05, strike=25.95,
                  lines=[("ЧАТ-БОТ", 25.20), ("НА САЙТ", 25.70)]),
    "orbit": dict(gen=orbit.frames, t0=37.40, t1=39.0667, start=37.45,
                  items=[("1", "Поиск"), ("2", "Анализ"), ("3", "Оценка"), ("4", "КП"), ("5", "Повтор")],
                  title=[("человек остаётся", 37.45, "s"), ("в контуре", 38.60, "b")], title_y=-900, speed=0.45),
    "phone": dict(gen=phone.frames, t0=42.9333, t1=45.2333, enter=42.96, chat="Islam Dev AI",
                  msgs=[dict(t=43.55, html='<b>Гайд №15</b>AI-воронка поиска клиентов: 6 шагов от списка компаний '
                                           'до лида у менеджера.'),
                        dict(t=44.15, html='<div class=file style="margin:0"><div class=ic>PDF</div><div><div class=fn>'
                                           'AI-воронка поиска<br>клиентов.pdf</div><div class=fs>канал · закреп</div></div></div>')],
                  tap=99, tap_xy=(0, 0)),
}
HOLD = 1.2          # seconds the last CTA frame is held after he stops talking

for name in ([] if "--splice" in sys.argv else names or list(JOBS)):   # --splice: reuse rendered effects
    cfg = dict(JOBS[name])
    gen, t0, t1 = cfg.pop("gen"), cfg.pop("t0"), cfg.pop("t1")
    fxlib.MATTE_MODEL = cfg.pop("matte", "human")
    clip = BClip(t0, t1)
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
dur = json.load(open(os.path.join(HERE, "timeline.json")))["duration"]
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
