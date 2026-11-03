# TTS with the user's ElevenLabs clone + character timings -> tts/pN.mp3, tts/pN.json
import json, sys, base64, subprocess, concurrent.futures as cf
V = 'BfVyIdPg9joQxukEjS3J'
P = json.load(open('lines.json'))
def go(i, text):
    body = {"text": text, "model_id": "eleven_multilingual_v2", "language_code": "ru",
            "voice_settings": {"stability": 0.5, "similarity_boost": 1.0, "style": 0, "use_speaker_boost": True}}
    open(f'tts/p{i}.req', 'w').write(json.dumps(body, ensure_ascii=False))
    r = subprocess.run(['curl', '-sS', '-X', 'POST', f'https://api.elevenlabs.io/v1/text-to-speech/{V}/with-timestamps?output_format=mp3_44100_128',
                        '-H', 'Content-Type: application/json', '--data-binary', f'@tts/p{i}.req'], capture_output=True, text=True)
    d = json.loads(r.stdout)
    if 'audio_base64' not in d: return i, r.stdout[:300]
    open(f'tts/p{i}.mp3', 'wb').write(base64.b64decode(d['audio_base64']))
    json.dump(d['alignment'], open(f'tts/p{i}.json', 'w'), ensure_ascii=False)
    return i, 'ok'
only = [int(x) for x in sys.argv[1:]] or range(len(P))
with cf.ThreadPoolExecutor(2) as ex:
    for i, s in ex.map(lambda i: go(i, P[i]), only): print(i, s)
