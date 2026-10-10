# Asks Gemini to judge each take by ear: stress errors, robotic spots, odd intonation; score 1-10.
import json, sys, base64, subprocess
P = "Это озвучка рилса синтезированным голосом мужчины, носителя русского. Текст: «{t}». Оцени по слуху строго: 1) неверные ударения, 2) роботизированные или металлические места, проглоченные или искажённые слова, 3) неестественная интонация (вопрос без вопросительной интонации, странные паузы, монотонность). Ответь JSON: {{\"score\": 1-10 (10 = звучит как живой человек), \"issues\": [\"слово: проблема\", ...]}}"
L = json.load(open('lines.json'))
for f in sys.argv[1:]:
    i = int(f.split('/p')[-1].split('_')[0].split('.')[0])
    b = base64.b64encode(open(f,'rb').read()).decode()
    body = {"contents":[{"parts":[{"inline_data":{"mime_type":"audio/mpeg","data":b}},{"text":P.format(t=L[i])}]}],
            "generationConfig":{"responseMimeType":"application/json","temperature":0}}
    open('/tmp/rate.req','w').write(json.dumps(body))
    r = subprocess.run(['curl','-sS','https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent','-H','Content-Type: application/json','--data-binary','@/tmp/rate.req'],capture_output=True,text=True)
    try: print(f, json.loads(r.stdout)['candidates'][0]['content']['parts'][0]['text'].replace('\n',' '))
    except Exception: print(f, r.stdout[:200])
