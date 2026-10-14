# usage: python3 tts.py <workdir> <lang> [idx...]  -> <workdir>/tts/pN.mp3+json (en) or <workdir>/ru/tts/ (ru)
import json, sys, os, base64, subprocess, concurrent.futures as cf
V='BfVyIdPg9joQxukEjS3J'
wd,lang=sys.argv[1],sys.argv[2]
base=wd
os.makedirs(f'{base}/tts',exist_ok=True)
P=json.load(open(f'{base}/lines.json'))
def go(i):
    body={"text":P[i],"model_id":"eleven_multilingual_v2","language_code":"ru",
          "voice_settings":{"stability":0.45,"similarity_boost":1.0,"style":0.2,"use_speaker_boost":True,"speed":1.1}}
    req=f'{base}/tts/p{i}.req';open(req,'w').write(json.dumps(body,ensure_ascii=False))
    r=subprocess.run(['curl','-sS','-X','POST',f'https://api.elevenlabs.io/v1/text-to-speech/{V}/with-timestamps?output_format=mp3_44100_128','-H','Content-Type: application/json','--data-binary',f'@{req}'],capture_output=True,text=True)
    d=json.loads(r.stdout)
    if 'audio_base64' not in d: return i,r.stdout[:300]
    open(f'{base}/tts/p{i}.mp3','wb').write(base64.b64decode(d['audio_base64']))
    json.dump(d['alignment'],open(f'{base}/tts/p{i}.json','w'),ensure_ascii=False)
    return i,'ok'
only=[int(x) for x in sys.argv[3:]] or range(len(P))
with cf.ThreadPoolExecutor(2) as ex:
    for i,s in ex.map(go,only): print(i,s)
