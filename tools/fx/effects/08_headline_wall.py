"""08 headline wall: paper notes and post cards with headlines SLAP onto the wall behind the speaker one by
one (overshoot + a tiny camera shake), building a collage; he stays in front. Reference: @tenfoldmarc 08/17."""
import random, math
import numpy as np, cv2
from fxlib import person_mattes, over, transform, with_alpha, clean_plate, shadow, prog, ease_out, lerp, FPS, W, H

NAME_EN, NAME_RU = "headline wall", "стена заголовков"

CSS = "body{display:flex;align-items:center;justify-content:center;height:100vh}"
STYLES = [
    "background:#FFF9EC;color:#17130D;font:700 44px/1.1 'Playfair Display';padding:26px 26px 30px;width:330px",
    "background:#fff;color:#14161B;font:600 28px/1.3 Manrope;padding:22px 24px;width:360px;border-radius:18px",
    "background:#16181D;color:#F2F2F2;font:700 38px/1.12 'Playfair Display';padding:26px;width:320px",
    "background:#FFE34D;color:#14161B;font:800 30px/1.15 Unbounded;padding:22px 24px;width:330px",
]


def note(html, text, style, kind):
    head = ('<div style="display:flex;gap:10px;align-items:center;margin-bottom:12px;font:700 20px Manrope;opacity:.6">'
            '<span style="width:34px;height:34px;border-radius:50%;background:#C9CED8"></span>пост · 2 ч</div>') if kind == 1 else ""
    return html.still(f'<div style="{style};box-shadow:0 2px 0 rgba(0,0,0,.08)">{head}{text}</div>', CSS, size=(460, 420))


DEMO = dict(t0=3.00, t1=5.25, start=3.10, every=0.17,
            headlines=["Ищем ещё одного менеджера", "Нужен администратор в чат — срочно",
                       "Опять найм", "Фонд зарплат вырос", "+3 вакансии за месяц",
                       "Кто будет отвечать клиентам?", "Онбординг нового сотрудника",
                       "Задач больше, людей не хватает", "Снова собеседования", "Команда растёт, прибыль — нет"])


def frames(clip, html, t0, start, every, headlines, person_scale=0.84, seed=3, spots=None):
    rnd = random.Random(seed)
    imgs = [note(html, h, STYLES[j % 4], j % 4) for j, h in enumerate(headlines)]
    spots = spots or [(205, 340), (545, 300), (880, 350), (190, 680), (890, 660), (210, 1010),
             (880, 1000), (190, 1330), (890, 1320), (545, 560)]
    cards = [(spots[j % len(spots)], imgs[j], rnd.uniform(-7, 7)) for j in range(len(imgs))]
    mattes = person_mattes(clip)
    for i in range(len(clip)):
        t = t0 + i / FPS
        f = clip.frame(i)
        k0 = ease_out(prog(t, start - 0.05, start + 0.35))
        ps = lerp(1.0, person_scale, k0)            # he steps back a little so the wall shows
        back = clean_plate(f, mattes[i]) * 0.75 if k0 > 0 else f.copy()
        shake = 0.0
        for j, ((x, y), img, ang) in enumerate(cards):
            ts = start + j * every
            k = prog(t, ts, ts + 0.16)
            if k <= 0:
                continue
            sc = lerp(1.7, 1.0, ease_out(k, 2))
            if t - ts < 0.22:
                shake = max(shake, 1 - (t - ts) / 0.22)
            layer = transform(img, sc * 0.98, ang, tx=x, ty=y)
            over(back, shadow(layer, blur=lerp(30, 10, k), opacity=0.5, dx=6, dy=lerp(40, 12, k)))
            over(back, layer, opacity=min(1, k * 2))
        out = back
        over(out, transform(with_alpha(f, mattes[i]), ps, 0, cx=W / 2, cy=H, tx=W / 2, ty=H))
        if shake > 0:
            dx, dy = 9 * shake * math.sin(t * 90), 7 * shake * math.cos(t * 77)
            out = cv2.warpAffine(out, np.float32([[1.01, 0, dx - 5.4], [0, 1.01, dy - 9.6]]), (W, H),
                                 borderMode=cv2.BORDER_REFLECT)
        yield out
