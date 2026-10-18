"""Re-voice the v4 takes with the approved clone, chunk by chunk onto the lip spans of his own speech.
Each sentence is synthesized whole (natural intonation), split at word boundaries into chunks, and every chunk
is time-fitted into the span where his lips say it (spans measured on the Audio-Isolated original)."""
import base64, json, os, subprocess, sys, numpy as np, wave, urllib.request

VOICE = "BfVyIdPg9joQxukEjS3J"   # islam.devai-2, approved 2026-10-05
SET = dict(stability=0.45, similarity_boost=1.0, style=0.2, use_speaker_boost=True, speed=1.1)
SR = 44100
OUT = os.path.dirname(os.path.abspath(__file__)) + "/work"

def tts(text, path):
    if os.path.exists(path + ".json"):
        return json.load(open(path + ".json"))
    body = json.dumps(dict(text=text, model_id="eleven_multilingual_v2", language_code="ru", voice_settings=SET))
    out = subprocess.run(["curl", "-sS", "-X", "POST", "-H", "Content-Type: application/json", "--data-binary", "@-",
                          f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_128"],
                         input=body.encode(), capture_output=True, check=True).stdout
    r = json.loads(out)
    open(path + ".mp3", "wb").write(base64.b64decode(r["audio_base64"]))
    json.dump(r["alignment"], open(path + ".json", "w"), ensure_ascii=False)
    return r["alignment"]


def load(path):
    a = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                       capture_output=True).stdout
    return np.frombuffer(a, np.float32).copy()


def stretch(x, ratio):
    """Change duration by `ratio` (out/in) keeping pitch (ffmpeg atempo)."""
    if abs(ratio - 1) < 0.01:
        return x
    tempo = 1 / ratio
    chain = []
    while tempo > 2: chain.append("atempo=2"); tempo /= 2
    while tempo < 0.5: chain.append("atempo=0.5"); tempo /= 0.5
    chain.append(f"atempo={tempo:.4f}")
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                        ",".join(chain), "-f", "f32le", "-"], input=x.tobytes(), capture_output=True).stdout
    return np.frombuffer(p, np.float32).copy()


def trim(x, th=0.004):
    """Drop silence at the chunk edges, keeping soft onsets like «с» (40 ms before the first loud sample)."""
    idx = np.where(np.abs(x) > th)[0]
    return x[max(0, idx[0] - 1800): idx[-1] + 900] if len(idx) else x


from plan import TAKES, T, END

# the clone's first sound is softer than his: measured +0.17 s late against his lips (lipcheck.py), so start earlier
LEAD = 0.10


def build():
    track = np.zeros(int((END + 1) * SR), np.float32)
    report = []
    for take, a, b, seat, chunks in TAKES:
        text = " ".join(c[0] for c in chunks)
        al = tts(text, f"{OUT}/{take}-tts")
        audio = load(f"{OUT}/{take}-tts.mp3")
        st, en = al["character_start_times_seconds"], al["character_end_times_seconds"]
        pos = 0
        for ci, (ctext, s0, s1) in enumerate(chunks):
            a_idx = text.index(ctext, pos); b_idx = a_idx + len(ctext) - 1; pos = b_idx + 1
            t_a = st[a_idx] if ci == 0 else (en[a_idx - 2] + st[a_idx]) / 2
            t_b = en[b_idx] if ci == len(chunks) - 1 else (en[b_idx] + st[b_idx + 2]) / 2
            seg = trim(audio[int(t_a * SR): int(t_b * SR)])
            have, want = len(seg) / SR, s1 - s0
            # single emphatic words he dragged out may stretch further than a whole phrase
            ratio = float(np.clip(want / have, 0.72, 1.7 if len(ctext.split()) <= 3 else 1.35))
            seg = stretch(seg, ratio)
            n = min(len(seg), 2048)
            seg[:64] *= np.linspace(0, 1, 64); seg[-n // 8:] *= np.linspace(1, 0, n // 8)
            i0 = int((T(take, s0) - LEAD) * SR)
            track[i0:i0 + len(seg)] += seg[: len(track) - i0]
            report.append(f"{take} {ctext!r:52} lips {s0:5.2f}-{s1:5.2f} ({want:.2f}s) tts {have:.2f}s x{ratio:.2f}"
                          + ("  !" if abs(want / have - ratio) > 0.02 else ""))
    return track, report


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    tr, rep = build()
    wav = wave.open(f"{OUT}/tight-voice.wav", "wb"); wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(SR)
    wav.writeframes((np.clip(tr, -1, 1) * 32767).astype(np.int16).tobytes()); wav.close()
    print("\n".join(rep))
