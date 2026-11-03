#!/usr/bin/env python3
"""Reel 24 «Telegram — интерфейс для бизнеса», step 2: tools/fx effects on the trimmed base, spliced back in.

    python3 fx24.py ORIG.mp4 WORK [name ...] [--preview] [--splice]

Times are on the trimmed axis (timeline.json); every effect sits inside shots of one zoom.
  green  12 green screen    0.00-3.03   «Telegram превращается … в интерфейс для бизнеса»: he stands in front of a
                                        Telegram chat list where every chat is a business system
  wall   08 headline wall   4.20-8.17   «CRM, админку, отдельное приложение и ещё пять сервисов»: the windows slap
                                        onto the wall behind him, then get crossed out
  phone  06 phone mockup    20.43-25.23 «руководитель пишет боту: сколько сегодня новых заявок?» and the bot answers
  pull   11 pull-back       29.43-34.73 «интерфейсом управления всей системой»: his shot sits inside Telegram, the
                                        systems connect one by one
  vertigo 15 vertigo        39.83-end   dolly zoom on «архитектуру такой системы» (CTA plate comes from build.py)
"""
import importlib, json, math, os, random, subprocess, sys
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools", "fx"))
import fxlib
from fxlib import (Clip, Html, write_video, over, transform, with_alpha, clean_plate, shadow, person_mattes, rounded_mask,
                   prog, ease_out, ease_in_out, lerp, FPS, W, H)

SKY, INK, PANEL = "#2AABEE", "#0E1621", "#17212B"     # Telegram's own sky blue and its dark theme


def _clip_init(self, path, t0, t1, size=(W, H)):
    """fxlib.Clip with a 4-decimal seek, as cut.py writes it (3 decimals landed a frame off on reel 19)."""
    self.path, self.t0, self.t1, self.size = str(path), t0, t1, size
    w, h = size
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t0:.4f}", "-t", f"{t1 - t0:.4f}", "-i", self.path,
           "-vf", f"scale={w}:{h}:flags=lanczos,fps={FPS}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = len(raw) // (w * h * 3)
    self.u8 = np.frombuffer(raw, np.uint8)[: n * w * h * 3].reshape(n, h, w, 3)
    self.n = n


Clip.__init__ = _clip_init

orig, work = sys.argv[1], sys.argv[2]
only = [a for a in sys.argv[3:] if not a.startswith("--")]
preview = "--preview" in sys.argv
T = json.load(open(os.path.join(HERE, "timeline.json")))
WORDS, segs = T["words"], T["segments"]
base = os.path.join(work, "base.mp4")
os.makedirs(os.path.join(work, "fx"), exist_ok=True)
mod = lambda n: importlib.import_module(f"effects.{n}")
HOLD = 1.2          # the last frame is held after he stops talking, under the CTA plate


def BClip(a, b):
    """Frames [a, b) of base.mp4: the seek sits a quarter frame before a, so frame a is the first one kept."""
    c = Clip(base, a - 0.008, b - 0.008)
    c.t0, c.t1 = a, b
    return c


def word(w, lo=0, hi=99, end=False):
    for x in WORDS:
        if lo <= x["s"] <= hi and x["w"].lower().strip("«»,.:?").startswith(w.lower()):
            return x["e"] if end else x["s"]
    raise SystemExit(f"no word {w} in {lo}-{hi}")


def span(*ks):
    return segs[ks[0]]["out"][0], segs[ks[-1]]["out"][1]


def warm_mattes(a, b):
    """Fill the matte cache shot by shot, so smoothing never carries a silhouette across a jump cut."""
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
        print(p, flush=True)
        return
    write_video(gen, out, crf=12)
    print(out, flush=True)


JOBS = {}

# ---- 12 green screen: the hook. His room turns into a Telegram chat list of business systems -------------
JOBS["green"] = span(0)
def green():
    a, b = JOBS["green"]
    m = mod("12_green_screen")
    m.CSS = f"""
body{{width:1080px;height:1920px;background:radial-gradient(1200px 900px at 50% 30%,#1B3A55 0%,{INK} 70%);font-family:Manrope;overflow:hidden}}
#app{{position:absolute;left:50px;right:50px;top:300px;height:500px;border-radius:34px;background:{PANEL};
     box-shadow:0 30px 80px rgba(0,0,0,.55),0 0 0 2px rgba(42,171,238,.35);overflow:hidden}}
.top{{position:relative;z-index:2;display:flex;align-items:center;gap:14px;padding:24px 30px;background:#1F2C3A;color:#fff;font-size:0}}
.top:after{{content:'Telegram · бизнес';order:1;font:800 32px Manrope}}
.top:before{{content:"";width:46px;height:46px;border-radius:50%;background:{SKY} url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M21.5 3.6 2.9 10.8c-1 .4-1 1.8.1 2.1l4.7 1.5 1.8 5.6c.3.9 1.4 1.1 2 .4l2.6-2.6 4.9 3.6c.8.6 1.9.1 2.1-.8l3-15.3c.2-1.2-.9-2.1-2.1-1.6z' fill='white'/%3E%3C/svg%3E") center/26px no-repeat}}
.top b{{order:2;margin-left:auto;padding:6px 16px;border-radius:20px;background:{SKY};font:800 26px Unbounded}}
#list{{position:absolute;left:0;right:0;top:94px}}
.it{{display:flex;gap:18px;align-items:center;padding:18px 30px;border-bottom:1px solid rgba(255,255,255,.06);height:112px;background:{PANEL}}}
.av{{width:68px;height:68px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;color:#fff;font:800 24px Unbounded}}
.tx{{flex:1;min-width:0}}.nm{{font:800 27px Manrope;color:#fff}}.q{{font:500 25px Manrope;color:#8EA3B8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.tm{{font:600 21px Manrope;color:#6E8297;text-align:right}}.tm i{{display:block;margin-top:8px;margin-left:auto;width:34px;height:34px;border-radius:50%;
    background:{SKY};color:#fff;font:800 18px/34px Manrope;text-align:center;font-style:normal}}
#cap{{position:absolute;left:0;right:0;top:214px;text-align:center;font:800 50px Unbounded;color:#fff;letter-spacing:-.02em}}
#cap span{{background:{SKY};color:#fff;padding:0 14px;border-radius:12px}}
"""
    chats = [("CRM · Заявки", "Новый лид: Руслан, автосервис", "#2AABEE"),
             ("AI-ассистент", "Черновик ответа готов ✓", "#7B61FF"),
             ("Склад", "Осталось 12 шт. — заказать?", "#F2A93B"),
             ("Оплаты", "Счёт №214 оплачен: 48 000 ₽", "#2BB673"),
             ("Отчёты", "Заявок за день: 14", "#E5484D"),
             ("Задачи команды", "Перезвонить клиенту до 15:00", "#1E9BD7")]
    clip = BClip(a, b)
    fxlib.MATTE_MODEL = "human+objects"      # the mic on its arm stays in front of him
    with Html() as html:
        run("green", m.frames(clip, html, t0=a, swap=a + 0.1, flood=0.35, every=0.3, cap=word("интерфейс", 1.5, 2.5) - 0.05,
                              questions=[c[1] for c in chats], names=[c[0] for c in chats], colors=[c[2] for c in chats],
                              caption='мессенджер → <span>интерфейс</span>', person_scale=0.72), len(clip))
    fxlib.MATTE_MODEL = "human"


# ---- 08 headline wall: CRM, the admin panel, an app and five more services slap on the wall, then crossed --
JOBS["wall"] = span(2)
def wall():
    a, b = JOBS["wall"]
    css = "body{display:flex;align-items:center;justify-content:center;height:100vh}"

    def window(title, lines, accent, small=False, crossed=False):
        w = 280 if small else 330
        rows = "".join(f'<div style="height:{14 if small else 18}px;border-radius:8px;background:#E6EAF0;margin-top:{10 if small else 14}px;width:{x}%"></div>'
                       for x in lines)
        x = (f'<svg style="position:absolute;inset:-10px;width:calc(100% + 20px);height:calc(100% + 20px)" viewBox="0 0 100 100" preserveAspectRatio="none">'
             f'<path d="M6 8 L94 92 M94 8 L6 92" stroke="#FF3B3B" stroke-width="7" stroke-linecap="round" vector-effect="non-scaling-stroke" style="stroke-width:16px"/></svg>'
             if crossed else "")
        return (f'<div style="position:relative;width:{w}px;border-radius:20px;background:#fff;overflow:hidden;'
                f'box-shadow:0 2px 0 rgba(0,0,0,.08)">'
                f'<div style="display:flex;align-items:center;gap:8px;padding:12px 16px;background:{accent};color:#fff;'
                f'font:800 {22 if small else 30}px Unbounded"><i style="width:10px;height:10px;border-radius:50%;background:#fff;opacity:.8"></i>{title}</div>'
                f'<div style="padding:4px 18px 20px">{rows}</div>{x}</div>')

    items = [("CRM", [90, 70, 80, 55], "#E5484D", False, word("CRM", 5, 6.2)),
             ("Админка", [60, 85, 70], "#6B7487", False, word("админку", 5.8, 6.5)),
             ("Приложение", [75, 50, 85], "#7B61FF", False, word("отдельное", 6.2, 7) + 0.25),
             ("Почта", [80, 60], "#F2A93B", True, word("пять", 7.3, 7.8)),
             ("Таблицы", [70, 85], "#2BB673", True, word("пять", 7.3, 7.8) + 0.08),
             ("Задачи", [65, 80], "#1E9BD7", True, word("сервисов", 7.5, 8) - 0.02),
             ("Звонки", [85, 55], "#FF7A2F", True, word("сервисов", 7.5, 8) + 0.06),
             ("Отчёты", [60, 75], "#9B59B6", True, word("сервисов", 7.5, 8) + 0.14)]
    strike = b - 0.3
    spots = [(215, 330), (865, 310), (190, 700), (560, 175), (875, 690), (190, 1010), (890, 1000), (870, 480)]
    rnd = random.Random(24)
    with Html() as html:
        imgs = [(html.still(window(t, l, c, s), css, size=(460, 420)), html.still(window(t, l, c, s, True), css, size=(460, 420)))
                for t, l, c, s, _ in items]
    cards = [(spots[j], imgs[j], rnd.uniform(-7, 7), items[j][4]) for j in range(len(items))]
    clip = BClip(a, b)
    mattes = person_mattes(clip)

    def gen():
        for i in range(len(clip)):
            t = a + i / FPS
            f = clip.frame(i)
            k0 = ease_out(prog(t, cards[0][3] - 0.25, cards[0][3] + 0.15))
            ps = lerp(1.0, 0.86, k0)
            back = clean_plate(f, mattes[i]) * lerp(1, 0.6, k0) if k0 > 0 else f.copy()
            sh = 0.0
            for j, ((x, y), (im, imx), ang, ts) in enumerate(cards):
                k = prog(t, ts, ts + 0.16)
                if k <= 0:
                    continue
                sc = lerp(1.7, 1.0, ease_out(k, 2))
                if t - ts < 0.22:
                    sh = max(sh, 1 - (t - ts) / 0.22)
                layer = transform(imx if t >= strike + 0.04 * j else im, sc, ang, tx=x, ty=y)
                over(back, shadow(layer, blur=lerp(30, 10, k), opacity=0.5, dx=6, dy=lerp(40, 12, k)))
                over(back, layer, opacity=min(1, k * 2))
            out = back
            over(out, transform(with_alpha(f, mattes[i]), ps, 0, cx=W / 2, cy=H, tx=W / 2, ty=H))
            if sh > 0:
                dx, dy = 8 * sh * math.sin(t * 90), 6 * sh * math.cos(t * 77)
                out = cv2.warpAffine(out, np.float32([[1.01, 0, dx - 5.4], [0, 1.01, dy - 9.6]]), (W, H), borderMode=cv2.BORDER_REFLECT)
            yield out
    run("wall", gen(), len(clip))


# ---- 06 phone mockup: the owner asks the bot how many new requests came today -----------------------------
JOBS["phone"] = span(6, 8)
def phone():
    a, b = JOBS["phone"]
    m = mod("06_phone_mockup")
    m.CSS += f"""
#sc{{background:{INK}}}
.msg{{font:600 27px/1.35 Manrope}}
.msg.out{{margin-left:110px;background:#2B5278;border-bottom-right-radius:6px}}
.msg.in{{margin-right:20px;background:{PANEL};border-bottom-left-radius:6px}}
.msg .row{{display:flex;justify-content:space-between;font:600 25px Manrope;opacity:.85;margin-top:4px}}
.msg .row em{{font-style:normal;font-weight:800;color:{SKY}}}
.tick{{display:block;text-align:right;font:600 15px Manrope;color:#7FC4F0;margin-top:4px}}
"""
    _track = m.head_track
    m.head_track = lambda mattes: [tuple(np.median(np.array(_track(mattes)), axis=0))] * len(mattes)
    # bigger phone (the stock 0.74 left the bot's numbers unreadable), pinned at the right edge beside his beard
    import inspect
    src = (inspect.getsource(m.frames).replace("* 0.74", "* 0.88")
           .replace("cx = max(hx + 0.62 * hw + PW * 0.37, min(W - 130 - PW * 0.37, hx + 1.3 * hw))", "cx = W - 50 - PW * 0.44")
           .replace("cy = hy + 2.0 * hw", "cy = 700 + 0 * hw"))
    exec(src, m.__dict__)
    _body = m.body
    m.body = lambda chat, msgs: (_body(chat, msgs).replace("бот · онлайн", "ваш бизнес-бот · онлайн")
                                 .replace("class=msg id=m0", "class='msg out' id=m0").replace("class=msg id=m1", "class='msg in' id=m1"))
    q = word("сколько", 21.5, 22.5)
    ans = word("получает", 23, 24)
    msgs = [dict(t=q - 0.1, html='Сколько сегодня новых заявок?<span class=tick>10:42 ✓✓</span>'),
            dict(t=ans - 0.1, html='<b>Сегодня 14 новых заявок</b><div class=row>сайт<em>6</em></div><div class=row>Telegram<em>5</em></div>'
                                   '<div class=row>звонки<em>3</em></div><div class=row style="margin-top:8px">ждут ответа<em style="color:#FF6B6B">2</em></div>'
                                   '<div class=btns><div class=bt>Показать</div><div class="bt g">Назначить</div></div>')]
    clip = BClip(a, b)
    with Html() as html:
        run("phone", m.frames(clip, html, t0=a, enter=a + 0.1, chat="CRM-бот", msgs=msgs, tap=99, tap_xy=(0, 0)), len(clip))


# ---- 11 pull-back: his shot turns out to be a chat window inside the Telegram «control panel» -------------
JOBS["pull"] = span(10, 11)
def pull():
    a, b = JOBS["pull"]
    SLOT = (330, 400, 600, 1067)
    S = 2
    base_css = f"""
body{{width:1080px;height:1920px;background:radial-gradient(1100px 1200px at 60% 35%,#1B3A55 0%,{INK} 75%)}}
#win{{position:absolute;left:300px;top:330px;width:660px;height:1340px;border-radius:30px;background:{PANEL};
     box-shadow:0 40px 90px rgba(0,0,0,.5),0 0 0 2px rgba(42,171,238,.4)}}
.tb{{height:56px;display:flex;align-items:center;gap:10px;padding:0 22px;font:700 20px Manrope;color:#8EA3B8}}
.tb i{{width:13px;height:13px;border-radius:50%;background:#2F3E4E;display:block}}
.tb .nm{{margin-left:auto;margin-right:auto;font:800 21px Manrope;color:#fff}}
#slot{{position:absolute;left:30px;top:70px;width:600px;height:1067px;border-radius:18px;background:#000}}
#bar{{position:absolute;left:30px;right:30px;top:1160px;height:150px;border-radius:18px;background:#1F2C3A;padding:22px 24px;color:#fff;font:700 26px Manrope}}
#bar small{{display:block;font:600 20px Manrope;color:#8EA3B8;margin-bottom:12px}}
"""
    top_css = f"""
body{{width:1080px;height:1920px}}
#side{{position:absolute;left:34px;top:600px;width:450px;border-radius:26px;background:rgba(23,33,43,.97);padding:26px 26px 18px;
      box-shadow:0 30px 70px rgba(0,0,0,.5);border:2px solid rgba(42,171,238,.45);font:800 33px Manrope;color:#fff}}
#side .h{{font:800 20px Unbounded;color:{SKY};letter-spacing:.06em;margin-bottom:14px}}
.st{{display:flex;align-items:center;gap:16px;height:70px;opacity:.3}}
.st i{{width:34px;height:34px;border-radius:50%;border:3px solid #4A5B6C;flex:none;display:flex;align-items:center;
      justify-content:center;color:#fff;font:800 19px Manrope;font-style:normal}}
.st.on{{opacity:1}}.st.on i{{background:{SKY};border-color:{SKY}}}
#ttl{{position:absolute;left:44px;top:176px;width:1000px;font:900 58px/1.05 Unbounded;color:#fff;letter-spacing:-.03em;text-transform:uppercase}}
#ttl em{{font-style:normal;color:{SKY}}}
#ttl small{{display:block;font:800 24px Unbounded;letter-spacing:.14em;color:#8EA3B8;margin-bottom:10px}}
"""
    steps = [("CRM", word("управления", 32.5, 34)), ("Заявки", word("управления", 32.5, 34) + 0.3), ("Склад", word("всей", 33.5, 34.2)),
             ("Оплаты", word("системой", 33.8, 34.5)), ("AI-агент", word("системой", 33.8, 34.5) + 0.3)]
    js = """window.seek=t=>{CFG.steps.forEach((s,j)=>{document.getElementById('s'+j).className='st'+(t>=s[1]?' on':'');});
      document.getElementById('ttl').style.opacity=Math.min(1,Math.max(0,(t-CFG.ttl)/0.3));};"""
    pull_at = word("интерфейсом", 32.5, 33) - 0.25
    clip = BClip(a, b)
    with Html() as html:
        bg = html.still('<div id=win><div class=tb><i></i><i></i><i></i><span class=nm>Telegram · бизнес</span></div><div id=slot></div>'
                        '<div id=bar><small>сообщение</small>/сводка за день</div></div>', base_css, scale=S)
        times = [a + i / FPS for i in range(round((b - a) * FPS) + 1)]
        top_body = ('<div id=ttl><small>не просто чат</small>Пульт <em>всей системы</em></div><div id=side><div class=h>ПОДКЛЮЧЕНО</div>' +
                    "".join(f'<div class=st id=s{j}><i>✓</i>{s}</div>' for j, (s, _) in enumerate(steps)) + '</div>')
        cfg = json.dumps(dict(steps=steps, ttl=pull_at + 0.5), ensure_ascii=False)
        tops = html.frames(top_body, top_css, f"const CFG={cfg};" + js, times, scale=S)
        sx, sy, sw, sh = SLOT
        z0 = W / sw
        c_slot = np.array([sx + sw / 2, sy + sh / 2]); c_full = np.array([W / 2, H / 2])

        def gen():
            for i, top in zip(range(len(clip)), tops):
                t = a + i / FPS
                k = ease_in_out(prog(t, pull_at, pull_at + 0.9))
                if k <= 0:
                    yield clip.frame(i)
                    continue
                z = z0 ** (1 - k)
                c = c_slot * (1 - k) + c_full * k
                A = np.float32([[z, 0, W / 2 - z * c[0]], [0, z, H / 2 - z * c[1]]])
                A2 = A.copy(); A2[:, :2] /= S
                out = cv2.warpAffine(bg[..., :3], A2, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
                vid = cv2.resize(clip.frame(i), (sw * 2, sh * 2), interpolation=cv2.INTER_AREA)
                vl = np.dstack([vid, rounded_mask(sw * 2, sh * 2, max(1, int(36 * min(1, k * 3))))])
                Av = A.copy(); Av[:, :2] /= 2; Av[0, 2] += z * sx; Av[1, 2] += z * sy
                over(out, cv2.warpAffine(vl, Av, (W, H), flags=cv2.INTER_LINEAR))
                over(out, cv2.warpAffine(top, A2, (W, H), flags=cv2.INTER_AREA), opacity=min(1, k * 1.6))
                yield out
        run("pull", gen(), len(clip))


# ---- 15 vertigo from the 4K original on «архитектуру такой системы» ------------------------------------------
JOBS["vertigo"] = span(13)
def vertigo():
    a, b = JOBS["vertigo"]
    sa, sb = segs[13]["src"]
    off = sa - a
    clip = Clip(orig, sa, sb, size=(1620, 2880))
    with Html() as html:
        gen = mod("15_vertigo").frames(clip, html, t0=sa, person_zoom=1.3, start=word("архитектуру", 40, 41.5) + off - 0.15,
                                       dur=1.9, text=("", 999))
        run("vertigo", (np.clip((f - 0.5) * 1.05 + 0.5, 0, 1) for f in gen), len(clip))


json.dump({k: [round(a, 4), round(b, 4)] for k, (a, b) in JOBS.items()}, open(os.path.join(HERE, "fxspans.json"), "w"), indent=1)
names = only or list(JOBS)
if "--splice" not in sys.argv or only:
    for n in names:
        a, b = JOBS[n]
        if n not in ("vertigo",):
            warm_mattes(a, b)
        globals()[n]()
if preview or (only and "--splice" not in sys.argv):
    sys.exit()

# splice: base with every effect span replaced, frame-exact on the 30 fps grid, then the last frame held
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
fc = (";".join(parts) + ";" + "".join(f"[p{i}]" for i in range(len(parts))) +
      f"concat=n={len(parts)}:v=1:a=0,tpad=stop_mode=clone:stop_duration={HOLD}[v]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-crf", "12",
                "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p", "-r", str(FPS), os.path.join(work, "base_fx.mp4")], check=True)
print("base_fx ready")
