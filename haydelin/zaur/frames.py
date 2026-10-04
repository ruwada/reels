# render an HTML animation (window.seek(t)) to an mp4: frames.py in.html out.mp4 seconds
import sys, os, subprocess, tempfile
from playwright.sync_api import sync_playwright
src, out, sec = sys.argv[1], sys.argv[2], float(sys.argv[3])
d = tempfile.mkdtemp()
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto("file://" + os.path.abspath(src)); pg.evaluate("document.fonts.ready")
    for f in range(round(sec * 30)):
        pg.evaluate(f"seek({f / 30})"); pg.screenshot(path=f"{d}/{f:05d}.png")
    b.close()
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", f"{d}/%05d.png", "-c:v", "libx264", "-crf", "14",
                "-pix_fmt", "yuv420p", out], check=True)
