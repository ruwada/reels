"""17 glass type: a huge word made of thick clear glass stands on the wall behind the speaker: it refracts
and blurs the room behind it, has an extruded edge, a specular highlight and a rim; slight 3D turn,
he stays in front. Reference: @tenfoldmarc 17/17."""
import numpy as np, cv2
from fxlib import person_mattes, warp_quad, card_quad, person_over, prog, ease_out, lerp, FPS, W, H

NAME_EN, NAME_RU = "glass type", "стеклянный текст"
DEMO = dict(t0=46.20, t1=48.05, word="ВРУЧНУЮ", appear=46.30, cy=430, size=190, depth=16)


def glass(bg, mask, depth=16, light=(-0.6, -0.8)):
    """Render glass letters given by `mask` (H, W float) over `bg`."""
    a = mask[..., None]
    out = bg.copy()
    # extruded side: stacked offsets, darker toward the back
    for d in range(depth, 0, -2):
        sm = np.roll(np.roll(mask, d, 0), d // 2, 1)[..., None] * (1 - a)
        shade = 0.55 + 0.25 * (1 - d / depth)
        side = cv2.GaussianBlur(bg, (0, 0), 6) * shade + 0.08
        out = out * (1 - sm * 0.85) + side * sm * 0.85
    # face: refraction through a bevelled surface
    hgt = cv2.GaussianBlur(mask, (0, 0), 9)
    gy, gx = np.gradient(hgt)
    gx, gy = gx * 260, gy * 260
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    refr = cv2.remap(bg, xx + gx * 2.2, yy + gy * 2.2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    refr = cv2.GaussianBlur(refr, (0, 0), 3.5)
    face = refr * 1.10 + np.float32([0.05, 0.04, 0.02])                # cool, a bit brighter
    nlen = np.sqrt(gx ** 2 + gy ** 2 + 1)
    lam = np.clip((-gx * light[0] - gy * light[1]) / nlen, 0, 1)        # lit bevel
    face += (lam ** 2 * 0.65)[..., None]
    rim = np.clip(mask - cv2.erode(mask, np.ones((5, 5), np.uint8)), 0, 1)
    face += rim[..., None] * 0.45
    out = out * (1 - a) + face * a
    # soft shadow on the wall
    sh = cv2.GaussianBlur(np.roll(mask, 26, 0), (0, 0), 16)[..., None] * (1 - a) * 0.35
    return out * (1 - sh)


def frames(clip, html, t0, word, appear, cy, size, depth):
    css = ("body{display:flex;align-items:center;justify-content:center;height:100vh}"
           f"div{{font:900 {size}px/1 Unbounded;color:#fff;letter-spacing:-.02em;white-space:nowrap}}")
    txt = html.still(f"<div>{word}</div>", css, size=(1400, size + 120))
    mattes = person_mattes(clip)
    tw = txt.shape[1]
    for i in range(len(clip)):
        t = t0 + i / FPS
        f = clip.frame(i)
        k = ease_out(prog(t, appear, appear + 0.6))
        if k <= 0:
            yield f
            continue
        sc = min(1.0, (W - 60) / tw * 1.08)
        q = card_quad(W / 2, cy + 60 * (1 - k), tw * sc, txt.shape[0] * sc, ry=lerp(-28, -14, k) + 2 * (t - appear),
                      rx=8)
        mask = warp_quad(txt, q)[..., 3] * k
        back = glass(f, mask, depth)
        yield person_over(back, f, mattes[i])
