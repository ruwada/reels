import json,base64,subprocess,sys
P=json.load(open('lines.json'))
def ask(i,model):
    a=base64.b64encode(open(f'tts/p{i}.mp3','rb').read()).decode()
    prompt=("Ты фонетист русского языка. Послушай аудио. Ожидаемый текст с правильными ударениями: "+P[i]+
     "\nПроверь КАЖДОЕ слово: где диктор фактически поставил ударение. Выведи только список слов, где фактическое ударение НЕ совпадает с правильным, в формате: слово — услышано: …, правильно: …. Если всё верно, выведи ОК. Будь строг, но не выдумывай.")
    body={"contents":[{"parts":[{"inline_data":{"mime_type":"audio/mp3","data":a}},{"text":prompt}]}]}
    open('/tmp/g.json','w').write(json.dumps(body,ensure_ascii=False))
    r=subprocess.run(['curl','-sS',f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent','-H','Content-Type: application/json','-H','x-goog-api-key: dummy','--data-binary','@/tmp/g.json'],capture_output=True,text=True)
    d=json.loads(r.stdout)
    try: return d['candidates'][0]['content']['parts'][-1]['text']
    except Exception: return r.stdout[:300]
m=sys.argv[1]
for i in (sys.argv[2:] or range(len(P))): print(i, ask(int(i),m).strip(), sep=': ')
