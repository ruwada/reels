#!/usr/bin/env python3
"""Re-voice the app narration with the user's ElevenLabs voice (TTS from the clean script, no stumbles).
Each phrase is synthesised separately (with previous/next text for natural intonation) and later placed at the
moment the matching screen appears. usage: tts_app.py OUTDIR"""
import json, subprocess, sys, os
VOICE = "BfVyIdPg9joQxukEjS3J"  # islam.devai-2, same as "Договорились" / CTA
# (text, slot start, slot end) on the reel timeline, slots follow the phone screens in edit.json
PHRASES = [
    ("Утром и вечером звенит будильник.", 23.2, 25.0),
    ("Нажимаешь на старт, и персонаж на экране повторяет твою мимику.", 25.05, 29.0),
    ("Открыл рот, и он открыл.", 29.05, 30.75),
    ("Таймер ведёт по шести зонам рта.", 30.8, 32.8),
    ("Две минуты, и ни одной зоны не пропустишь.", 32.85, 35.2),
    ("Носишь брэ́кеты или тя́ги?", 35.3, 36.9),  # stress marks: plain "брекеты" came out wrong
    ("Для них отдельные режимы: приложение напоминает и про чистку, и про тяги.", 36.95, 42.0),
    ("А у детей за каждую чистку монеты, на которые они покупают награды.", 42.05, 46.4),
    ("Чистить зубы становится игрой.", 46.45, 48.25),
    ("Родитель видит в своём телефоне, почистил ребёнок зубы или нет.", 48.3, 52.25),
    ("Пропустил, и приходит уведомление.", 52.3, 54.3),
    ("Даже если телефон ребёнка выключен.", 54.35, 56.5),
]
SETTINGS = {"stability": 0.45, "similarity_boost": 0.92, "style": 0.15, "use_speaker_boost": True}

def main(out):
    os.makedirs(out, exist_ok=True)
    for i, (text, s, e) in enumerate(PHRASES):
        body = {"text": text, "model_id": "eleven_multilingual_v2", "language_code": "ru", "voice_settings": SETTINGS,
                "previous_text": PHRASES[i - 1][0] if i else "Вот что получилось.",
                "next_text": PHRASES[i + 1][0] if i + 1 < len(PHRASES) else "Это ровно то, что я хотел."}
        json.dump(body, open(f"{out}/req.json", "w"), ensure_ascii=False)
        subprocess.run(["curl", "-sS", "-f", "-X", "POST",
                        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128",
                        "-H", "Content-Type: application/json", "--data-binary", f"@{out}/req.json",
                        "-o", f"{out}/p{i:02d}.mp3"], check=True)

if __name__ == "__main__":
    main(sys.argv[1])
