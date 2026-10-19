"""Voice = the approved clone (islam.devai-2, its usual settings), one TTS per PHRASE of his own speech.
A phrase is what he said between two real pauses (>= 0.25 s on the isolated take audio), with the words he
actually said. Each phrase is synthesized whole with its neighbours as context (no cutting inside a phrase,
so no stutter), then fitted into the span where his lips say it: first by asking the TTS for the right
speaking speed, then a small pitch-keeping stretch (rubberband) for the rest -> work/tight-voice.wav."""
import hashlib, json, os, subprocess, numpy as np, wave
from plan import T, END

VOICE = "BfVyIdPg9joQxukEjS3J"   # islam.devai-2, approved 2026-10-05
BASE = dict(stability=0.45, similarity_boost=1.0, style=0.2, use_speaker_boost=True)
SPEED = 1.1                       # his approved delivery speed
SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = f"{HERE}/work/phr"

# take: [(what he said, lips start, lips end)] - spans from spans.json, words from Gemini + GigaAM on the take
PHRASES = {
    "0342": [("Монтажёр делал бы такие эффекты неделю,", 3.85, 6.53), ("а я делаю с и-и, пока пью кофе.", 6.91, 9.38)],
    "0343": [("Ищешь монтажёра,", 5.96, 6.92), ("ждёшь правки,", 7.42, 8.34), ("платишь за каждый эффект?", 9.13, 10.60)],
    "0344": [("А можно так?", 1.98, 2.66), ("Твои ролики летают вокруг тебя.", 3.05, 5.19)],
    "0346": [("Главное слово — стекло прямо на стене.", 1.86, 4.45)],
    "0348": [("Комната выезжает,", 1.70, 2.90), ("прямо как в кино.", 3.04, 3.97)],
    "0349": [("Ты на обложке журнала.", 2.47, 4.37)],
    "0351": [("Фон меняется по щелчку,", 1.72, 3.36), ("без зелёной ткани.", 3.61, 4.71)],
    "0352": [("Вокруг оживают рисунки.", 1.38, 2.95)],
    "0354": [("Или ты —", 1.71, 2.41), ("коллаж из бумаги.", 2.82, 4.04)],
    "0355": [("Стена за спиной заполняется твоими роликами.", 1.55, 4.12)],
    "0356": [("Наезд,", 1.55, 2.38), ("на каждое", 2.47, 3.36), ("твоё слово.", 3.58, 4.80)],
    "0358": [("Охваты растут прямо за спиной.", 0.96, 2.92)],
    "0359": [("Пролетаем сквозь кадр.", 1.10, 2.95)],
    "0364": [("Я просто пишу ассистенту, что мне нужно.", 2.82, 5.06)],
    "0365": [("Субтитры, звук, обложка —", 1.93, 3.66), ("всё монтируется само.", 4.37, 5.40)],
    "0366": [("А всё это", 4.72, 5.54), ("просто окно на моём ноутбуке.", 5.86, 7.69)],
    "0368": [("Хочешь такие эффекты в своих роликах?", 4.30, 6.30),
             ("Забирай гайд под номером восемнадцать в телеграме,", 6.50, 8.99),
             ("ссылка в шапке профиля.", 9.68, 10.79)],
}
LEAD = 0.0   # onset offset of the clone vs his lips, set from lipcheck.py


def tts(text, speed, prev, nxt):
    key = hashlib.md5(f"{text}|{speed:.2f}|{prev}|{nxt}".encode()).hexdigest()[:12]
    p = f"{CACHE}/{key}.mp3"
    if not os.path.exists(p):
        assert os.environ.get("ALLOW_TTS") == "1", f"not cached, ask the user before spending credits: {text}"
        body = json.dumps(dict(text=text, model_id="eleven_multilingual_v2", language_code="ru",
                               previous_text=prev or None, next_text=nxt or None,
                               voice_settings=dict(BASE, speed=round(speed, 2))))
        r = subprocess.run(["curl", "-sS", "-f", "-X", "POST", "-H", "Content-Type: application/json", "--data-binary", "@-",
                            "-o", p, f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128"],
                           input=body.encode())
        assert r.returncode == 0, text
    return load(p)


def load(path, af=None):
    cmd = ["ffmpeg", "-v", "error", "-i", path] + (["-af", af] if af else []) + ["-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).copy()


def onset(x, sr, lo=0.0, hi=None, norm=None):
    """First moment the smoothed loudness passes 12 % of the reference level (same rule as lipcheck.py)."""
    hop = sr // 100
    n = len(x) // hop
    e = np.convolve(np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1)), np.ones(5) / 5, "same")
    ref = norm if norm is not None else np.percentile(e, 98)
    i0, i1 = int(lo * 100), int((hi if hi is not None else n / 100) * 100)
    idx = np.where(e[i0:i1] > 0.12 * ref)[0]
    return (i0 + idx[0]) / 100 if len(idx) else lo


def trim(x, th=0.006):
    idx = np.where(np.abs(x) > th)[0]
    return x[max(0, idx[0] - int(0.03 * SR)): idx[-1] + int(0.04 * SR)]


def stretch(x, ratio):
    if abs(ratio - 1) < 0.01:
        return x
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                        f"rubberband=tempo={1 / ratio:.4f}:transients=smooth:formant=preserved", "-f", "f32le", "-"],
                       input=x.tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(p, np.float32).copy()


if __name__ == "__main__":
    os.makedirs(CACHE, exist_ok=True)
    track = np.zeros(int((END + 1) * SR), np.float32)
    for take, ph in PHRASES.items():
        iso = load(f"/tmp/fx/v4/{take}-iso.mp3")
        hop = SR // 100; n = len(iso) // hop
        iso_ref = np.percentile(np.convolve(np.sqrt((iso[: n * hop].reshape(n, hop) ** 2).mean(1)), np.ones(5) / 5, "same"), 98)
        for i, (text, s0, s1) in enumerate(ph):
            prev = " ".join(p[0] for p in ph[:i]); nxt = " ".join(p[0] for p in ph[i + 1:])
            want = s1 - s0
            x = trim(tts(text, SPEED, prev, nxt))
            sp = float(np.clip(SPEED * (len(x) / SR) / want, 0.85, 1.2))
            if abs(sp - SPEED) > 0.03:
                x = trim(tts(text, sp, prev, nxt))
            else:
                sp = SPEED
            ratio = float(np.clip(want / (len(x) / SR), 0.85, 1.40))   # he drags single words: stretch them further
            y = stretch(x, ratio)
            f = int(0.008 * SR); y[:f] *= np.linspace(0, 1, f); y[-4 * f:] *= np.linspace(1, 0, 4 * f)
            lip = onset(iso, SR, s0 - 0.2, s0 + 0.4, iso_ref)          # where his voice really starts
            i0 = int((T(take, lip) - onset(y, SR) - LEAD) * SR)        # the clone's first sound lands there
            if i0 < 0:
                y, i0 = y[-i0:], 0
            track[i0:i0 + len(y)] += y
            fit = len(y) / SR / want
            print(f"{take} {text:52} lips {want:.2f}s  speed {sp:.2f}  stretch x{ratio:.2f}  fit {fit:.2f}"
                  + ("  <--" if abs(fit - 1) > 0.06 else ""))
    wav = wave.open(f"{HERE}/work/tight-voice.wav", "wb"); wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(SR)
    wav.writeframes((np.clip(track[: int(END * SR)], -1, 1) * 32767).astype(np.int16).tobytes()); wav.close()
