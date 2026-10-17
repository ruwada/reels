"""09 zoom-through cut: the camera rushes INTO the shot (accelerating zoom + zoom blur) and comes out of
the blur in the next shot, decelerating. Works on any cut; if `cut` is None the hardest cut in the segment
is found automatically. Reference: @tenfoldmarc 09/17."""
import numpy as np, cv2
from fxlib import (person_mattes, head_track, over, zoom_frame, radial_blur, prog, ease_in, ease_out, lerp, FPS, W, H)

NAME_EN, NAME_RU = "zoom-through cut", "переход сквозь кадр"
DEMO = dict(t0=5.20, t1=8.55, cut=None, into=0.32, out=0.40, zmax=5.0,
            text=[("НО ЕСТЬ ДРУГОЙ СПОСОБ", 5.27, 6.6), ("МАСШТАБИРУЙ СИСТЕМУ", 7.35, 8.6)])


def find_cut(clip):
    d = [np.abs(clip.u8[i + 1, ::8, ::8].astype(np.int16) - clip.u8[i, ::8, ::8]).mean() for i in range(len(clip) - 1)]
    return int(np.argmax(d)) + 1


def frames(clip, html, t0, cut, into, out, zmax, text):
    css = ("body{display:flex;align-items:center;justify-content:center;height:100vh;color:#fff;"
           "font:600 40px Manrope;letter-spacing:.42em;text-shadow:0 3px 14px rgba(0,0,0,.6)}")
    timgs = [html.still(s, css, size=(W, 120)) for s, _, _ in text]
    ci = find_cut(clip) if cut is None else int(round((cut - t0) * FPS))
    heads = head_track(person_mattes(clip))
    for i in range(len(clip)):
        t = t0 + i / FPS
        f = clip.frame(i)
        hx, hy, hw = heads[i]
        px, py = hx, hy + 0.8 * hw                       # rush towards the face
        if i < ci:
            k = ease_in(prog(i, ci - into * FPS, ci), 3)
            z = lerp(1, zmax, k)
            o = radial_blur(zoom_frame(f, z, px, py), 0.35 * k, px, py, steps=10)
            o = o * (1 - 0.25 * k)
        else:
            k = 1 - ease_out(prog(i, ci, ci + out * FPS), 3)
            z = lerp(1, zmax * 0.55, k)
            o = radial_blur(zoom_frame(f, z, px, py), 0.35 * k, px, py, steps=10)
            o = o * (1 - 0.25 * k)
        for img, (_, a, b) in zip(timgs, text):
            if a <= t < b:
                fade = min(prog(t, a, a + 0.25), 1 - prog(t, b - 0.2, b))
                over(o, img, 0, 1240, opacity=fade)
        yield o
