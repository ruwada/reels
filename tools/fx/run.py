"""Render one effect (or all) as a demo clip.

  python3 tools/fx/run.py 01_orbit [--src VIDEO] [--out DIR] [--no-label] [--preview]

Each effect lives in tools/fx/effects/NN_name.py and exposes
  NAME_EN, NAME_RU          for the demo tag
  DEMO = dict(t0=..., t1=..., **settings)   default segment of the source + settings
  frames(clip, html, **settings) -> iterator of float BGR frames (one per clip frame)
Settings carry absolute word times (seconds in the source), so a template is reused by
changing DEMO-like settings for another reel.
--preview writes a contact sheet of 6 frames instead of the full clip.
"""
import argparse, importlib, sys, os, pathlib, time
import numpy as np, cv2

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fxlib
from fxlib import Clip, Html, write_video, over, label

EFFECTS = sorted(p.stem for p in (pathlib.Path(__file__).parent / "effects").glob("[0-9][0-9]_*.py"))


def run(name, src, outdir, with_label=True, preview=False, settings=None):
    mod = importlib.import_module(f"effects.{name}")
    cfg = dict(mod.DEMO)
    cfg.update(settings or {})
    t0, t1 = cfg.pop("t0"), cfg.pop("t1")
    big = cfg.pop("src_size", None)
    clip = Clip(src, t0, t1, size=big or (fxlib.W, fxlib.H))
    n = int(name[:2])
    with Html() as html:
        tag = html.still(label(n, mod.NAME_EN, mod.NAME_RU)) if with_label else None
        gen = mod.frames(clip, html, t0=t0, **cfg)

        def labelled():
            for i, f in enumerate(gen):
                if tag is not None:
                    over(f, tag, opacity=min(1.0, i / 6))
                yield f

        if preview:
            idx = set(np.linspace(0, len(clip) - 1, 6).astype(int))
            shots = [cv2.resize(f, (360, 640)) for i, f in enumerate(labelled()) if i in idx]
            sheet = np.hstack(shots)
            p = os.path.join(outdir, f"{name}-preview.jpg")
            cv2.imwrite(p, (np.clip(sheet, 0, 1) * 255).astype(np.uint8))
            return p
        out = os.path.join(outdir, f"{name}.mp4")
        return write_video(labelled(), out, audio=(src, t0, t1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("effect", help="e.g. 01_orbit, or 'all'")
    ap.add_argument("--src", default="/tmp/fx/src1080.mp4")
    ap.add_argument("--out", default="/tmp/fx/out")
    ap.add_argument("--no-label", action="store_true")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    names = EFFECTS if a.effect == "all" else [e for e in EFFECTS if e.startswith(a.effect)]
    for nm in names:
        t = time.time()
        print(nm, "->", run(nm, a.src, a.out, not a.no_label, a.preview), f"{time.time() - t:.0f}s", flush=True)
