# Several TTS takes per phrase with neighbour context (smoother intonation) -> tts/pI_K.mp3 + .json
import json, sys, base64, subprocess, concurrent.futures as cf
V = 'BfVyIdPg9joQxukEjS3J'
L = json.load(open('lines.json'))
VAR = [(0.5, 0.0), (0.5, 0.0), (0.4, 0.1), (0.4, 0.1), (0.4, 0.1), (0.4, 0.1)] + [(0.5, 0.0)] * 6
KS = [int(k) for k in __import__("os").environ.get("KS", "0,1,2,3").split(",")]
def go(job):
    i, k = job; st, sy = VAR[k]
    body = {"text": L[i], "model_id": "eleven_multilingual_v2", "language_code": "ru",
            "previous_text": " ".join(L[max(0, i-2):i]) or None, "next_text": L[i+1] if i+1 < len(L) else None,
            "voice_settings": {"stability": st, "similarity_boost": 1.0, "style": sy, "use_speaker_boost": True}}
    body = {a: b for a, b in body.items() if b is not None}
    req = f'tts/p{i}_{k}.req'; open(req, 'w').write(json.dumps(body, ensure_ascii=False))
    r = subprocess.run(['curl', '-sS', '-X', 'POST', f'https://api.elevenlabs.io/v1/text-to-speech/{V}/with-timestamps?output_format=mp3_44100_128',
                        '-H', 'Content-Type: application/json', '--data-binary', f'@{req}'], capture_output=True, text=True)
    d = json.loads(r.stdout)
    if 'audio_base64' not in d: return job, r.stdout[:200]
    open(f'tts/p{i}_{k}.mp3', 'wb').write(base64.b64decode(d['audio_base64']))
    json.dump(d['alignment'], open(f'tts/p{i}_{k}.json', 'w'), ensure_ascii=False)
    return job, 'ok'
only = [int(x) for x in sys.argv[1:]] or range(len(L))
with cf.ThreadPoolExecutor(3) as ex:
    for j, s in ex.map(go, [(i, k) for i in only for k in KS]): print(j, s)
