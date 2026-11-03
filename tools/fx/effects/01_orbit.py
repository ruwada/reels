"""01 orbit: cards (reel thumbnails, screenshots) circle the speaker at chest height, passing BEHIND him
and in front of him, plus an elegant serif title. Reference: @tenfoldmarc 01/17."""
import math
import numpy as np, cv2
from fxlib import person_mattes, head_track, over, transform, person_over, prog, ease_out, lerp, FPS, W, H

NAME_EN, NAME_RU = "orbit", "орбита"
DEMO = dict(t0=9.02, t1=11.50, start=9.10,
            items=[f"/tmp/fx/thumbs/t{i:02d}.jpg" for i in (2, 3, 6, 7, 10, 11, 12)],
            title=[("рутину забирают", 9.10, "s"), ("AI-агенты", 9.59, "b")], title_y=330)


def card(html, path):
    return html.still(
        f'<div style="width:220px;height:391px;border-radius:22px;border:5px solid rgba(255,255,255,.95);'
        f'background:url(file://{path}) center/cover;box-shadow:0 18px 40px rgba(0,0,0,.45)"></div>',
        "body{display:flex;align-items:center;justify-content:center;height:100vh}", size=(300, 470))


def title_img(html, parts):
    css = ("body{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;color:#FFF6E0;"
           "text-shadow:0 4px 22px rgba(0,0,0,.55)}.s{font:400 46px Manrope;letter-spacing:.01em}"
           ".b{font:italic 700 118px/1 'Playfair Display'}.st{font:400 54px Manrope;color:#FFE7A8}")
    out = []
    for n in range(1, len(parts) + 1):
        body = "".join(f'<div class={c}>{t}</div>' for t, _, c in parts[:n])
        if n == len(parts):
            body = body[:-6] + ' <span class=st>✦</span></div>'
        out.append(html.still(body, css, size=(W, 360)))
    return out


def frames(clip, html, t0, start, items, title, title_y, tilt=-6.0, speed=0.22):
    chips = [card(html, p) for p in items]
    titles = title_img(html, title)
    mattes = person_mattes(clip)
    heads = head_track(mattes)
    N = len(items)
    for i in range(len(clip)):
        t = t0 + i / FPS
        f = clip.frame(i)
        m = mattes[i]
        hx, hy, hw = heads[i]
        cx, cy = hx, hy + 2.9 * hw     # orbit at chest height
        rx, ry = 2.1 * hw, 0.42 * hw
        k = ease_out(prog(t, start, start + 0.9))
        if k <= 0:
            yield f
            continue
        back, front = f.copy(), []
        # orbit ring: thin ellipse, back half under the person, front half over
        ring_b = np.zeros((H, W, 4), np.float32)
        ring_f = np.zeros((H, W, 4), np.float32)
        for half, layer in ((0, ring_f), (1, ring_b)):  # sin>0 half is in front
            pts = []
            for a in np.linspace(math.pi * half, math.pi * (half + 1), 90):
                x, y = rx * k * math.cos(a), ry * k * math.sin(a)
                c, s = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
                pts.append((cx + x * c - y * s, cy + x * s + y * c))
            cv2.polylines(layer, [np.int32(pts)], False, (1, 1, 1, 0.55), 3, cv2.LINE_AA)
        over(back, ring_b)
        placed = []
        for j, cimg in enumerate(chips):
            a = (t - start) * speed * 2 * math.pi + 2 * math.pi * j / N
            depth = math.sin(a)                 # >0 = in front of the speaker
            x, y = rx * k * math.cos(a), ry * k * depth
            c, s = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
            px, py = cx + x * c - y * s, cy + x * s + y * c
            sc = lerp(0.5, 1.0, (depth + 1) / 2) * lerp(0.3, 1, k) * hw / 330
            placed.append((depth, px, py, sc, cimg))
        for depth, px, py, sc, cimg in sorted(placed, key=lambda p: p[0]):
            layer = transform(cimg, sc, 0, tx=px, ty=py)
            if depth < 0:
                layer[..., :3] *= lerp(0.75, 1, depth + 1)
                over(back, layer, opacity=lerp(0.7, 1, depth + 1))
            else:
                front.append(layer)
        shown = [j for j, (_, ts, _) in enumerate(title) if t >= ts]
        if shown:                       # title sits on the wall, behind the speaker
            a = ease_out(prog(t, title[0][1], title[0][1] + 0.4))
            over(back, titles[shown[-1]], 0, title_y - 180 + 30 * (1 - a), opacity=a)
        out = person_over(back, f, m)
        over(out, ring_f)
        for layer in front:
            over(out, layer)
        yield out
