"""04 frame break: the shot shrinks into a reel-style frame on a dark blurred backdrop, and the speaker
breaks OUT of it: his head and hands spill over the frame edges. Reference: @tenfoldmarc 04/17."""
import numpy as np, cv2
from fxlib import (person_mattes, head_track, over, rounded_mask, zoom_frame, prog, ease_in_out, lerp, FPS, W, H)

NAME_EN, NAME_RU = "frame break", "выход из рамки"
DEMO = dict(t0=62.00, t1=65.30, start=62.15, dur=0.8, handle="@islam.devai",
            caption="Всё, что повторяется по схеме, — системе")

UI_CSS = """body{width:%dpx;height:%dpx;position:relative;font-family:Manrope;color:#fff}
.ic{position:absolute;right:26px;width:58px;height:58px}
.b{position:absolute;left:30px;bottom:44px;right:110px}
.h{display:flex;align-items:center;gap:14px;font:700 28px Manrope}
.av{width:52px;height:52px;border-radius:50%%;background:linear-gradient(135deg,#FFD84D,#FF6A4D)}
.fl{padding:6px 16px;border:2px solid rgba(255,255,255,.8);border-radius:10px;font:700 22px Manrope}
.c{margin-top:12px;font:500 24px/1.3 Manrope;opacity:.92}
.bar{position:absolute;left:0;right:0;bottom:0;height:5px;background:rgba(255,255,255,.3)}
.bar i{display:block;height:100%%;width:38%%;background:#fff}
"""

ICON = {  # simple stroked icons as inline SVG
    "heart": '<path d="M29 50 C10 36 6 26 10 18 C14 10 24 9 29 17 C34 9 44 10 48 18 C52 26 48 36 29 50Z"/>',
    "chat": '<path d="M12 14 H46 V40 H26 L16 48 V40 H12Z"/>',
    "send": '<path d="M8 28 L50 10 L36 50 L28 32Z M28 32 L50 10"/>',
}


def ui_overlay(html, w, h, handle, caption):
    icons = "".join(
        f'<svg class=ic style="bottom:{300 - j * 100}px" viewBox="0 0 58 58" fill="none" stroke="#fff" stroke-width="4" '
        f'stroke-linejoin="round">{ICON[n]}</svg>' for j, n in enumerate(("heart", "chat", "send")))
    body = (f'{icons}<div class=b><div class=h><span class=av></span>{handle}<span class=fl>Подписаться</span></div>'
            f'<div class=c>{caption}</div></div><div class=bar><i></i></div>')
    return html.still(body, UI_CSS % (w, h), size=(w, h))


def frames(clip, html, t0, start, dur, handle, caption):
    mattes = person_mattes(clip)
    heads = head_track(mattes)
    hx, hy, hw = np.median(np.array(heads), axis=0)
    top = int(hy + 1.25 * hw * 0.84)                      # the frame's top edge crosses the face: the head breaks out
    fw = 640
    fh = int(min(H - 300 - top, fw * 16 / 9 * 0.9))
    x0 = int(np.clip(hx - fw / 2, 60, W - 130 - fw))
    final = np.array([x0, top, x0 + fw, top + fh], float)
    ui = ui_overlay(html, fw, fh, handle, caption)
    for i in range(len(clip)):
        t = t0 + i / FPS
        f = clip.frame(i)
        m = mattes[i]
        k = ease_in_out(prog(t, start, start + dur))
        if k <= 0:
            yield f
            continue
        vs = lerp(1, 0.84, k)                      # the shot itself shrinks a little, anchored at the face
        f = zoom_frame(f, vs, hx, hy)
        m = cv2.warpAffine(m, np.float32([[vs, 0, hx - vs * hx], [0, vs, hy - vs * hy]]), (W, H))
        X0, Y0, X1, Y1 = (np.array([0, 0, W, H], float) * (1 - k) + final * k).astype(int)
        bg = cv2.GaussianBlur(cv2.resize(f, (W // 4, H // 4)), (0, 0), 6)
        bg = cv2.resize(bg, (W, H)) * lerp(1, 0.32, k)
        rm = np.zeros((H, W), np.float32)
        rm[Y0:Y1, X0:X1] = rounded_mask(X1 - X0, Y1 - Y0, int(lerp(0, 34, k)))
        inside = rm[..., None]
        out = bg * (1 - inside) + f * inside
        # thin frame border + reel UI fade in
        edge = cv2.dilate(rm, np.ones((5, 5), np.uint8)) - rm
        out = out * (1 - edge[..., None] * 0.5 * k) + edge[..., None] * 0.5 * k
        if k > 0.6:
            over(out, cv2.resize(ui, (X1 - X0, Y1 - Y0)), X0, Y0, opacity=(k - 0.6) / 0.4)
        # the break-out: person pixels OUTSIDE the frame go on top, with a soft shadow on the backdrop
        outside = m * (1 - rm) * k
        outside[Y1 - 30:] = 0                      # only the top and sides break out, never below the frame
        sh = cv2.GaussianBlur(outside, (0, 0), 14)
        sh = np.roll(sh, 14, axis=0) * 0.5 * (1 - m)
        out = out * (1 - sh[..., None])
        out = out * (1 - outside[..., None]) + f * outside[..., None]
        yield out
