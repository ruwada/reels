"""Voice = his own speech from each take (ElevenLabs Audio Isolation, made once in /tmp/fx/v4/*-iso.wav), cut
sample-exact with the video ranges, loudness levelled per take, short fades -> work/tight-voice-own.wav.
Same timing as the picture, so the lips match by construction."""
import subprocess, numpy as np, os
from plan import TAKES, FPS, frames_of

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
FADE = int(0.012 * SR)
TARGET = -15.0   # dB RMS of speech in every take


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


out = []
for take, a, b, *_ in TAKES:
    fa, fb = frames_of(a, b)
    x = load(f"/tmp/fx/v4/{take}-iso.wav")
    i0, i1 = round(fa / FPS * SR), round(fb / FPS * SR)
    seg = np.zeros(i1 - i0, np.float32)
    part = x[i0:i1]
    seg[:len(part)] = part
    fr = seg[:len(seg) // 2400 * 2400].reshape(-1, 2400)          # even out loudness between takes
    r = np.sqrt((fr ** 2).mean(1)); act = r[r > r.max() * 0.15]
    seg *= min(10 ** (4 / 20), 10 ** ((TARGET - 20 * np.log10(np.sqrt((act ** 2).mean()))) / 20))
    ramp = np.linspace(0, 1, FADE, dtype=np.float32)
    seg[:FADE] *= ramp
    seg[-FADE:] *= ramp[::-1]
    out.append(seg)
y = np.concatenate(out)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                f"{HERE}/work/tight-voice-own.wav"], input=y.tobytes(), check=True)
print(f"{len(y) / SR:.3f} s")
