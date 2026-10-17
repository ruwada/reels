"""14 doodle boil: a hand-drawn white outline traces the speaker and little marker doodles draw themselves
in on cue; every line is redrawn with fresh wobble every 3 frames ("line boil", like hand animation).
Reference: @tenfoldmarc 14/17."""
import math
import numpy as np, cv2
from fxlib import person_mattes, head_track, over, transform, prog, ease_out, FPS, W, H

NAME_EN, NAME_RU = "doodle boil", "живые каракули"

PINK, YELLOW, WHITE = (0.72, 0.45, 1.0), (0.35, 0.88, 1.0), (1.0, 1.0, 1.0)  # BGR


def shape(name):
    """Polylines in a unit box (-1..1)."""
    if name == "crown":
        return [[(-1, .6), (-1, -.5), (-.5, .05), (0, -.8), (.5, .05), (1, -.5), (1, .6), (-1, .6)]]
    if name == "arrow_up":
        return [[(-.6, .9), (-.5, .3), (-.2, -.1), (.2, -.5), (.5, -.85)], [(.05, -.9), (.5, -.85), (.45, -.4)]]
    if name == "star":
        pts = []
        for k in range(11):
            r = 1 if k % 2 == 0 else .42
            a = -math.pi / 2 + k * math.pi / 5
            pts.append((r * math.cos(a), r * math.sin(a)))
        return [pts]
    if name == "spark":
        return [[(0, -1), (0, 1)], [(-1, 0), (1, 0)], [(-.55, -.55), (.55, .55)], [(-.55, .55), (.55, -.55)]]
    if name == "coin":
        return [[(math.cos(a), math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40)],
                [(-.2, .55), (-.2, -.55), (.25, -.55), (.4, -.3), (.25, -.05), (-.2, -.05)], [(-.45, .25), (.2, .25)]]
    if name == "bolt":
        return [[(.25, -1), (-.45, .1), (.05, .1), (-.25, 1), (.5, -.25), (0, -.25), (.25, -1)]]
    if name == "doc":
        return [[(-.6, -1), (.3, -1), (.7, -.6), (.7, 1), (-.6, 1), (-.6, -1)], [(.3, -1), (.3, -.6), (.7, -.6)],
                [(-.35, -.2), (.45, -.2)], [(-.35, .15), (.45, .15)], [(-.35, .5), (.2, .5)]]
    if name == "bell":
        return [[(-.75, .55), (-.55, .3), (-.55, -.25), (-.3, -.7), (0, -.82), (.3, -.7), (.55, -.25), (.55, .3),
                 (.75, .55), (-.75, .55)], [(-.18, .72), (0, .9), (.18, .72)], [(.85, -.75), (1.05, -.95)],
                [(-.85, -.75), (-1.05, -.95)]]
    if name == "cross":
        return [[(-1, -1), (1, 1)], [(1, -1), (-1, 1)]]
    raise KeyError(name)


def draw_lines(img, lines, cx, cy, s, color, width, frac, rng, wob=0.035):
    total = sum(len(l) - 1 for l in lines)
    budget = frac * total
    for l in lines:
        pts = np.array(l, np.float32)
        pts = pts + rng.normal(0, wob, pts.shape)               # the boil
        dense = []
        for a, b in zip(pts[:-1], pts[1:]):
            if budget <= 0:
                break
            u = min(1.0, budget)
            for v in np.linspace(0, u, 8):
                dense.append(a + (b - a) * v)
            budget -= 1
        if len(dense) > 1:
            p = np.int32([(cx + x * s, cy + y * s) for x, y in dense])
            cv2.polylines(img, [p], False, color + (1.0,), width, cv2.LINE_AA)


def outline(m, rng, grow=16):
    hard = (m > 0.5).astype(np.uint8)
    hard = cv2.dilate(hard, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (grow * 2, grow * 2)))
    cs, _ = cv2.findContours(hard, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return []
    c = max(cs, key=cv2.contourArea)[:, 0, :].astype(np.float32)
    c = c[:: max(1, len(c) // 260)]
    c = c + rng.normal(0, 2.2, c.shape)
    keep = (c[:, 0] > 6) & (c[:, 0] < W - 6) & (c[:, 1] < H - 6)  # drop the parts lying on the frame border
    segs, cur = [], []
    for p, k in zip(c, keep):
        if k:
            cur.append(p)
        elif len(cur) > 3:
            segs.append(np.array(cur)); cur = []
        else:
            cur = []
    if len(cur) > 3:
        segs.append(np.array(cur))
    return segs


DEMO = dict(t0=23.55, t1=25.65, trace=23.60,
            # doodle, appears, position relative to head (x in head widths, y in head widths from the head top)
            doodles=[("bolt", 23.66, (1.25, 0.55), 70, YELLOW), ("spark", 23.85, (-1.2, 0.1), 30, WHITE),
                     ("doc", 24.95, (-1.3, 1.25), 72, WHITE), ("star", 25.10, (1.35, -0.2), 40, YELLOW),
                     ("bell", 25.25, (1.3, 1.6), 66, PINK), ("spark", 25.40, (-0.9, -0.35), 24, WHITE)],
            words=[("мгновенно!", 23.70, (0.95, 1.35))])


def frames(clip, html, t0, trace, doodles, words, strike=()):
    css = ("body{display:flex;align-items:center;justify-content:center;height:100vh;font:700 90px Caveat;color:#FFB4E1;"
           "text-shadow:0 3px 0 #5a1840,0 0 18px rgba(0,0,0,.7)}")
    wimgs = [html.still(w, css, size=(640, 170)) for w, _, _ in words]
    mattes = person_mattes(clip)
    heads = head_track(mattes)
    for i in range(len(clip)):
        t = t0 + i / FPS
        rng = np.random.default_rng(i // 3)               # new wobble every 3 frames
        f = clip.frame(i)
        hx, hy, hw = heads[i]
        layer = np.zeros((H, W, 4), np.float32)
        frac = ease_out(prog(t, trace, trace + 0.7))
        for seg in outline(mattes[i], rng):
            n = max(2, int(len(seg) * frac))
            cv2.polylines(layer, [np.int32(seg[:n])], False, WHITE + (1.0,), 6, cv2.LINE_AA)
        for name, ts, (rx, ry), size, col in doodles:
            k = prog(t, ts, ts + 0.45)
            if k > 0:
                draw_lines(layer, shape(name), hx + rx * hw, hy + ry * hw, size * hw / 240, col, 6, k, rng)
        over(f, layer)
        top = np.zeros((H, W, 4), np.float32)
        for img, (w, ts, (rx, ry)) in zip(wimgs, words):
            if t >= ts:
                over(f, transform(img, 1 + 0.02 * rng.normal(), rng.normal(0, 1.5), tx=hx + rx * hw, ty=hy + ry * hw))
                if w in strike and t >= ts + 0.15:   # the word gets crossed out
                    draw_lines(top, shape("cross"), hx + rx * hw, hy + ry * hw, 60, PINK, 7,
                               prog(t, ts + 0.15, ts + 0.35), rng)
        over(f, top)
        yield f
