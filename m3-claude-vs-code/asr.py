# Checks each TTS phrase by ear: Gemini transcribes the mp3 verbatim.
import json, sys, base64, subprocess
for f in sys.argv[1:]:
    b = base64.b64encode(open(f,'rb').read()).decode()
    body = {"contents":[{"parts":[{"inline_data":{"mime_type":"audio/mpeg","data":b}},
      {"text":"Транскрибируй русскую речь дословно, как слышно, без исправлений. Иностранные слова пиши кириллицей так, как они звучат. Только текст."}]}]}
    open('/tmp/asr.req','w').write(json.dumps(body))
    r = subprocess.run(['curl','-sS','https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent','-H','Content-Type: application/json','--data-binary','@/tmp/asr.req'],capture_output=True,text=True)
    try: print(f, '|', json.loads(r.stdout)['candidates'][0]['content']['parts'][0]['text'].strip())
    except Exception: print(f, r.stdout[:300])
