# For each phrase: real-voice sample + 4 takes -> Gemini picks the most natural take, closest to the real speaker.
import json, base64, subprocess, sys
L = json.load(open('lines.json'))
real = base64.b64encode(open('/tmp/real.mp3','rb').read()).decode()
res = json.load(open('pick.json')) if len(sys.argv) > 1 else {}
CAND = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {str(i): [0, 1, 2, 3] for i in range(len(L))}
for i in map(int, CAND):
    parts = [{"text": "Аудио 0: живой голос автора (эталон)."}, {"inline_data": {"mime_type": "audio/mpeg", "data": real}}]
    ks = CAND[str(i)]
    for k in ks:
        parts += [{"text": f"Дубль {k}:"}, {"inline_data": {"mime_type": "audio/mpeg", "data": base64.b64encode(open(f'tts/p{i}_{k}.mp3','rb').read()).decode()}}]
    parts.append({"text": f"{len(ks)} дублей синтеза фразы «{L[i]}» для рилса. Сравни строго по слуху: естественность и живая интонация, правильные ударения, нет роботизированности/металла/проглоченных слов, похожесть на эталон. Ответь JSON: {{\"best\": номер, \"scores\": [оценки 1-10 по порядку], \"why\": \"коротко\", \"issues_best\": \"что не так в лучшем, или пусто\"}}"})
    body = {"contents": [{"parts": parts}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
    open('/tmp/pick.req', 'w').write(json.dumps(body))
    r = subprocess.run(['curl', '-sS', 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent', '-H', 'Content-Type: application/json', '--data-binary', '@/tmp/pick.req'], capture_output=True, text=True)
    try: d = json.loads(json.loads(r.stdout)['candidates'][0]['content']['parts'][0]['text']); d['best'] = ks[d['best']] if d['best'] < len(ks) else d['best']; res[str(i)] = d; print(i, d)
    except Exception: print(i, r.stdout[:200])
json.dump(res, open('pick.json', 'w'), ensure_ascii=False, indent=1)
