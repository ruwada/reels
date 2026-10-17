"""02 couch wall: the wall behind the speaker fills up, tile by tile, with screenshots of his content
(reels, slides, notes); he stays in front, cut out. Reference: @tenfoldmarc 02/17."""
import math, random
import numpy as np, cv2
from fxlib import person_mattes, over, transform, person_over, prog, ease_out, ease_out_back, lerp, FPS, W, H

NAME_EN, NAME_RU = "couch wall", "стена контента за спиной"
DEMO = dict(t0=0.10, t1=2.95, start=0.25, every=0.09,
            tiles=[f"/tmp/fx/thumbs/t{i:02d}.jpg" for i in (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12)],
            notes=["+1 менеджер", "+1 зарплата", "ещё задачи", "найм снова"],
            words=[("большинство компаний", 0.16, "s"), ("один путь", 1.96, "b")], words_y=1270)

CSS = "body{display:flex;align-items:center;justify-content:center;height:100vh}"


def tile(html, path=None, note=None):
    if path:
        body = (f'<div style="width:236px;height:420px;border-radius:18px;background:url(file://{path}) center/cover;'
                f'border:4px solid rgba(255,255,255,.9);box-shadow:0 14px 30px rgba(0,0,0,.5)"></div>')
    else:
        body = (f'<div style="width:236px;padding:26px 22px;border-radius:14px;background:#FFF8E8;color:#16120C;'
                f'font:700 34px/1.1 \'Playfair Display\';box-shadow:0 14px 30px rgba(0,0,0,.45)">{note}</div>')
    return html.still(body, CSS, size=(300, 480))


def words_img(html, parts):
    css = (CSS + "body{flex-direction:column;color:#fff;text-shadow:0 4px 18px rgba(0,0,0,.6);"
           "padding:0 130px 0 60px;box-sizing:border-box;text-align:center}"
           ".s{font:700 52px Manrope}.b{font:900 92px/1.05 Unbounded;letter-spacing:-.02em}")
    return [html.still("".join(f'<div class={c}>{t}</div>' for t, _, c in parts[:n]), css, size=(W, 300))
            for n in range(1, len(parts) + 1)]


def frames(clip, html, t0, start, every, tiles, notes, words, words_y, seed=7):
    rnd = random.Random(seed)
    imgs = [tile(html, path=p) for p in tiles] + [tile(html, note=n) for n in notes]
    # masonry slots: 4 columns, staggered rows, covering the whole background
    slots = []
    for c in range(4):
        y = -120 + (c % 2) * 190
        while y < H - 200:
            slots.append((140 + c * 268, y + 210))
            y += 450
    rnd.shuffle(slots)
    order = [(slots[j], imgs[j % len(imgs)], rnd.uniform(-5, 5)) for j in range(len(slots))]
    wimgs = words_img(html, words)
    mattes = person_mattes(clip)
    for i in range(len(clip)):
        t = t0 + i / FPS
        f = clip.frame(i)
        dim = ease_out(prog(t, start, start + 0.6))
        back = f * (1 - 0.45 * dim)
        for j, ((x, y), img, ang) in enumerate(order):
            ts = start + j * every
            k = prog(t, ts, ts + 0.28)
            if k <= 0:
                continue
            layer = transform(img, lerp(1.35, 1.0, ease_out_back(k)), ang, tx=x, ty=y)
            over(back, layer, opacity=min(1, k * 3))
        out = person_over(back, f, mattes[i])
        shown = [j for j, (_, ts, _) in enumerate(words) if t >= ts]
        if shown:
            over(out, wimgs[shown[-1]], 0, words_y - 150)
        yield out
