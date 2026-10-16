"""Shared toolkit for the 17 reel effects (tools/fx/effects/*.py).

Pieces:
  Clip          frames of a source video segment as float32 BGR arrays
  person_mattes per-frame person matte (u2net_human_seg + guided filter + temporal smoothing), cached
  Html          headless Chromium: render HTML to RGBA stills or animated frames (window.seek(t))
  over / warp   compositing helpers, perspective warps, easing curves
  write_video   pipes frames to ffmpeg and muxes the source audio of the same segment

Everything works on 1080x1920 at 30 fps. Run tools/fx/setup.sh once in a fresh container.
"""
import os, subprocess, hashlib, json, math, tempfile, pathlib
import numpy as np
import cv2

W, H, FPS = 1080, 1920, 30
HERE = pathlib.Path(__file__).resolve().parent
MODELS = pathlib.Path(os.environ.get("FX_MODELS", "/tmp/fx/models"))
CACHE = pathlib.Path(os.environ.get("FX_CACHE", "/tmp/fx/cache"))
CHROME = os.environ.get("FX_CHROME", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
INTER = "/usr/share/fonts/opentype/inter/"


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def prog(t, a, b):
    """0..1 progress of t inside [a, b]."""
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)

def ease_out(x, p=3):
    return 1 - (1 - clamp(x)) ** p

def ease_in(x, p=3):
    return clamp(x) ** p

def ease_in_out(x):
    x = clamp(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def ease_out_back(x, s=1.70158):
    x = clamp(x) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2

def spring(x, freq=4.5, damp=6.0):
    """Damped spring 0 -> 1 with overshoot."""
    x = max(0.0, x)
    return 1 - math.exp(-damp * x) * math.cos(freq * 2 * math.pi * x * 0.5)

def lerp(a, b, x):
    return a + (b - a) * x


# ---------------------------------------------------------------- video in/out
class Clip:
    """Decoded segment [t0, t1) of a video, resized to `size` (w, h), float32 BGR 0..1."""

    def __init__(self, path, t0, t1, size=(W, H)):
        self.path, self.t0, self.t1, self.size = str(path), t0, t1, size
        w, h = size
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", self.path,
               "-vf", f"scale={w}:{h}:flags=lanczos,fps={FPS}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
        raw = subprocess.run(cmd, capture_output=True, check=True).stdout
        n = len(raw) // (w * h * 3)
        self.u8 = np.frombuffer(raw, np.uint8)[: n * w * h * 3].reshape(n, h, w, 3)
        self.n = n

    def __len__(self):
        return self.n

    def frame(self, i):
        return self.u8[min(i, self.n - 1)].astype(np.float32) / 255.0


def write_video(frames, out, audio=None, crf=16):
    """frames: iterable of float32 BGR 0..1 (H, W, 3). audio: (path, t0, t1) or None."""
    out = str(out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-"]
    if audio:
        p, a0, a1 = audio
        cmd += ["-ss", f"{a0:.3f}", "-t", f"{a1 - a0:.3f}", "-i", str(p), "-map", "0:v", "-map", "1:a",
                "-c:a", "aac", "-b:a", "192k", "-af", "afade=t=in:d=0.05,areverse,afade=t=in:d=0.08,areverse"]
    cmd += ["-c:v", "libx264", "-crf", str(crf), "-preset", "medium", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-shortest", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in frames:
        proc.stdin.write((np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError("ffmpeg failed")
    return out


# ---------------------------------------------------------------- person matte
_SESS = None

def _u2net():
    global _SESS
    if _SESS is None:
        import onnxruntime as ort
        _SESS = ort.InferenceSession(str(MODELS / "u2net_human_seg.onnx"), providers=["CPUExecutionProvider"])
    return _SESS

def guided_filter(I, p, r=8, eps=1e-4):
    mean = lambda x: cv2.boxFilter(x, -1, (2 * r + 1, 2 * r + 1))
    mI, mp_ = mean(I), mean(p)
    a = (mean(I * p) - mI * mp_) / (mean(I * I) - mI * mI + eps)
    b = mp_ - a * mI
    return mean(a) * I + mean(b)

def matte_frame(bgr):
    """bgr float32 (h, w, 3) -> matte float32 (h, w) 0..1."""
    h, w = bgr.shape[:2]
    rgb = cv2.cvtColor(cv2.resize(bgr, (320, 320), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
    x = (rgb - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    s = _u2net()
    o = s.run(None, {s.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    o = (o - o.min()) / max(1e-6, o.max() - o.min())
    m = cv2.resize(o.astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    small = (w // 2, h // 2)
    gm = guided_filter(cv2.resize(g, small), cv2.resize(m, small), r=6, eps=2e-4)
    m = cv2.resize(gm, (w, h), interpolation=cv2.INTER_LINEAR)
    return np.clip((m - 0.08) / 0.84, 0, 1).astype(np.float32)

def person_mattes(clip):
    """List of mattes for every frame of `clip`. Cached per source frame on disk, so any segment that
    overlaps an earlier one reuses its mattes."""
    ph = hashlib.md5(f"{os.path.abspath(clip.path)}|{clip.size}".encode()).hexdigest()[:10]
    d = CACHE / f"matte-{ph}"
    d.mkdir(parents=True, exist_ok=True)
    base = int(round(clip.t0 * FPS))
    out, prev = [], None
    for i in range(len(clip)):
        f = d / f"{base + i:06d}.png"
        if f.exists():
            m = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
        else:
            m = matte_frame(clip.frame(i))
            if prev is not None:  # light temporal smoothing kills edge flicker
                m = 0.65 * m + 0.35 * prev
            cv2.imwrite(str(f), (m * 255).astype(np.uint8))
        prev = m
        out.append(m)
    return out


def clean_plate(bgr, matte, grow=40):
    """Background with the person painted out (rough, meant to sit behind the person or under blur)."""
    m = (cv2.dilate((matte > 0.2).astype(np.uint8), np.ones((grow, grow), np.uint8)) * 255)
    sw, sh = W // 4, H // 4
    small = cv2.inpaint((cv2.resize(bgr, (sw, sh)) * 255).astype(np.uint8), cv2.resize(m, (sw, sh)), 9, cv2.INPAINT_TELEA)
    fill = cv2.GaussianBlur(cv2.resize(small, (bgr.shape[1], bgr.shape[0])).astype(np.float32) / 255, (0, 0), 6)
    a = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 8)[..., None]
    return bgr * (1 - a) + fill * a


# ---------------------------------------------------------------- compositing
def over(dst, rgba, x=0, y=0, opacity=1.0):
    """Alpha-composite rgba (h, w, 4 float BGRA 0..1, straight alpha) onto dst at (x, y), in place."""
    h, w = rgba.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x0 >= x1 or y0 >= y1:
        return dst
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = src[..., 3:4] * opacity
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + src[..., :3] * a
    return dst

def with_alpha(bgr, a):
    return np.dstack([bgr, a])

def transform(rgba, scale=1.0, angle=0.0, cx=None, cy=None, tx=0.0, ty=0.0, size=(W, H)):
    """Scale/rotate rgba about its (cx, cy) and place that point at (tx, ty) on a canvas of `size`."""
    h, w = rgba.shape[:2]
    cx = w / 2 if cx is None else cx
    cy = h / 2 if cy is None else cy
    M = cv2.getRotationMatrix2D((cx, cy), angle, scale)
    M[0, 2] += tx - cx
    M[1, 2] += ty - cy
    return cv2.warpAffine(rgba, M, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

def warp_quad(rgba, quad, size=(W, H)):
    """Map the full rgba rectangle onto quad [(x,y) tl, tr, br, bl] on a canvas."""
    h, w = rgba.shape[:2]
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(quad))
    return cv2.warpPerspective(rgba, M, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

def card_quad(cx, cy, w, h, ry=0.0, rx=0.0, rz=0.0, persp=2200.0):
    """Corners of a w x h card centred at (cx, cy), rotated in 3D (degrees), with perspective."""
    pts = np.array([[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]], float)
    a, b, c = map(math.radians, (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    p = pts @ (Rz @ Ry @ Rx).T
    k = persp / (persp + p[:, 2])
    return [(cx + x * s, cy + y * s) for (x, y, _), s in zip(p, k)]

def zoom_frame(bgr, scale, cx=W / 2, cy=H / 2):
    """Digital zoom: magnify around (cx, cy) keeping that point fixed."""
    M = np.float32([[scale, 0, cx - scale * cx], [0, scale, cy - scale * cy]])
    return cv2.warpAffine(bgr, M, (bgr.shape[1], bgr.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def radial_blur(bgr, amount, cx=W / 2, cy=H / 2, steps=8):
    """Zoom blur: average of progressively magnified copies."""
    if amount <= 0.002:
        return bgr
    acc = np.zeros_like(bgr)
    for i in range(steps):
        acc += zoom_frame(bgr, 1 + amount * i / (steps - 1), cx, cy)
    return acc / steps

def shadow(rgba, blur=30, opacity=0.45, dx=0, dy=20):
    """Drop shadow layer (same size) for an rgba layer."""
    a = cv2.GaussianBlur(rgba[..., 3], (0, 0), blur) * opacity
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    a = cv2.warpAffine(a, M, (a.shape[1], a.shape[0]))
    return np.dstack([np.zeros(a.shape + (3,), np.float32), a])

def rounded_mask(w, h, r):
    m = np.zeros((h, w), np.uint8)
    cv2.rectangle(m, (r, 0), (w - r, h), 255, -1)
    cv2.rectangle(m, (0, r), (w, h - r), 255, -1)
    for x, y in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)):
        cv2.circle(m, (x, y), r, 255, -1, cv2.LINE_AA)
    return cv2.GaussianBlur(m, (3, 3), 0).astype(np.float32) / 255

def vignette(bgr, strength=0.35):
    yy, xx = np.mgrid[0:bgr.shape[0], 0:bgr.shape[1]].astype(np.float32)
    d = np.sqrt(((xx - bgr.shape[1] / 2) / bgr.shape[1]) ** 2 + ((yy - bgr.shape[0] / 2) / bgr.shape[0]) ** 2)
    return bgr * (1 - strength * np.clip(d * 1.6, 0, 1) ** 2)[..., None]

def grain(bgr, amount=0.025, seed=0):
    rng = np.random.default_rng(seed)
    return bgr + rng.normal(0, amount, bgr.shape[:2] + (1,)).astype(np.float32)


# ---------------------------------------------------------------- HTML (Chromium) rendering
GF = open(HERE / "fonts/gf/fonts.css").read().replace("@@FX@@", "file://" + str(HERE))
FONT_CSS = f"""
@font-face{{font-family:Unbounded;src:url(file://{HERE}/fonts/unbounded-cyr.woff2) format('woff2');font-weight:200 900;unicode-range:U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}}
@font-face{{font-family:Unbounded;src:url(file://{HERE}/fonts/unbounded-lat.woff2) format('woff2');font-weight:200 900;unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}}
@font-face{{font-family:Manrope;src:url(file://{HERE}/fonts/manrope-cyr.woff2) format('woff2');font-weight:200 800;unicode-range:U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}}
@font-face{{font-family:Manrope;src:url(file://{HERE}/fonts/manrope-lat.woff2) format('woff2');font-weight:200 800;unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}}
@font-face{{font-family:Inter;src:local('Inter')}}
{GF}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:transparent;-webkit-font-smoothing:antialiased}}
"""

class Html:
    """with Html() as h: rgba = h.still(body_html, css, size=(w, h)); for rgba in h.frames(..., times)."""

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._b = self._pw.chromium.launch(executable_path=CHROME, args=["--allow-file-access-from-files"])
        self._tmp = tempfile.mkdtemp(prefix="fxhtml-")
        return self

    def __exit__(self, *a):
        self._b.close()
        self._pw.stop()

    def _page(self, body, css, size, js="", scale=1):
        w, h = size
        p = self._b.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
        f = os.path.join(self._tmp, hashlib.md5((body + css + js).encode()).hexdigest() + ".html")
        open(f, "w").write(f"<!doctype html><html><head><meta charset=utf-8><style>{FONT_CSS}{css}</style></head>"
                           f"<body>{body}<script>{js}</script></body></html>")
        p.goto("file://" + f)
        p.evaluate("document.fonts.ready")
        p.wait_for_timeout(60)
        return p

    @staticmethod
    def _shot(p):
        png = p.screenshot(omit_background=True, type="png")
        a = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
        return a  # BGRA, straight alpha

    def still(self, body, css="", size=(W, H), scale=1):
        p = self._page(body, css, size, scale=scale)
        try:
            return self._shot(p)
        finally:
            p.close()

    def frames(self, body, css, js, times, size=(W, H), scale=1):
        """js must define window.seek = t => {...}; yields one rgba per time (size * scale pixels)."""
        p = self._page(body, css, size, js, scale=scale)
        try:
            for t in times:
                p.evaluate(f"window.seek({t:.4f})")
                yield self._shot(p)
        finally:
            p.close()


def label(n, name_en, name_ru):
    """Small top-left tag used on demo clips: '07 · checklist · чек-лист'."""
    return (f'<div style="position:absolute;left:48px;top:150px;padding:14px 26px;border-radius:40px;'
            f'background:rgba(10,10,12,.62);color:#fff;font:600 30px Manrope;letter-spacing:.02em;'
            f'backdrop-filter:blur(8px)"><b style="font-family:Unbounded;font-weight:700;color:#FFD84D">{n:02d}</b>'
            f'&nbsp; {name_en} <span style="opacity:.6">· {name_ru}</span></div>')


def head_track(mattes, smooth=0.8):
    """Per-frame (x_centre, y_top, head_width) of the head from person mattes, smoothed."""
    out, prev = [], None
    for m in mattes:
        rows = np.where(m.max(axis=1) > 0.5)[0]
        if len(rows):
            y = rows[0]
            band = m[y:y + 220]
            cols = band.sum(axis=0)
            x = float((cols * np.arange(m.shape[1])).sum() / max(cols.sum(), 1e-6))
            wid = float((m[min(y + 110, m.shape[0] - 1)] > 0.5).sum())
            cur = np.array([x, float(y), wid])
        else:
            cur = prev if prev is not None else np.array([W / 2, H * 0.25, 260.0])
        prev = cur if prev is None else smooth * prev + (1 - smooth) * cur
        out.append(prev.copy())
    return out


def person_over(bg, frame, matte):
    """Put the person from `frame` (matte) on top of `bg`."""
    a = matte[..., None]
    return bg * (1 - a) + frame * a


def frost(frame, alpha, blur=22):
    """Frosted-glass: blur the frame wherever an overlay's alpha is set (CSS backdrop-filter can't see the video)."""
    a = (alpha > 0.5).astype(np.float32)
    a = cv2.GaussianBlur(a, (0, 0), 1.2)[..., None]
    small = cv2.GaussianBlur(cv2.resize(frame, (W // 3, H // 3)), (0, 0), blur / 3)
    return frame * (1 - a) + cv2.resize(small, (frame.shape[1], frame.shape[0]))[...] * a
