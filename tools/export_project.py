#!/usr/bin/env python3
"""Export a reel's edit plan as an editable DaVinci Resolve project (FCPXML 1.9) instead of a flat mp4.

    python3 export_project.py edit.json [outdir]

Writes outdir (default: <reel>/proekt/):
  <name>.fcpxml         timeline 1080x1920 30p; import in Resolve: File > Import > Timeline
  subtitry.srt          the same subtitles as plain text, for Resolve's own subtitle track
  media/                B-roll clips, rendered cards, hook/CTA plates and the word-highlight
                        subtitle layer (mov with alpha); the original video is NOT copied,
                        the user drops it into media/ under its own file name.
Tracks: V1 speaker (split at zooms, zoom = clip scale), V2 B-roll and cards, V3 subtitles
(one clip per 2-3 word phrase, so each can be moved or deleted), V4 hook and CTA.
Transitions and the loudness chain are not carried over: they are added in the editor.
Uses the card and subtitle code from render.py, so the look matches the rendered reel.
"""
import json, os, shutil, subprocess, sys, tempfile, urllib.parse
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R

FPS = R.FPS
GUIDE_URL = "https://claude.ai/code/artifact/9cea20c4-4137-48be-8524-23adec6bdebb"
GUIDE = """Как открыть рилс в DaVinci Resolve (подробный гайд: """ + GUIDE_URL + """)

1. Положи свой оригинал «{src}» в папку media (имя не меняй).
2. Resolve: New Project > шестерёнка внизу справа > Master Settings:
   Timeline resolution 1080 x 1920, Timeline frame rate 30 > Save.
3. Вкладка Edit: перетащи папку media в Media Pool (на вопрос про частоту кадров: Don't Change).
4. File > Import > Timeline... > {xml}, сними галочку «Automatically import source clips
   into media pool» > OK.

V1 ты (зумы = Inspector > Zoom), V2 B-roll и карточки, V3 субтитры (фраза = клип), V4 хук и призыв.
Вручную: переходы (Ctrl/Cmd+T на краю клипа) и громкость -14 LUFS (Deliver > Audio > Normalize).
subtitry.srt: те же фразы обычными субтитрами Resolve (File > Import > Subtitle), без подсветки.
"""


def fr(t):
    """seconds -> frame-aligned FCPXML time"""
    return f"{round(t * FPS)}/{FPS}s"


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path],
                         capture_output=True, text=True, check=True)
    j = json.loads(out.stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    num, den = map(int, v["r_frame_rate"].split("/"))
    return dict(w=v["width"], h=v["height"], fps=(num, den), dur=float(j["format"]["duration"]),
                arate=int(a["sample_rate"]) if a else None, ach=a["channels"] if a else 0)


def srt_time(t):
    ms = round(max(t, 0) * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def encode_frames(d, out, alpha, fade_out=0.0, n=None):
    vf = []
    if fade_out and n:
        vf = ["-vf", f"fade=out:st={max(n / FPS - fade_out, 0):.3f}:d={fade_out}:alpha=1"]
    codec = ["-c:v", "png", "-pix_fmt", "rgba"] if alpha else \
        ["-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p"]
    R.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", f"{d}/%05d.png", *vf, *codec, out])


def main(plan_path, outdir=None):
    plan = json.load(open(plan_path))
    root = os.path.dirname(os.path.abspath(plan_path))
    p = lambda x: x if os.path.isabs(x) else os.path.join(root, x)
    src = p(plan["src"])
    outdir = outdir or os.path.join(root, "proekt")
    media = os.path.join(outdir, "media")
    os.makedirs(media, exist_ok=True)
    name = os.path.splitext(os.path.basename(plan.get("out", "reel.mp4")))[0]
    info = probe(src)
    total = info["dur"]
    words = json.load(open(p(plan["words"])))
    tmp = tempfile.mkdtemp(prefix="proj-")

    assets = {}  # file name in media/ -> (id, probe info)

    def asset(fname):
        if fname not in assets:
            assets[fname] = (f"a{len(assets) + 1}", probe(os.path.join(media, fname)))
        return assets[fname][0]

    # the speaker's original: referenced by its own name, not copied
    src_name = os.path.basename(src)
    assets[src_name] = ("a0", info)

    # ---- subtitles: one full-length alpha layer, cut into one clip per phrase on the timeline
    en = json.load(open(p(plan["en"]))) if plan.get("en") else None
    R.build_ass(words, f"{tmp}/subs.ass", plan.get("subs"), en)
    subs = f"{tmp}/subs.ass".replace(":", "\\:")
    R.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=black@0:s={R.W}x{R.H}:r={FPS}:d={total:.3f},format=rgba",
           "-vf", f"ass='{subs}':fontsdir=/usr/local/share/fonts/brand:alpha=1",
           "-c:v", "png", "-pix_fmt", "rgba", f"{media}/subtitry-sloj.mov"])
    chunks = R.chunk_words(words)
    with open(os.path.join(outdir, "subtitry.srt"), "w") as f:
        for i, ch in enumerate(chunks, 1):
            f.write(f"{i}\n{srt_time(ch[0]['s'])} --> {srt_time(ch[-1]['e'])}\n{' '.join(w['w'] for w in ch)}\n\n")
    if en:  # English line: also an editable subtitle track
        with open(os.path.join(outdir, "subtitry-en.srt"), "w") as f:
            for i, seg in enumerate(en, 1):
                f.write(f"{i}\n{srt_time(seg['s'])} --> {srt_time(seg['e'])}\n{seg['t']}\n\n")

    # ---- cards, clips, hook / CTA
    v2, v4 = [], []  # (clip name, file, timeline start, timeline end, source in)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=R.CHROME)
        page = browser.new_page(viewport={"width": R.W, "height": R.H})
        for i, c in enumerate(plan.get("cards", []), 1):
            s, e = c["start"], c["end"]
            if c["kind"] == "clip":
                fname = f"broll-{i:02d}-{os.path.basename(c['file'])}"
                R.run(["ffmpeg", "-y", "-v", "error", "-i", p(c["file"]), "-map", "0:v:0", "-c", "copy",
                       os.path.join(media, fname)])  # video only: stock audio must not reach the timeline
                v2.append((f"B-roll {i}", fname, s, e, c.get("from", 0)))
            else:
                theme = c.get("theme", plan.get("theme", "dark"))
                glass = theme == "glass"
                d = f"{tmp}/card{i}"
                R.render_frames(page, R.card_html(c, theme), e - s, d, transparent=glass)
                fname = f"kartochka-{i:02d}-{c['kind']}.{'mov' if glass else 'mp4'}"
                encode_frames(d, os.path.join(media, fname), alpha=glass)
                v2.append((f"Карточка {i} ({c['kind']})", fname, s, e, 0))
        for key, top, label in (("hook", 260, "Хук"), ("cta", 300, "Призыв")):
            b = plan.get(key)
            if not b:
                continue
            s = b.get("start", 0)
            s = total + s if s < 0 else s
            e = b.get("end", total)
            d = f"{tmp}/{key}"
            n = R.render_frames(page, R.banner_html(b["text"], b.get("accent"), b.get("top", top), b.get("sub")), e - s, d, transparent=True)
            fname = f"{'huk' if key == 'hook' else 'prizyv'}.mov"
            encode_frames(d, os.path.join(media, fname), alpha=True, fade_out=0.25, n=n)
            v4.append((label, fname, s, e, 0))
        browser.close()

    # ---- FCPXML
    fmt_ids = {}

    def fmt(w, h, fps):
        k = (w, h, fps)
        if k not in fmt_ids:
            fmt_ids[k] = f"f{len(fmt_ids) + 1}"
        return fmt_ids[k]

    tl_fmt = fmt(R.W, R.H, (FPS, 1))
    for fname in [x[1] for x in v2 + v4] + ["subtitry-sloj.mov"]:
        asset(fname)

    def clip(ref, name, s, e, start, lane=None, extra=""):
        a_id = assets[ref][0]
        lane_attr = f' lane="{lane}"' if lane is not None else ""
        return s, (f'<asset-clip ref="{a_id}"{lane_attr} name={quoteattr(name)} offset="{fr(s)}" '
                   f'start="{fr(start)}" duration="{fr(e - s)}" tcFormat="NDF">{extra}</asset-clip>')

    connected = []
    for name_, fname, s, e, start in v2:  # stock clips of other shapes fill the frame, as in render.py
        connected.append(clip(fname, name_, s, e, start, lane=1, extra='<adjust-conform type="fill"/>'))
    for i, ch in enumerate(chunks, 1):
        s, e = ch[0]["s"], ch[-1]["e"]
        connected.append(clip("subtitry-sloj.mov", " ".join(w["w"] for w in ch), s, e, s, lane=2))
    for name_, fname, s, e, start in v4:
        connected.append(clip(fname, name_, s, e, start, lane=3))

    # V1: the speaker, split at zoom boundaries; connected clips hang off the segment they start in
    cuts = sorted({0.0, total, *[z["start"] for z in plan.get("zooms", [])], *[z["end"] for z in plan.get("zooms", [])]})
    segs = []
    for a, b in zip(cuts, cuts[1:]):
        if round(b * FPS) <= round(a * FPS):
            continue
        z = next((z for z in plan.get("zooms", []) if z["start"] <= a < z["end"]), None)
        segs.append((a, b, z))
    spine = []
    for a, b, z in segs:
        inner = ""
        if z:
            sc = z.get("scale", 1.15)
            inner += f'<adjust-transform scale="{sc} {sc}"/>'
        for t, c in connected:
            if round(a * FPS) <= round(t * FPS) < round(b * FPS):
                inner += c
        label = "Спикер" + (" зум %s" % z.get("scale", 1.15) if z else "")
        spine.append(f'<asset-clip ref="a0" name={quoteattr(label)} '
                     f'offset="{fr(a)}" start="{fr(a)}" duration="{fr(b - a)}" tcFormat="NDF" audioRole="dialogue">{inner}</asset-clip>')

    res = []
    for fname, (aid, inf) in assets.items():
        fid = fmt(inf["w"], inf["h"], inf["fps"])
        audio = f' hasAudio="1" audioSources="1" audioChannels="{inf["ach"]}" audioRate="{inf["arate"]}"' if inf["arate"] else ""
        url = "file:///media/" + urllib.parse.quote(fname)
        res.append(f'<asset id="{aid}" name={quoteattr(fname)} start="0s" duration="{fr(inf["dur"])}" hasVideo="1" '
                   f'format="{fid}"{audio}><media-rep kind="original-media" src={quoteattr(url)}/></asset>')
    res = [f'<format id="{fid}" frameDuration="{fps[1]}/{fps[0]}s" width="{w}" height="{h}" colorSpace="1-1-1 (Rec. 709)"/>'
                     for (w, h, fps), fid in fmt_ids.items()] + res

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.9">
<resources>
{chr(10).join(res)}
</resources>
<library>
<event name={quoteattr(name)}>
<project name={quoteattr(name)}>
<sequence format="{tl_fmt}" duration="{fr(total)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
<spine>
{chr(10).join(spine)}
</spine>
</sequence>
</project>
</event>
</library>
</fcpxml>
"""
    open(os.path.join(outdir, f"{name}.fcpxml"), "w").write(xml)
    open(os.path.join(outdir, "KAK-OTKRYT.txt"), "w").write(GUIDE.format(src=src_name, xml=f"{name}.fcpxml"))
    shutil.rmtree(tmp, ignore_errors=True)
    print("project in", outdir, "- put", src_name, "into media/")


if __name__ == "__main__":
    main(*sys.argv[1:])
