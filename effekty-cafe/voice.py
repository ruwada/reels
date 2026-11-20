"""Re-voice the cafe takes with the approved clone, chunk by chunk onto the lip spans of his own speech.
Each sentence is synthesized whole (natural intonation), split at word boundaries into chunks, and every chunk
is time-fitted into the span where his lips say it (spans measured on the Audio-Isolated original)."""
import base64, json, os, subprocess, sys, numpy as np, wave, urllib.request

VOICE = "BfVyIdPg9joQxukEjS3J"   # islam.devai-2, approved 2026-10-05
SET = dict(stability=0.45, similarity_boost=1.0, style=0.2, use_speaker_boost=True, speed=1.1)
SR = 44100
OUT = os.path.dirname(os.path.abspath(__file__)) + "/work"

# sentence -> chunks with the source span (seconds in that take) his lips speak them in
PLAN = {
 "main": [
  [("Монтажёр бы это делал", 2.15, 3.54), ("неделю.", 4.05, 4.62), ("А я", 4.90, 5.31),
   ("не вставая с этого кресла.", 5.63, 6.99)],
  [("И сейчас будем разговаривать о том, что меняется у нас", 9.44, 12.68), ("в этом видео.", 13.25, 14.04)],
  [("У нас в этом видео меняется много чего.", 14.78, 16.72)],
  [("И", 17.26, 17.62), ("монтаж всего этого", 18.71, 20.13), ("тоже", 22.47, 22.92), ("меняется", 23.36, 23.98),
   ("сам по себе.", 24.22, 24.92)],
  [("Я тут ничего не делаю.", 25.58, 26.87)],
  [("Чтобы вы поняли правильно:", 27.24, 28.41)],
  [("я сижу,", 29.40, 29.95), ("попиваю свой кофе,", 30.60, 31.64)],
  [("А...", 32.20, 32.50), ("монтаж...", 33.50, 34.00), ("и...", 35.40, 35.65), ("стиль...", 36.80, 37.18),
   ("и формат...", 37.95, 38.73), ("меняются.", 39.22, 40.05)],
 ],
 "t308": [
  [("Хочешь такой же ролик?", 7.90, 8.92)],
  [("Тринадцатый гайд", 9.90, 10.85), ("в телеграме.", 11.03, 11.60), ("Забирай — в шапке.", 11.82, 13.00)],
 ],
}


def tts(text, path):
    if os.path.exists(path + ".json"):
        return json.load(open(path + ".json"))
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps(dict(text=text, model_id="eleven_multilingual_v2", language_code="ru",
                             voice_settings=SET)).encode(), headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req))
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


def build(take, total):
    os.makedirs(OUT, exist_ok=True)
    track = np.zeros(int(total * SR) + SR, np.float32)
    report = []
    for si, chunks in enumerate(PLAN[take]):
        text = " ".join(c[0] for c in chunks)
        al = tts(text, f"{OUT}/{take}-s{si}")
        audio = load(f"{OUT}/{take}-s{si}.mp3")
        chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
        pos = 0
        for ci, (ctext, s0, s1) in enumerate(chunks):
            a_idx = text.index(ctext, pos); b_idx = a_idx + len(ctext) - 1; pos = b_idx + 1
            # cut between words: midway into the gap to the neighbour chunk
            t_a = st[a_idx] if ci == 0 else (en[a_idx - 2] + st[a_idx]) / 2
            t_b = en[b_idx] if ci == len(chunks) - 1 else (en[b_idx] + st[b_idx + 2]) / 2
            seg = trim(audio[int(t_a * SR): int(t_b * SR)])
            have, want = len(seg) / SR, s1 - s0
            ratio = float(np.clip(want / have, 0.72, 1.35))
            seg = stretch(seg, ratio)
            n = min(len(seg), 2048)
            seg[:64] *= np.linspace(0, 1, 64); seg[-n // 8:] *= np.linspace(1, 0, n // 8)
            i0 = int(s0 * SR)
            track[i0:i0 + len(seg)] += seg[: len(track) - i0]
            report.append(f"{take} {ctext!r:34} lips {s0:5.2f}-{s1:5.2f} ({want:.2f}s)  tts {have:.2f}s  x{ratio:.2f}"
                          + ("  !" if abs(want / have - ratio) > 0.02 else ""))
    return track, report


if __name__ == "__main__":
    for take, total in (("main", 41.0), ("t308", 14.0)):
        tr, rep = build(take, total)
        wav = wave.open(f"{OUT}/{take}-voice.wav", "wb"); wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(SR)
        wav.writeframes((np.clip(tr, -1, 1) * 32767).astype(np.int16).tobytes()); wav.close()
        print("\n".join(rep))
