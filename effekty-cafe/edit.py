"""Reel «17 эффектов» from the cafe takes: one effect per phrase on the tight timeline (tight.py), soft
zoom-blur transitions at every boundary, voice = clone fitted to his lips (voice.py).
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
RANGES = [("main", 1.80, 7.20), ("main", 9.25, 20.35), ("main", 22.35, 28.60), ("main", 29.20, 32.65),
          ("main", 33.35, 34.15), ("main", 35.15, 37.30), ("main", 37.80, 40.15), ("t308", 7.60, 13.40)]


def T(take, t):
    """Source time of a take -> tight timeline."""
    acc = 0.0
    for tk, a, b in RANGES:
        d = (round(b * FPS) - round(a * FPS)) / FPS
        if tk == take and a <= t <= b:
            return round(acc + t - a, 3)
        acc += d
    raise ValueError((take, t))


TH = [f"/tmp/fx/thumbs/t{i:02d}.jpg" for i in (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12)]

# (effect, start, end, settings) on the tight timeline; ends are the next start
SEG = [
    ("08_headline_wall", 0.00, dict(start=0.08, every=0.16, person_scale=1.0,
        spots=[(200, 440), (790, 420), (190, 760), (800, 760), (545, 330), (200, 1080), (800, 1060), (545, 560),
               (200, 1290), (800, 1280)], headlines=[
        "Ищем монтажёра на рилсы", "Монтаж ролика: 5 дней", "Правки опять не те", "Монтажёр не отвечает",
        "Публикацию снова сдвинули", "Нужен моушн-дизайнер", "Кто смонтирует к пятнице?", "Переделать субтитры",
        "Ролик всё ещё в работе", "Эффекты стоят отдельно"])),
    ("15_vertigo", 2.95, dict(src_size=(1620, 2880), person_zoom=1.12, start=3.0, dur=1.7, text_y=1150,
                              text=("НЕ ВСТАВАЯ С КРЕСЛА", T("main", 5.63)))),
    ("11_pull_back", 5.40, dict(hold=0.55, pull=1.0, file="кофейня.mov", counter=(6.3, 10.1), steps=[
        ("Расшифровал речь", 6.7), ("Убрал паузы", 7.4), ("Озвучил под губы", 8.2), ("Подобрал эффекты", 9.0),
        ("Собрал ролик", 9.9)])),
    ("01_orbit", 10.30, dict(start=10.32, items=[TH[i] for i in (1, 2, 5, 6, 8, 9, 10)], title_y=255,
                             title=[("меняется", T("main", 15.6), "s"), ("много чего", T("main", 16.2), "b")])),
    ("03_ui_world", 13.20, dict(split=13.24, tag=13.95, type=14.05, cmd="/монтаж собери рилс", files=[
        ("кофейня", "MOV", "#E5484D", 13.40), ("голос", "WAV", "#2BB673", 13.55), ("эффекты", "FX", "#5B6CFF", 13.70)],
        results=[("вырезал паузы", 14.85), ("наложил эффекты", 15.35), ("свёл звук", 15.85)])),
    ("14_doodle_boil", T("main", 22.35), dict(trace=T("main", 22.40), words=[("сам по себе!", T("main", 24.22), (-0.15, 2.2))],
        doodles=[("spark", T("main", 22.5), (-1.1, 0.0), 30, (1.0, 1.0, 1.0)), ("bolt", T("main", 23.4), (1.2, 0.45), 70, (0.34, 0.85, 1.0)),
                 ("star", T("main", 23.9), (1.25, -0.2), 40, (0.34, 0.85, 1.0)), ("doc", T("main", 24.4), (-1.25, 1.2), 72, (1.0, 1.0, 1.0))])),
    ("07_checklist", T("main", 25.15), dict(enter=T("main", 25.18), title="МОНТАЖ ДЕЛАЕТ СЕБЯ САМ", items=[
        ("Субтитры", T("main", 25.25), T("main", 25.65)), ("Эффекты", T("main", 25.60), T("main", 26.05)),
        ("Звук", T("main", 26.00), T("main", 26.45)), ("Обложка", T("main", 26.35), T("main", 26.85))])),
    ("09_zoom_through", T("main", 27.05), dict(cut=T("main", 28.60) + 0.0001, into=0.40, out=0.45, zmax=4.0,
                                              text=[("ЧТОБЫ ВЫ ПОНЯЛИ ПРАВИЛЬНО", T("main", 27.20), T("main", 28.45))])),
    ("16_cover_story", T("main", 30.05), dict(mast_text="КОФЕ", mast=T("main", 30.10), kick=T("main", 30.40),
        kicker="МОНТАЖ · ВЫПУСК № 13", issue="ОКТЯБРЬ 2026", bar=T("main", 31.6), ink="#2A1A10",
        lines=[("Кейс", "Рилс без монтажёра", T("main", 30.6), 60, 1060),
               ("Разбор", "17 эффектов из одного дубля", T("main", 31.0), 660, 900)])),
    ("05_digital_zoom", 26.20, dict(src_size=(1620, 2880), word_y=1060,
                                   beats=[(26.20, 1.0, "а"), (T("main", 33.50), 1.45, "монтаж")])),
    ("13_paper_cut", 27.00, dict(person_scale=0.84, lines_y=1020, letter_dt=0.05, circle=T("main", 37.05),
                                lines=[("И", T("main", 35.30)), ("СТИЛЬ", T("main", 36.61))])),
    ("12_green_screen", 29.17, dict(swap=29.18, flood=29.25, every=0.10, cap=29.30, person_scale=0.80,
                                   caption='и <span>формат</span>',
                                   questions=["Сделай рилс", "Добавь субтитры", "Сделай обложку", "Убери паузы",
                                              "Наложи эффекты", "Сделай рилс", "Переведи на английский"],
                                   names=["Монтаж", "Субтитры", "Обложка", "Звук", "Эффекты"],
                                   colors=["#5B3DF5", "#FF8A3D", "#2BB673", "#E5484D", "#1E9BD7"])),
    ("17_glass_type", T("main", 39.05), dict(_tag_y=1240, word="МЕНЯЕТСЯ", appear=T("main", 39.08), cy=262, size=150, depth=14)),
    ("04_frame_break", 31.50, dict(start=31.55, dur=0.6, handle="@islam.devai", caption="Хочешь такой же ролик?")),
    ("06_phone_mockup", T("t308", 9.45), dict(enter=T("t308", 9.47), chat="Islam Dev AI", tap=T("t308", 10.9), tap_xy=(100, 290),
        msgs=[dict(t=T("t308", 9.7), html='<b>Гайд №13: 17 эффектов</b>Как сделать такой ролик без монтажёра.'
                    '<div class=btns><div class=bt id=tapbtn>Открыть</div><div class="bt g">Позже</div></div>'),
              dict(t=T("t308", 11.2), html='<span class=ok>✓ Гайд открыт</span><br>Шаг 1: снимите один дубль.')])),
    ("02_couch_wall", T("t308", 11.75), dict(start=T("t308", 11.78), every=0.05, tiles=TH, words_y=1130,
        notes=["гайд №13", "17 эффектов", "один дубль", "без монтажёра"],
        words=[("забирай в телеграме", T("t308", 11.82), "s"), ("ссылка в шапке", T("t308", 12.3), "b")])),
]
END = 37.30
NAMES = {"08_headline_wall": "стена заголовков", "15_vertigo": "головокружение", "11_pull_back": "отъезд в редактор",
         "01_orbit": "орбита", "03_ui_world": "мир интерфейса", "14_doodle_boil": "живые каракули",
         "07_checklist": "чек-лист", "09_zoom_through": "переход сквозь кадр", "16_cover_story": "обложка журнала",
         "05_digital_zoom": "цифровой наезд", "13_paper_cut": "бумажная аппликация", "12_green_screen": "замена фона",
         "17_glass_type": "стеклянный текст", "04_frame_break": "выход из рамки", "06_phone_mockup": "телефон рядом",
         "02_couch_wall": "стена контента"}
FG_BOTTOM = 1330   # rows below: the table and cup in front of him, treated as foreground


def _with_table(fn):
    def wrapped(clip, *a, **k):
        ms = fn(clip, *a, **k)
        if not TABLE[0]:
            return ms
        h = ms[0].shape[0]
        ramp = np.clip((np.arange(h, dtype=np.float32) - FG_BOTTOM * h / H) / (40 * h / H) + 0.5, 0, 1)[:, None]
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
    big = cfg.pop("src_size", None)
    clip = Clip(TIGHT, fa / FPS, fb / FPS, size=big or (W, H))
    mod = importlib.import_module(f"effects.{name}")
    TABLE[0] = name not in NO_TABLE
    n = 0
    for f in mod.frames(clip, html, t0=fa / FPS, **cfg):
        if n >= fb - fa:
            break
        over(f, tags[k], opacity=min(1.0, (n + 1) / 6) * (1 - prog(n, 33, 42)))   # tag shows ~1.2 s
        yield f
        n += 1
    while n < fb - fa:                      # never let a segment come up short: hold its last frame
        yield f
        n += 1


def blur_tr(f, s):
    """s in (0, 1]: zoom-blur strength at a boundary."""
    z = 1 + 0.10 * s
    return radial_blur(zoom_frame(f, z, W / 2, H * 0.4), 0.22 * s, W / 2, H * 0.4, steps=8)


def frames(seg_ids, html):
    tags = [html.still(tag(int(s[0][:2]), NAMES[s[0]], s[2].get("_tag_y", 230))) for s in SEG]
    buf = collections.deque()
    for j, k in enumerate(seg_ids):
        for i, f in enumerate(seg_frames(k, html, tags)):
            if i < TR and j > 0:                               # coming out of the boundary
                f = blur_tr(f, ease_out(1 - i / TR))
            buf.append(f)
            if len(buf) > TR:
                yield buf.popleft()
        if j + 1 < len(seg_ids):                               # going into the boundary
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
    ap.add_argument("--out", default=f"{HERE}/work/rils-effekty.mp4")
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
        else:
            write(frames(range(len(SEG)), html), args.out, VOICE, 0, END)
            print(args.out)
