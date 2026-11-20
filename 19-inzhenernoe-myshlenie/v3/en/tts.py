#!/usr/bin/env python3
"""English voice-over in the user's cloned voice: one ElevenLabs take per Russian sentence (with context)."""
import base64, json, os, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); out = sys.argv[1]; os.makedirs(out, exist_ok=True)
L = json.load(open(os.path.join(HERE, "lines.json")))
VOICE = "BfVyIdPg9joQxukEjS3J"  # islam.devai-2, approved by the user
for i, t in enumerate(L):
    p = os.path.join(out, f"s{i:02d}.json")
    if os.path.exists(p): continue
    body = {"text": t, "model_id": "eleven_multilingual_v2", "language_code": "en",
            "previous_text": " ".join(L[max(0, i - 2):i]), "next_text": " ".join(L[i + 1:i + 2]),
            "voice_settings": {"stability": 0.45, "similarity_boost": 1.0, "style": 0.2, "use_speaker_boost": True, "speed": 1.1}}
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_128",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req))
    open(os.path.join(out, f"s{i:02d}.mp3"), "wb").write(base64.b64decode(r["audio_base64"]))
    json.dump(r["alignment"], open(p, "w"))
    print(i, t)
