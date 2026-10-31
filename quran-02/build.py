#!/usr/bin/env python3
"""Render a Quran recitation video from ready parts only.

    python3 build.py <config.json>

Text and translation come untouched from src/<name>/ayat.json (fetch.py), audio and ayah timing from mp3quran.
The only thing decided here is timing: each ayah boundary from the timing file is moved to the middle of the
nearest pause within +-1 s, so the text never changes in the middle of a word.
"""
import json, os, subprocess, sys
import numpy as np

cfg = json.load(open(sys.argv[1]))
name, style = cfg['name'], cfg['style']
d = json.load(open(f"src/{name}/ayat.json"))
mp3 = f"src/{name}/{d['surah']:03d}.mp3"
W = f"work/{name}"; os.makedirs(W, exist_ok=True)

# --- timing: snap boundaries to pauses -------------------------------------------------------------
t0 = max(0, d['ayat'][0]['start'] - 2); t1 = d['ayat'][-1]['stop'] + 2
pcm = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-to", str(t1), "-i", mp3, "-ac", "1", "-ar", "16000",
                      "-f", "s16le", "-"], capture_output=True).stdout
a = np.frombuffer(pcm, np.int16).astype(float); H = 800  # 50 ms frames
db = np.array([20 * np.log10(np.sqrt(np.mean(a[i:i + H] ** 2)) + 1) for i in range(0, len(a) - H, H)])
quiet = db < np.percentile(db, 95) - 15
runs, i = [], 0
while i < len(quiet):
    if quiet[i]:
        j = i
        while j < len(quiet) and quiet[j]: j += 1
        if j - i >= 3: runs.append((t0 + i * 0.05, t0 + j * 0.05))
        i = j
    else: i += 1


def snap(t, side):
    """Middle of the nearest pause; for the very start/end use the pause's inner edge."""
    near = [r for r in runs if abs((r[0] + r[1]) / 2 - t) <= 1.0 or r[0] <= t <= r[1]]
    if not near: return t, None
    r = min(near, key=lambda r: abs((r[0] + r[1]) / 2 - t))
    return {'mid': (r[0] + r[1]) / 2, 'start': max(r[0], r[1] - 0.25), 'end': min(r[1], r[0] + 0.3)}[side], r


edges = [snap(d['ayat'][0]['start'], 'start')[0]]
log = []
for x in d['ayat'][:-1]:
    t, r = snap(x['stop'], 'mid'); edges.append(t); log.append((x['key'], x['stop'], t, r))
edges.append(snap(d['ayat'][-1]['stop'], 'end')[0])
A0, A1 = edges[0], edges[-1]
for k, raw, t, r in log: print(f"after {k}: timing file {raw:.2f}  ->  {t:.2f}  ({t - raw:+.2f} s, pause {r})")
rel = [e - A0 for e in edges]          # boundaries relative to video start
AD = A1 - A0; T = AD + cfg.get('tail', 1.2)
print(f"audio {A0:.2f}-{A1:.2f} ({AD:.1f} s), video {T:.1f} s")

# --- text layers (Playwright) ----------------------------------------------------------------------
json.dump(dict(style=style, surah_name=cfg['surah_name'], ayat=d['ayat'], out=W), open(f"{W}/layers.json", "w"), ensure_ascii=False)
subprocess.run(["node", "layers.mjs", f"{W}/layers.json"], check=True,
               env={**os.environ, "NODE_PATH": subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()})

# --- background: clips joined with soft crossfades, stretched to fill ----------------------------------
clips = cfg['clips']; XF = 0.8
raw_len = sum(c[2] for c in clips) - XF * (len(clips) - 1)
stretch = max(1.0, T / raw_len)
inputs, fc = [], []
for n, (cid, ss, du) in enumerate(clips):
    inputs += ["-ss", str(ss), "-t", str(du), "-i", f"broll/{cid}.mp4"]
    fc.append(f"[{n}:v]setpts={stretch:.4f}*(PTS-STARTPTS),scale=1080:1920:force_original_aspect_ratio=increase,"
              f"crop=1080:1920,fps=30,format=yuv420p,setsar=1[c{n}]")
prev, off = "c0", clips[0][2] * stretch
for n in range(1, len(clips)):
    fc.append(f"[{prev}][c{n}]xfade=transition=fade:duration={XF}:offset={off - XF:.3f}[x{n}]")
    prev, off = f"x{n}", off - XF + clips[n][2] * stretch
fc.append(f"[{prev}]trim=0:{T:.3f},setpts=PTS-STARTPTS[bg]")
na = len(clips)
inputs += ["-ss", f"{A0:.3f}", "-t", f"{AD:.3f}", "-i", mp3]
cur = "bg"
layer_in = na + 1
if os.path.exists(f"{W}/under.png"):  # constant shade under the text (style "bottom")
    inputs += ["-loop", "1", "-t", f"{T:.3f}", "-i", f"{W}/under.png"]
    fc.append(f"[{cur}][{layer_in}:v]overlay=0:0[under]"); cur = "under"; layer_in += 1
if style == "glass":  # frosted panel: blurred background shows through a rounded mask, one per ayah
    fc.append(f"[{cur}]split[bgA][bgB];[bgB]gblur=sigma=18,format=rgba,split={len(d['ayat'])}" +
              "".join(f"[bl{k}]" for k in range(len(d['ayat']))))
    cur = "bgA"
for k, x in enumerate(d['ayat']):
    s, e = rel[k], rel[k + 1]
    fin = 0.6 if k == 0 else 0.25
    fout_st = e - 0.25 if k < len(d['ayat']) - 1 else T - 1.1
    fade = f"fade=t=in:st={s:.3f}:d={fin}:alpha=1,fade=t=out:st={fout_st:.3f}:d=0.25:alpha=1"
    win = f"between(t,{s - 0.05:.3f},{fout_st + 0.3:.3f})"
    if style == "glass":
        inputs += ["-loop", "1", "-t", f"{T:.3f}", "-i", f"{W}/mask-{k + 1}.png"]
        fc.append(f"[{layer_in}:v]format=gray[m{k}];[bl{k}][m{k}]alphamerge,{fade}[g{k}];[{cur}][g{k}]overlay=0:0:enable='{win}'[o{k}a]")
        cur = f"o{k}a"; layer_in += 1
    inputs += ["-loop", "1", "-t", f"{T:.3f}", "-i", f"{W}/text-{k + 1}.png"]
    fc.append(f"[{layer_in}:v]format=rgba,{fade}[t{k}];[{cur}][t{k}]overlay=0:0:enable='{win}'[o{k}]")
    cur = f"o{k}"; layer_in += 1
inputs += ["-loop", "1", "-t", f"{T:.3f}", "-i", f"{W}/base.png"]
fc.append(f"[{cur}][{layer_in}:v]overlay=0:0,fade=t=out:st={T - 0.7:.3f}:d=0.7,format=yuv420p[v]")
fc.append(f"[{na}:a]afade=t=in:d=0.08,afade=t=out:st={AD - 0.3:.3f}:d=0.3,apad=whole_dur={T:.3f}[a]")
out = f"{W}/{name}.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                "-t", f"{T:.3f}", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
json.dump(dict(edges_abs=edges, edges_rel=rel, T=T), open(f"{W}/timing-used.json", "w"), indent=1)
print(out)
