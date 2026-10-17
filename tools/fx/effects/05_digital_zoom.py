"""05 digital zoom: hard punch-ins on the beat words (crop from the 4K source, so no quality loss),
with a two-frame zoom blur on each snap and a big word under the face. Reference: @tenfoldmarc 05/17."""
import numpy as np, cv2
from fxlib import (Clip, person_mattes, head_track, over, radial_blur, prog, ease_out, lerp, FPS, W, H)

NAME_EN, NAME_RU = "digital zoom", "цифровой зум"
DEMO = dict(t0=32.25, t1=36.95, src_size=(1620, 2880),
            # time, zoom (1 = original framing), word shown from that moment
            beats=[(32.25, 1.0, "раньше:"), (32.78, 1.0, "ручная обработка"), (33.82, 1.3, "заявок"),
                   (34.22, 1.55, "переписка"), (35.37, 1.0, "составление"), (36.01, 1.35, "счетов"),
                   (36.37, 1.7, "отчёты")],
            word_y=1290)


def frames(clip, html, t0, beats, word_y):
    big = clip.size[0] / W                       # source resolution relative to output
    small = Clip(clip.path, clip.t0, clip.t1)    # 1080 copy only for face tracking
    heads = head_track(person_mattes(small))
    css = ("body{display:flex;align-items:center;justify-content:center;height:100vh;"
           "font:900 100px/1.05 Unbounded;letter-spacing:-.02em;color:#fff;text-shadow:0 6px 26px rgba(0,0,0,.6)}"
           "span{color:#FFD84D}")
    words = {}
    for _, _, w in beats:
        if w and w not in words:
            parts = w.split()
            words[w] = html.still('<div style="text-align:center;max-width:980px">' + " ".join(parts[:-1]) +
                                  (" " if len(parts) > 1 else "") + f"<span>{parts[-1]}</span></div>", css, size=(W, 260))
    for i in range(len(clip)):
        t = t0 + i / FPS
        cur = [b for b in beats if b[0] <= t] or [beats[0]]
        prev = beats[max(0, len(cur) - 2)]
        bt, z1, word = cur[-1]
        z0 = prev[1]
        k = ease_out(prog(t, bt, bt + 0.12), 4)
        z = lerp(z0, z1, k) * (1 + 0.012 * (t - bt))          # snap, then a slow creep
        hx, hy, hw = heads[min(i, len(heads) - 1)]
        fx, fy = hx, hy + 0.9 * hw                            # zoom towards the face
        f = clip.frame(i)                                     # big frame
        s = z / big
        M = np.float32([[s, 0, W / 2 - s * fx * big], [0, s, H * 0.42 - s * fy * big]])
        # keep the frame covered: clamp translation
        M[0, 2] = np.clip(M[0, 2], W - s * f.shape[1], 0)
        M[1, 2] = np.clip(M[1, 2], H - s * f.shape[0], 0)
        out = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
        if 0 < t - bt < 0.1 and z1 != z0:
            out = radial_blur(out, 0.06 * (1 - (t - bt) / 0.1), W / 2, H * 0.42)
        if word:
            over(out, words[word], 0, word_y - 130)
        yield out
