#!/usr/bin/env python3
"""Client-story cut of the Haydelin reel: dentist Zaur orders the app, Islam builds it, the app demo, Zaur's reaction.

Builds work/zaur/src.mp4 (one continuous picture + voice track) that render.py then dresses with
cards, subtitles, hook and CTA (zaur/edit.json).

Voices: Zaur = Omni scene audio converted to his ElevenLabs clone (speech-to-speech keeps the lipsync),
then EQ-matched to his real reels; Islam = his ElevenLabs voice (TTS lines + the app narration converted
by speech-to-speech from his recording, so it keeps the timing of the screens).
"""
import os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, "..", "work", "zaur")
ORIG = os.path.join(HERE, "..", "orig.mov")
BROLL = os.path.join(HERE, "..", "broll")

# (video file, in, out)  -> placed back to back
SEGS = [
    ("sc1.mp4", 0.4, 5.5),       # Zaur: braces, treatment drags on
    ("sc2.mp4", 0.3, 6.9),       # Zaur: patients don't brush, kids don't want to
    ("sc3.mp4", 0.6, 4.5),       # Zaur: make it impossible to miss
    ("sc4.mp4", 0.0, 4.4),       # Islam types: "Договорились..."
    ("sc5.mp4", 0.0, 2.9),       # night coding: "Вот что получилось."
    (ORIG, 10.3, 43.95),         # app demo from v2 (screens are cards in edit.json)
    ("sc7.mp4", 0.8, 4.8),       # Zaur with the phone (Omni dissolves into the reference photo after 4.9 s): "Это ровно то, что я хотел."
    (os.path.join(BROLL, "8266177.mp4"), 2.0, 6.8),  # CTA
]
# (audio file, offset in that file, timeline position)
VOICE = [
    ("z1e.wav", 0.4, 0.0),
    ("z2e.wav", 0.3, 5.1),
    ("z3e.wav", 0.6, 11.7),
    ("B1.mp3", 0.0, 15.9),
    ("B2.mp3", 0.0, 20.35),
    ("app-b.mp3", 0.0, 22.9),
    ("z7e.wav", 0.8, 56.55),
    ("B3.mp3", 0.0, 60.75),
]


def run(cmd):
    subprocess.run(cmd, check=True)


def p(f):
    return f if os.path.isabs(f) else os.path.join(W, f)


def main():
    parts, t = [], 0.0
    for i, (f, a, b) in enumerate(SEGS):
        out = f"{W}/seg{i}.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", f"{b - a:.3f}", "-i", p(f), "-an",
             "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration=1",
             "-frames:v", str(round((b - a) * 30)),  # exact frame count, so the picture never drifts from the voice
             "-c:v", "libx264", "-preset", "fast", "-crf", "14", out])
        parts.append(out); t += b - a
    total = t
    open(f"{W}/list.txt", "w").write("".join(f"file '{x}'\n" for x in parts))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{W}/list.txt", "-c", "copy", f"{W}/pic.mp4"])

    args, fc = ["ffmpeg", "-v", "error", "-y"], []
    for i, (f, off, at) in enumerate(VOICE):
        args += ["-ss", str(off), "-i", p(f)]
        ms = round(at * 1000)
        fc.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=mono,loudnorm=I=-16:TP=-2:LRA=7,"
                  f"aresample=48000,adelay={ms}:all=1[a{i}]")
    fc.append("".join(f"[a{i}]" for i in range(len(VOICE))) +
              f"amix=inputs={len(VOICE)}:normalize=0:duration=longest,apad,atrim=0:{total:.3f}[a]")
    run(args + ["-filter_complex", ";".join(fc), "-map", "[a]", "-ac", "1", "-ar", "48000", f"{W}/voice.wav"])
    run(["ffmpeg", "-v", "error", "-y", "-i", f"{W}/pic.mp4", "-i", f"{W}/voice.wav", "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "pcm_s16le", "-shortest", f"{W}/src.mov"])
    print(f"src.mov {total:.2f}s")


if __name__ == "__main__":
    main()
