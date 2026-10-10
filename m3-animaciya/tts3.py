# One continuous TTS take (natural flow) with the approved clone -> tts3/<name>.mp3 + .json
import json, sys, base64, subprocess
V = 'BfVyIdPg9joQxukEjS3J'
L = json.load(open('lines.json'))
name, stab, style, speed = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
body = {"text": " ".join(L), "model_id": "eleven_multilingual_v2", "language_code": "ru",
        "voice_settings": {"stability": stab, "similarity_boost": 1.0, "style": style, "use_speaker_boost": True, "speed": speed}}
open(f'tts3/{name}.req', 'w').write(json.dumps(body, ensure_ascii=False))
r = subprocess.run(['curl', '-sS', '-X', 'POST', f'https://api.elevenlabs.io/v1/text-to-speech/{V}/with-timestamps?output_format=mp3_44100_128',
                    '-H', 'Content-Type: application/json', '--data-binary', f'@tts3/{name}.req'], capture_output=True, text=True)
d = json.loads(r.stdout)
if 'audio_base64' not in d: print(r.stdout[:300]); sys.exit(1)
open(f'tts3/{name}.mp3', 'wb').write(base64.b64decode(d['audio_base64']))
json.dump(d['alignment'], open(f'tts3/{name}.json', 'w'), ensure_ascii=False)
print(name, d['alignment']['character_end_times_seconds'][-1])
