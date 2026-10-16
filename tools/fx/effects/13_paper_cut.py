"""13 paper cut: the speaker becomes a paper cut-out (thick white torn border, drop shadow) on a scrapbook
page with pencil scribbles, a torn yellow patch and red marks; ransom-note letters land one by one and
get circled. The border and letters "boil" at 10 fps like stop-motion. Reference: @tenfoldmarc 13/17."""
import random
import numpy as np, cv2
from fxlib import person_mattes, over, transform, with_alpha, prog, ease_out_back, lerp, FPS, W, H

NAME_EN, NAME_RU = "paper cut", "бумажная аппликация"
DEMO = dict(t0=28.30, t1=30.50, person_scale=0.86,
            lines=[("ТОЛЬКО", 29.26), ("СЛОЖНОЕ", 29.70)], letter_dt=0.06, circle=30.18)

PALETTE = [("#1F3FBF", "#fff"), ("#fff", "#111"), ("#111", "#fff"), ("#C8102E", "#fff"), ("#FFF3C4", "#111"),
           ("#E8E2D0", "#8A1020")]
FONTS = ["900 112px 'Playfair Display'", "800 100px Unbounded", "800 110px Manrope", "700 120px Caveat",
         "italic 900 112px 'Playfair Display'"]


def page(seed=1):
    rnd = np.random.default_rng(seed)
    bg = np.ones((H, W, 3), np.float32) * np.array([0.93, 0.96, 0.98], np.float32)  # BGR off-white
    for y in range(0, H, 46):
        cv2.line(bg, (0, y), (W, y), (0.86, 0.80, 0.72), 1, cv2.LINE_AA)
    for x in range(0, W, 46):
        cv2.line(bg, (x, 0), (x, H), (0.90, 0.86, 0.80), 1, cv2.LINE_AA)
    # torn yellow paper patch
    pts = [(560, 820), (1080, 760), (1080, 1180), (620, 1240)]
    poly = []
    for a, b in zip(pts, pts[1:] + pts[:1]):
        for s in np.linspace(0, 1, 30, endpoint=False):
            poly.append((a[0] + (b[0] - a[0]) * s + rnd.normal(0, 4), a[1] + (b[1] - a[1]) * s + rnd.normal(0, 4)))
    cv2.fillPoly(bg, [np.int32(poly)], (0.45, 0.93, 0.99), cv2.LINE_AA)
    # pencil scribble blocks
    for (x0, y0, x1, y1, col) in ((40, 240, 640, 560, (0.85, 0.62, 0.45)), (700, 880, 1040, 1100, (0.25, 0.25, 0.3)),
                                  (760, 1300, 1000, 1500, (0.55, 0.35, 0.95))):
        x, up = x0, True
        while x < x1:
            nx = x + rnd.uniform(8, 16)
            cv2.line(bg, (int(x), int(y1 if up else y0) + int(rnd.normal(0, 10))),
                     (int(nx), int(y0 if up else y1) + int(rnd.normal(0, 10))), col, 2, cv2.LINE_AA)
            x, up = nx, not up
    for (x, y) in ((90, 640), (130, 700), (900, 1180), (950, 1230)):  # red x marks
        cv2.line(bg, (x - 16, y - 16), (x + 16, y + 16), (0.2, 0.15, 0.85), 4, cv2.LINE_AA)
        cv2.line(bg, (x + 16, y - 16), (x - 16, y + 16), (0.2, 0.15, 0.85), 4, cv2.LINE_AA)
    for k in range(4):  # loops
        cx = 820 + k * 40
        cv2.ellipse(bg, (cx, 1640), (22, 26), 0, 0, 330, (0.25, 0.25, 0.3), 3, cv2.LINE_AA)
    g = rnd.normal(0, 0.018, (H, W, 1)).astype(np.float32)
    return np.clip(bg + g, 0, 1)


def letter(html, ch, j, rnd):
    bgc, fg = PALETTE[rnd.randrange(len(PALETTE))]
    font = FONTS[rnd.randrange(len(FONTS))]
    return html.still(f'<div style="background:{bgc};color:{fg};font:{font};line-height:1;padding:10px 14px 16px;'
                      f'box-shadow:2px 3px 0 rgba(0,0,0,.18)">{ch}</div>',
                      "body{display:flex;align-items:center;justify-content:center;height:100vh}", size=(200, 220))


def frames(clip, html, t0, person_scale, lines, letter_dt, circle):
    rnd = random.Random(5)
    bg = page()
    tiles = []
    for li, (word, ts) in enumerate(lines):
        n = len(word)
        for j, ch in enumerate(word):
            x = W / 2 - 40 + (j - (n - 1) / 2) * 112
            y = 330 + li * 160
            tiles.append((letter(html, ch, j, rnd), x, y, rnd.uniform(-9, 9), ts + j * letter_dt))
    mattes = person_mattes(clip)
    for i in range(len(clip)):
        t = t0 + i / FPS
        step = i // 3                                   # 10 fps "boil"
        r = np.random.default_rng(step)
        f = clip.frame(i)
        m = mattes[i]
        # paper border: grow the matte, roughen its edge with noise that changes every boil step
        hard = (m > 0.5).astype(np.uint8)
        grown = cv2.dilate(hard, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (34, 34))).astype(np.float32)
        noise = cv2.resize(r.random((H // 24, W // 24)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        border = (cv2.GaussianBlur(grown, (0, 0), 6) + (noise - 0.5) * 0.5 > 0.5).astype(np.float32)
        border = np.maximum(border, m)
        cut = np.dstack([f * m[..., None] + np.float32([0.97, 0.98, 0.99]) * (1 - m[..., None]), border])
        cut = transform(cut, person_scale, 0, cx=W / 2, cy=H, tx=W / 2 + r.normal(0, 1.5), ty=H + r.normal(0, 1.5))
        out = bg.copy()
        sh = cv2.GaussianBlur(cut[..., 3], (0, 0), 10)
        sh = np.roll(np.roll(sh, 12, 0), 8, 1) * 0.35
        out *= (1 - sh[..., None])
        over(out, cut)
        for img, x, y, ang, ts in tiles:
            k = prog(t, ts, ts + 0.12)
            if k <= 0:
                continue
            jitter = r.normal(0, 1.2)
            over(out, transform(img, lerp(1.6, 1.0, ease_out_back(k)) * 0.84, ang + jitter, tx=x, ty=y))
        if t >= circle:  # red marker circle drawn on around the letters
            p = min(1, (t - circle) / 0.3)
            cv2.ellipse(out, (W // 2 - 40, 410), (450, 175), -3 + r.normal(0, 0.6), 200, 200 + 360 * p, (0.18, 0.1, 0.85), 7,
                        cv2.LINE_AA)
        yield out
