"""Cut every take to its kept range at 30 fps 1080x1920, match its colour to the seat's reference take
(sunlight changed between takes), and join them into work/tight.mp4 (video only)."""
import os, subprocess, numpy as np, cv2
from plan import TAKES, SRC, REF, FPS, frames_of

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = f"{HERE}/work"
W, H = 1080, 1920


def decode(take, fa, fb):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC.format(take), "-vf",
                          f"fps={FPS},trim=start_frame={fa}:end_frame={fb},setpts=PTS-STARTPTS,scale={W}:{H}:flags=lanczos",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


def lab_stats(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    return lab.mean(0), lab.std(0)


def matcher(src_frame, ref_frame, amount=0.8):
    ms, ss = lab_stats(src_frame)
    mr, sr = lab_stats(ref_frame)
    k = 1 + amount * (sr / np.maximum(ss, 1e-3) - 1)
    def apply(f):
        lab = cv2.cvtColor(f, cv2.COLOR_BGR2LAB).astype(np.float32)
        lab = (lab - ms) * k + ms + amount * (mr - ms)
        return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    return apply


def encode(frames, path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "12", "-preset", "fast",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(f.tobytes())
    p.stdin.close(); p.wait()


if __name__ == "__main__":
    os.makedirs(WORK, exist_ok=True)
    refs = {}
    for seat, take in REF.items():
        a, b = [(x[1], x[2]) for x in TAKES if x[0] == take][0]
        fa, fb = frames_of(a, b)
        refs[seat] = decode(take, (fa + fb) // 2, (fa + fb) // 2 + 1)[0]
    parts = []
    for k, (take, a, b, seat, _) in enumerate(TAKES):
        p = f"{WORK}/v5-r{k:02d}.mp4"
        parts.append(p)
        if os.path.exists(p):
            continue
        fa, fb = frames_of(a, b)
        fr = decode(take, fa, fb)
        assert len(fr) == fb - fa, (take, len(fr), fb - fa)
        fix = matcher(fr[len(fr) // 2], refs[seat], 0.0 if take == REF[seat] else 0.8)
        encode((fix(f) for f in fr), p)
        print(take, len(fr), "frames", flush=True)
    open(f"{WORK}/list-v5.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WORK}/list-v5.txt",
                    "-c", "copy", f"{WORK}/tight-v5.mp4"], check=True)
    print("tight.mp4 written")
