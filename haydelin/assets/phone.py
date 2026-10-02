#!/usr/bin/env python3
"""Haydelin v2: app screens shown at native quality inside a phone frame over Pexels B-roll (no zooms).

    python3 phone.py WORK_DIR REEL_DIR

WORK_DIR holds screen.mp4 (iPhone screen recording) and gfx/*.png (redrawn screens, 1080x2337 or 1170x2532);
REEL_DIR is the reel folder with broll/. Writes WORK_DIR/p_<name>.mp4, each 1080x1920.
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter

WORK, REEL = sys.argv[1], sys.argv[2]
SW, SH = 540, 1168          # screen inside the phone (iPhone ratio 1170x2532)
BZ = 16                     # bezel
PW, PH = SW + 2 * BZ, SH + 2 * BZ
TOP = 210
X = {"left": 70, "right": 1080 - 70 - PW, "center": (1080 - PW) // 2}


def run(a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def frame_assets():
    """Phone body with a soft shadow (drawn under the screen) and a rounded mask for the screen."""
    pad = 60
    body = Image.new("RGBA", (PW + 2 * pad, PH + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("L", body.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((pad + 6, pad + 24, pad + PW + 6, pad + PH + 24), 78, fill=150)
    body.putalpha(sh.filter(ImageFilter.GaussianBlur(26)))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle((pad, pad, pad + PW, pad + PH), 78, fill=(18, 20, 22, 255), outline=(70, 76, 80, 255), width=3)
    body.save(f"{WORK}/phone_body.png")
    m = Image.new("L", (SW, SH), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, SW, SH), 62, fill=255)
    m.save(f"{WORK}/phone_mask.png")
    isl = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    ImageDraw.Draw(isl).rounded_rectangle((SW // 2 - 62, 14, SW // 2 + 62, 50), 18, fill=(0, 0, 0, 255))
    isl.save(f"{WORK}/phone_island.png")
    return pad


SCALE = f"scale={SW}:{SH}:flags=lanczos,setsar=1"


def piece(out, p):
    """One screen piece, SW x SH, 30 fps."""
    kind, dur = p[0], p[-1]
    if kind == "rec":            # ("rec", t0, speed, dur)
        _, t0, speed, _ = p
        run(["-ss", str(t0), "-t", f"{dur * speed:.3f}", "-i", f"{WORK}/screen.mp4", "-an", "-vf",
             f"setpts=PTS/{speed},fps=30,{SCALE},format=yuv420p", "-t", f"{dur:.3f}", "-c:v", "libx264", "-crf", "12", out])
    elif kind == "still":        # ("still", png, dur)
        run(["-loop", "1", "-framerate", "30", "-t", f"{dur:.3f}", "-i", f"{WORK}/gfx/{p[1]}", "-vf",
             f"{SCALE},format=yuv420p", "-c:v", "libx264", "-crf", "12", out])
    elif kind == "notif":        # ("notif", lock_bg, notif, at, dur): banner drops in from the top
        _, bg, n, at, _ = p
        run(["-loop", "1", "-framerate", "30", "-t", f"{dur:.3f}", "-i", f"{WORK}/gfx/{bg}",
             "-loop", "1", "-framerate", "30", "-t", f"{dur:.3f}", "-i", f"{WORK}/gfx/{n}", "-filter_complex",
             f"[0:v]{SCALE}[b];[1:v]{SCALE},format=rgba,fade=in:st={at}:d=0.2:alpha=1[n];"
             f"[b][n]overlay=x=0:y='if(lt(t,{at}),-300,-300*pow(max(0,1-(t-{at})/0.35),3))':eval=frame,format=yuv420p",
             "-c:v", "libx264", "-crf", "12", out])
    elif kind == "toggle":       # ("toggle", off, on, at, dur): switches flip on
        _, off, on, at, _ = p
        run(["-loop", "1", "-framerate", "30", "-t", f"{dur:.3f}", "-i", f"{WORK}/gfx/{off}",
             "-loop", "1", "-framerate", "30", "-t", f"{dur:.3f}", "-i", f"{WORK}/gfx/{on}", "-filter_complex",
             f"[0:v]{SCALE}[a];[1:v]{SCALE},format=rgba,fade=in:st={at}:d=0.25:alpha=1[b];[a][b]overlay,format=yuv420p",
             "-c:v", "libx264", "-crf", "12", out])


def composite(name, pieces, bg, bg_from, pos, pad):
    parts = []
    for i, p in enumerate(pieces):
        f = f"{WORK}/pc_{name}_{i}.mp4"; piece(f, p); parts.append(f)
    lst = f"{WORK}/pc_{name}.txt"
    open(lst, "w").write("".join(f"file '{f}'\n" for f in parts))
    scr = f"{WORK}/pc_{name}.mp4"
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", scr])
    dur = sum(p[-1] for p in pieces)
    x0 = X[pos]
    # entrance: the phone slides in from its own side (from below when centred); no scaling at any point
    if pos == "center":
        xe, ye = f"{x0 - pad}", f"'{TOP - pad}+700*pow(max(0,1-t/0.32),3)'"
    else:
        sgn = -1 if pos == "left" else 1
        xe, ye = f"'{x0 - pad}+{sgn * 760}*pow(max(0,1-t/0.32),3)'", f"{TOP - pad}"
    if bg.endswith(".png"):
        bgin = ["-loop", "1", "-framerate", "30", "-t", f"{dur:.3f}", "-i", bg]
        bgf = "scale=1080:1920,setsar=1"
    else:
        bgin = ["-ss", str(bg_from), "-t", f"{dur:.3f}", "-i", bg]
        bgf = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,"
               "eq=brightness=-0.07:saturation=0.9,vignette=angle=PI/4")
    fc = (f"[0:v]{bgf},trim=duration={dur:.3f},setpts=PTS-STARTPTS[bg];"
          f"[2:v]format=gray[m];[1:v]format=rgba[s0];[s0][m]alphamerge[s1];[s1][3:v]overlay[s];"
          f"[4:v]format=rgba[body];[body][s]overlay={pad + BZ}:{pad + BZ}[ph];"
          f"[bg][ph]overlay=x={xe}:y={ye}:eval=frame,format=yuv420p")
    run([*bgin, "-i", scr, "-loop", "1", "-i", f"{WORK}/phone_mask.png", "-loop", "1", "-i", f"{WORK}/phone_island.png",
         "-loop", "1", "-i", f"{WORK}/phone_body.png", "-filter_complex", fc, "-t", f"{dur:.3f}", "-r", "30",
         "-c:v", "libx264", "-crf", "14", "-preset", "medium", f"{WORK}/p_{name}.mp4"])
    print("built", name, round(dur, 2))


B = lambda i: f"{REEL}/broll/{i}.mp4"
PLAN = [
    # name, pieces, background, bg offset, phone position
    ("dev",    [("still", "role.png", 2.3)],                                   B(8266177), 3.0, "left"),
    ("alarm",  [("rec", 90.2, 1, 1.0), ("notif", "lock_child_bg.png", "n_child.png", 0.15, 1.0)], B(6322929), 2.0, "right"),
    ("start",  [("rec", 134.8, 1, 1.35), ("rec", 138.5, 1, 4.4)],               B(6762988), 4.0, "left"),
    ("timer",  [("rec", 139.0, 27, 4.45)],                                      B(6630297), 8.0, "right"),
    ("modes",  [("toggle", "tyagi_off.png", "tyagi_on.png", 1.0, 5.1)],         B(32810110), 2.0, "center"),
    ("coins",  [("rec", 267.3, 1, 2.6), ("rec", 270.4, 1, 3.7)],                B(8103766), 0.5, "left"),
    ("parent", [("rec", 309.3, 1, 2.0), ("notif", "lock_parent_bg.png", "n_parent.png", 0.3, 4.2)], B(7614368), 6.0, "right"),
    ("priv",   [("still", "priv.png", 4.85)],                                   f"{WORK}/gfx/bg_priv.png", 0, "center"),
    ("both",   [("still", "home.png", 1.75)],                                   B(6762988), 18.0, "left"),
]

if __name__ == "__main__":
    pad = frame_assets()
    only = sys.argv[3:] or [p[0] for p in PLAN]
    for name, pieces, bg, frm, pos in PLAN:
        if name in only:
            composite(name, pieces, bg, frm, pos, pad)
