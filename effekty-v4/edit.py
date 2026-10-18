"""Reel «17 эффектов» v4: 17 short takes, one effect each, joined by prep.py, soft
zoom-blur transitions at every boundary, voice fitted to his lips (voice.py).
usage: python3 edit.py [--preview SEG ...] [--out FILE]"""
import argparse, importlib, os, sys, collections, subprocess
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools", "fx"))
import fxlib
fxlib.MATTE_MODEL = "human+objects"   # he holds the cup most of the time: keep it in front
from fxlib import Clip, Html, over, zoom_frame, radial_blur, prog, ease_in, ease_out, W, H, FPS

TIGHT = f"{HERE}/work/tight.mp4"
WORK = __import__("pathlib").Path(HERE) / "work"
VOICE = f"{HERE}/work/tight-voice.wav"
sys.path.insert(0, HERE)
from plan import T, END, start, TAKES

TH = [f"/tmp/fx/thumbs/t{i:02d}.jpg" for i in (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12)]

# (effect, start on the reel timeline, settings); a segment ends where the next starts. Times inside are
# source seconds of a take mapped with T(take, t).
J = start("0364") + 0.45          # the zoom-through rides across the 0359 -> 0364 join and lands here
HOOK = ('<div style="position:absolute;left:0;right:0;top:1080px;text-align:center;'
        'text-shadow:0 6px 30px rgba(0,0,0,.75)">'
        '<div style="font:800 96px Unbounded;color:#FFD84D;letter-spacing:-1px">AFTER EFFECTS</div>'
        '<div style="font:700 66px Manrope;color:#fff;margin-top:6px">больше не нужен</div></div>')
SEG = [
    ("04_frame_break", start("0342"), dict(start=T("0342", 6.60), dur=0.6, handle="@islam.devai",
                                           caption="After Effects больше не нужен",
                                           _title=(HOOK, T("0342", 6.45)))),
    ("08_headline_wall", start("0343"), dict(start=T("0343", 5.75), every=0.20, person_scale=1.0,
        spots=[(200, 440), (800, 420), (190, 760), (820, 760), (545, 330), (200, 1080), (820, 1060), (545, 560)],
        headlines=["Ищем монтажёра на рилсы", "Правки опять не те", "Монтаж ролика: 5 дней", "Эффекты — отдельно",
                   "Монтажёр не отвечает", "Публикацию снова сдвинули", "Кто смонтирует к пятнице?", "Переделать субтитры"])),
    ("01_orbit", start("0344"), dict(start=T("0344", 1.75), items=[TH[i] for i in (1, 2, 5, 6, 8, 9, 10)], title_y=255,
                                     title=[("твои ролики", T("0344", 3.05), "s"), ("вокруг тебя", T("0344", 4.40), "b")])),
    ("17_glass_type", start("0346"), dict(_tag_y=1240, word="ГЛАВНОЕ", appear=T("0346", 1.90), cy=300, size=150, depth=14)),
    ("15_vertigo", start("0348"), dict(src_size=(1620, 2880), person_zoom=1.12, start=T("0348", 1.50), dur=2.2,
                                       fg_bottom=1780, text_y=1380, text=("КАК В КИНО", T("0348", 3.04)))),
    ("16_cover_story", start("0349"), dict(mast_text="МОНТАЖ", mast=T("0349", 2.25), kick=T("0349", 2.50),
        kicker="МОНТАЖ · ВЫПУСК № 18", issue="ОКТЯБРЬ 2026", bar=T("0349", 3.90), ink="#1d1a16",
        lines=[("Обложка", "Ты — на обложке журнала", T("0349", 3.20), 60, 1150),
               ("Разбор", "17 эффектов без монтажёра", T("0349", 3.60), 660, 1000)])),
    ("12_green_screen", start("0351"), dict(swap=T("0351", 3.22), flood=T("0351", 3.29), every=0.10, cap=T("0351", 3.34),
        person_scale=0.80, caption='без <span>зелёной ткани</span>',
        questions=["Сделай рилс", "Добавь субтитры", "Сделай обложку", "Убери паузы", "Наложи эффекты", "Сделай рилс",
                   "Переведи на английский"],
        names=["Монтаж", "Субтитры", "Обложка", "Звук", "Эффекты"],
        colors=["#5B3DF5", "#FF8A3D", "#2BB673", "#E5484D", "#1E9BD7"])),
    ("14_doodle_boil", start("0352"), dict(trace=T("0352", 1.12), words=[("оживают!", T("0352", 2.10), (-0.15, 2.2))],
        doodles=[("spark", T("0352", 1.2), (-1.1, 0.0), 30, (1.0, 1.0, 1.0)), ("bolt", T("0352", 1.6), (1.2, 0.45), 70, (0.34, 0.85, 1.0)),
                 ("star", T("0352", 1.9), (1.25, -0.2), 40, (0.34, 0.85, 1.0)), ("doc", T("0352", 2.3), (-1.25, 1.2), 72, (1.0, 1.0, 1.0))])),
    ("13_paper_cut", start("0354"), dict(person_scale=0.84, lines_y=1060, letter_dt=0.05, circle=T("0354", 3.45),
                                         lines=[("ИЛИ", T("0354", 1.75)), ("КОЛЛАЖ", T("0354", 2.85))])),
    ("02_couch_wall", start("0355"), dict(start=T("0355", 1.30), every=0.05, tiles=TH, words_y=1130,
        notes=["гайд №18", "17 эффектов", "без монтажёра", "один телефон"],
        words=[("стена за спиной", T("0355", 1.60), "s"), ("твоими роликами", T("0355", 3.10), "b")])),
    ("05_digital_zoom", start("0356"), dict(src_size=(1620, 2880), word_y=1060,
        beats=[(T("0356", 1.55), 1.0, "наезд"), (T("0356", 2.47), 1.25, "на каждое"), (T("0356", 3.58), 1.5, "слово")])),
    ("10_chart_grow", start("0358"), dict(grid=T("0358", 0.75), labels=["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"],
        values=[0.10, 0.14, 0.12, 0.30, 0.45, 0.72, 1.0],
        times=[T("0358", t) for t in (0.95, 1.20, 1.45, 1.75, 2.05, 2.35, 2.60)], tag=T("0358", 2.75), tag_text="×3 ↗",
        box=(130, 280, 930, 640), person_scale=1.0)),
    ("09_zoom_through", start("0359"), dict(cut=start("0364"), into=0.40, out=0.45, zmax=4.0,
        text=[("ПРОЛЕТАЕМ СКВОЗЬ КАДР", T("0359", 1.10), T("0359", 2.95))])),
    ("03_ui_world", J, dict(split=T("0364", 3.00), tag=T("0364", 3.55), type=T("0364", 3.65), cmd="/монтаж собери рилс",
        files=[("исходник", "MOV", "#E5484D", T("0364", 3.10)), ("голос", "WAV", "#2BB673", T("0364", 3.25)),
               ("эффекты", "FX", "#5B6CFF", T("0364", 3.40))],
        results=[("вырезал паузы", T("0364", 4.30)), ("наложил эффекты", T("0364", 4.70)), ("свёл звук", T("0364", 5.10))])),
    ("07_checklist", start("0365"), dict(enter=T("0365", 1.70), title="МОНТАЖ ДЕЛАЕТ СЕБЯ САМ", items=[
        ("Субтитры", T("0365", 1.95), T("0365", 2.35)), ("Звук", T("0365", 2.55), T("0365", 2.95)),
        ("Обложка", T("0365", 3.00), T("0365", 3.45)), ("Монтаж", T("0365", 4.40), T("0365", 5.10))])),
    ("11_pull_back", start("0366"), dict(hold=0.60, pull=1.10, file="рилс.mov", counter=(T("0366", 4.90), T("0366", 7.70)),
        steps=[("Расшифровал речь", T("0366", 5.00)), ("Убрал паузы", T("0366", 5.60)), ("Наложил голос", T("0366", 6.20)),
               ("Поставил эффекты", T("0366", 6.80)), ("Собрал ролик", T("0366", 7.60))])),
    ("06_phone_mockup", start("0368"), dict(enter=T("0368", 4.40), chat="Islam Dev AI", tap=T("0368", 8.40), tap_xy=(100, 290),
        msgs=[dict(t=T("0368", 6.60), html='<b>Гайд №18: 17 эффектов</b>Как сделать такие эффекты в своих роликах.'
                    '<div class=btns><div class=bt id=tapbtn>Открыть</div><div class="bt g">Позже</div></div>'),
              dict(t=T("0368", 8.70), html='<span class=ok>✓ Гайд открыт</span><br>Шаг 1: сними 17 коротких дублей.')])),
]
NO_TR = {J}                        # no zoom-blur where the zoom-through lands: it is already decelerating there
SEAT = {s: [x[3] for x in TAKES if T(x[0], x[1]) <= s + 1e-6][-1] for _, s, _ in SEG}
FG = {"A": 1780, "B": 1650}        # rows below: table / laptop / cup in front of him
NAMES = {"08_headline_wall": "стена заголовков", "15_vertigo": "головокружение", "11_pull_back": "отъезд в редактор",
         "01_orbit": "орбита", "03_ui_world": "мир интерфейса", "14_doodle_boil": "живые каракули",
         "07_checklist": "чек-лист", "09_zoom_through": "переход сквозь кадр", "16_cover_story": "обложка журнала",
         "05_digital_zoom": "цифровой наезд", "13_paper_cut": "бумажная аппликация", "12_green_screen": "замена фона",
         "17_glass_type": "стеклянный текст", "04_frame_break": "выход из рамки", "06_phone_mockup": "телефон рядом",
         "02_couch_wall": "стена контента", "10_chart_grow": "растущий график"}
FG_BOTTOM = [1780]


def _with_table(fn):
    def wrapped(clip, *a, **k):
        ms = fn(clip, *a, **k)
        if not TABLE[0]:
            return ms
        h = ms[0].shape[0]
        ramp = np.clip((np.arange(h, dtype=np.float32) - FG_BOTTOM[0] * h / H) / (40 * h / H) + 0.5, 0, 1)[:, None]
        return [np.maximum(m, ramp) for m in ms]
    return wrapped


TABLE = [True]
NO_TABLE = {"13_paper_cut"}   # the paper cut-out is him alone
fxlib.person_mattes = _with_table(fxlib.person_mattes)
TR = 4   # frames on each side of a boundary that get the zoom-blur transition


def tag(n, name, y=230):
    return (f'<div style="position:absolute;left:48px;top:{y}px;padding:12px 24px;border-radius:40px;'
            f'background:rgba(10,10,12,.55);color:#fff;font:600 30px Manrope;backdrop-filter:blur(8px)">'
            f'<b style="font-family:Unbounded;font-weight:700;color:#FFD84D">{n:02d}</b>&nbsp; {name}</div>')


def seg_frames(k, html, tags):
    name, a, cfg = SEG[k]
    b = SEG[k + 1][1] if k + 1 < len(SEG) else END
    fa, fb = round(a * FPS), round(b * FPS)
    cfg = dict(cfg)
    cfg.pop("_tag_y", None)
    title = cfg.pop("_title", None)
    tstill = html.still(title[0]) if title else None
    big = cfg.pop("src_size", None)
    clip = Clip(TIGHT, fa / FPS, fb / FPS, size=big or (W, H))
    mod = importlib.import_module(f"effects.{name}")
    TABLE[0] = name not in NO_TABLE
    FG_BOTTOM[0] = FG[SEAT[a]]
    n = 0
    for f in mod.frames(clip, html, t0=fa / FPS, **cfg):
        if n >= fb - fa:
            break
        over(f, tags[k], opacity=min(1.0, (n + 1) / 6) * (1 - prog(n, 33, 42)))   # tag shows ~1.2 s
        if tstill is not None:
            t = (fa + n) / FPS
            over(f, tstill, opacity=min(1.0, (n + 1) / 4) * (1 - prog(t, title[1] - 0.25, title[1])))
        yield f
        n += 1
    while n < fb - fa:                      # never let a segment come up short: hold its last frame
        yield f
        n += 1


def blur_tr(f, s):
    """s in (0, 1]: zoom-blur strength at a boundary."""
    z = 1 + 0.10 * s
    return radial_blur(zoom_frame(f, z, W / 2, H * 0.4), 0.22 * s, W / 2, H * 0.4, steps=8)


def splice(dirty, html, old):
    """Re-render only the dirty segments; every other frame is copied from the previous full render
    (its boundary blurs come with it). A dirty segment gets its own in/out blur."""
    tags = [html.still(tag(int(s[0][:2]), NAMES[s[0]], s[2].get("_tag_y", 230))) for s in SEG]
    for k, (name, a, _) in enumerate(SEG):
        b = SEG[k + 1][1] if k + 1 < len(SEG) else END
        fa, fb = round(a * FPS), round(b * FPS)
        if k not in dirty:
            src = Clip(old, fa / FPS, fb / FPS)
            for i in range(fb - fa):
                yield src.frame(min(i, len(src) - 1))
            continue
        fr = list(seg_frames(k, html, tags))
        if k > 0 and a not in NO_TR:
            for i in range(TR):
                fr[i] = blur_tr(fr[i], ease_out(1 - i / TR))
        if k + 1 < len(SEG) and SEG[k + 1][1] not in NO_TR:
            for q in range(TR):
                fr[-TR + q] = blur_tr(fr[-TR + q], ease_in((q + 1) / (TR + 1)))
        print("rendered", k, name, flush=True)
        yield from fr


def frames(seg_ids, html):
    tags = [html.still(tag(int(s[0][:2]), NAMES[s[0]], s[2].get("_tag_y", 230))) for s in SEG]
    buf = collections.deque()
    for j, k in enumerate(seg_ids):
        for i, f in enumerate(seg_frames(k, html, tags)):
            if i < TR and j > 0 and SEG[k][1] not in NO_TR:   # coming out of the boundary
                f = blur_tr(f, ease_out(1 - i / TR))
            buf.append(f)
            if len(buf) > TR:
                yield buf.popleft()
        if j + 1 < len(seg_ids) and SEG[seg_ids[j + 1]][1] not in NO_TR:   # going into the boundary
            for q in range(len(buf)):
                buf[q] = blur_tr(buf[q], ease_in((q + 1) / (TR + 1)))
        while buf:
            yield buf.popleft()


def write(frames_it, out, audio=None, t0=0.0, t1=None):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if audio:
        cmd += ["-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", audio, "-map", "0:v", "-map", "1:a",
                "-af", "highpass=f=70,acompressor=threshold=-20dB:ratio=2.5,loudnorm=I=-14:TP=-1.5", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in frames_it:
        p.stdin.write((np.clip(f, 0, 1) * 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", nargs="*", type=int)
    ap.add_argument("--out", default=f"{HERE}/work/video.mp4")
    ap.add_argument("--splice", nargs="+", type=int, help="re-render only these segments, copy the rest from --old")
    ap.add_argument("--old", default=f"{HERE}/work/video.mp4")
    args = ap.parse_args()
    os.chdir(os.path.join(HERE, "..", "tools", "fx"))
    with Html() as html:
        if args.preview is not None:
            for k in args.preview or range(len(SEG)):
                fr = list(seg_frames(k, html, [html.still(tag(int(s[0][:2]), NAMES[s[0]], s[2].get("_tag_y", 230))) for s in SEG]))
                idx = np.linspace(0, len(fr) - 1, 6).astype(int)
                sheet = np.hstack([cv2.resize(fr[i], (360, 640)) for i in idx])
                p = f"{HERE}/work/pv{k:02d}-{SEG[k][0]}.jpg"
                cv2.imwrite(p, (np.clip(sheet, 0, 1) * 255).astype(np.uint8)); print(p, flush=True)
        elif args.splice:
            write(splice(set(args.splice), html, args.old), args.out, None, 0, END)
            print(args.out)
        else:
            write(frames(range(len(SEG)), html), args.out, VOICE if os.path.exists(VOICE) else None, 0, END)
            print(args.out)
