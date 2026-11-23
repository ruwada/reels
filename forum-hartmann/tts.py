import json, sys, base64, subprocess, concurrent.futures as cf
V='BfVyIdPg9joQxukEjS3J'; P=json.load(open('lines.json'))
def go(i):
    body={"text":P[i],"model_id":"eleven_multilingual_v2","language_code":"ru",
          "voice_settings":{"stability":0.45,"similarity_boost":1.0,"style":0.2,"use_speaker_boost":True,"speed":1.1}}
    open(f'tts/p{i}.req','w').write(json.dumps(body,ensure_ascii=False))
    r=subprocess.run(['curl','-sS','-X','POST',f'https://api.elevenlabs.io/v1/text-to-speech/{V}/with-timestamps?output_format=mp3_44100_128','-H','Content-Type: application/json','--data-binary',f'@tts/p{i}.req'],capture_output=True,text=True)
    try: d=json.loads(r.stdout)
    except Exception: return i, r.stdout[:200]
    if 'audio_base64' not in d: return i, r.stdout[:300]
    open(f'tts/p{i}.mp3','wb').write(base64.b64decode(d['audio_base64'])); json.dump(d['alignment'],open(f'tts/p{i}.json','w'),ensure_ascii=False)
    return i,'ok'
only=[int(x) for x in sys.argv[1:]] or range(len(P))
with cf.ThreadPoolExecutor(2) as ex:
    for i,s in ex.map(go,only): print(i,s)
