"""15 vertigo: dolly zoom. The speaker keeps his size while the room behind him slides away (background
zooms out, he stays put), like Hitchcock's Vertigo. Person is cut from the 4K source, the room is a
clean plate with him painted out, so the background can move on its own. Reference: @tenfoldmarc 15/17."""
import numpy as np, cv2
from fxlib import (Clip, person_mattes, head_track, clean_plate, over, radial_blur, vignette, prog, ease_in_out,
                   lerp, FPS, W, H)

NAME_EN, NAME_RU = "vertigo", "головокружение (долли-зум)"
DEMO = dict(t0=65.90, t1=68.00, src_size=(1620, 2880), person_zoom=1.30, start=66.00, dur=1.6,
            text=("ОСТАЁТСЯ ЗА ЧЕЛОВЕКОМ", 67.15))


def frames(clip, html, t0, person_zoom, start, dur, text, fg_bottom=None, text_y=1330):
    """fg_bottom: rows below this y (output px) move with him, e.g. a table and cup in front of him."""
    big = clip.size[0] / W
    small = Clip(clip.path, clip.t0, clip.t1)
    mattes = person_mattes(small)
    if fg_bottom:
        ramp = np.clip((np.arange(H, dtype=np.float32) - fg_bottom) / 40 + 0.5, 0, 1)[:, None]
        mattes = [np.maximum(m, ramp) for m in mattes]
    heads = head_track(mattes)
    hx, hy, hw = np.median(np.array(heads), axis=0)
    fx, fy = hx, hy + 0.9 * hw
    css = ("body{display:flex;align-items:center;justify-content:center;height:100vh;color:#fff;"
           "font:700 40px Manrope;letter-spacing:.38em;text-shadow:0 3px 16px rgba(0,0,0,.7)}")
    timg = html.still(text[0], css, size=(W, 120))

    def place(img, z, src_scale):
        s = z / src_scale
        M = np.float32([[s, 0, fx - s * fx * src_scale], [0, s, fy - s * fy * src_scale]])
        return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    prevB = person_zoom
    for i in range(len(clip)):
        t = t0 + i / FPS
        k = ease_in_out(prog(t, start, start + dur))
        B = lerp(person_zoom, 1.0, k)                # background: from his zoom back to the original framing
        sf = small.frame(i)
        plate = clean_plate(sf, mattes[i])
        bg = place(plate, B, 1.0)
        speed = abs(prevB - B) * FPS
        prevB = B
        bg = radial_blur(bg, 0.05 * speed, fx, fy, steps=6)
        bg = vignette(bg, 0.25 + 0.25 * k)
        person = place(clip.frame(i), person_zoom, big)
        m = place(mattes[i], person_zoom, 1.0)
        out = bg * (1 - m[..., None]) + person * m[..., None]
        if t >= text[1]:
            over(out, timg, 0, text_y, opacity=prog(t, text[1], text[1] + 0.3))
        yield out
