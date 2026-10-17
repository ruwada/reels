"""Cut the pauses out: concatenate the kept ranges of the takes into work/tight.mp4 + work/tight-voice.wav.
Times in edit.py are seconds of this tight timeline."""
import subprocess, numpy as np, wave, os
W = os.path.dirname(os.path.abspath(__file__)) + "/work"
SRC = {"main": "/tmp/fx/cafe/cafe.mp4", "t308": "/tmp/fx/cafe/t308.mp4"}
RANGES = [("main", 1.80, 7.20), ("main", 9.25, 20.35), ("main", 22.35, 28.60), ("main", 29.20, 32.65),
          ("main", 33.35, 34.15), ("main", 35.15, 37.30), ("main", 37.80, 40.15), ("t308", 7.60, 13.40)]
FPS, SR = 30, 44100

if __name__ == "__main__":
    parts, voice = [], []
    for k, (take, a, b) in enumerate(RANGES):
        fa, fb = round(a * FPS), round(b * FPS)          # whole frames so audio and video stay locked
        p = f"{W}/r{k}.mp4"
        if not os.path.exists(p): subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC[take], "-vf", f"trim=start_frame={fa}:end_frame={fb},setpts=PTS-STARTPTS",
                        "-an", "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", p], check=True)
        parts.append(p)
        w = wave.open(f"{W}/{take}-voice.wav"); x = np.frombuffer(w.readframes(w.getnframes()), np.int16)
        n = (fb - fa) * SR // FPS
        seg = x[fa * SR // FPS: fa * SR // FPS + n]
        seg = np.pad(seg, (0, n - len(seg)))
        voice.append(seg)
    open(f"{W}/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
    if not os.path.exists(f"{W}/tight.mp4"): subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{W}/list.txt", "-c", "copy", f"{W}/tight.mp4"], check=True)
    v = np.concatenate(voice)
    o = wave.open(f"{W}/tight-voice.wav", "wb"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes(v.tobytes()); o.close()
    t = 0
    for (take, a, b) in RANGES:
        d = (round(b * FPS) - round(a * FPS)) / FPS
        print(f"{take} {a:6.2f}-{b:6.2f} -> tight {t:6.2f}-{t + d:6.2f}"); t += d
