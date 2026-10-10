import base64,json,subprocess,sys
for n in sys.argv[1:]:
    b=base64.b64encode(open(f'tts/{n}.mp3','rb').read()).decode()
    body={"contents":[{"parts":[{"inline_data":{"mime_type":"audio/mpeg","data":b}},{"text":"Transcribe this Russian audio verbatim, exactly as pronounced, including any mispronunciations, swallowed or garbled words. Output only the transcript."}]}]}
    open('/tmp/claude-0/asr.json','w').write(json.dumps(body))
    r=subprocess.run(['curl','-sS','-X','POST','https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent','-H','Content-Type: application/json','--data-binary','@/tmp/claude-0/asr.json'],capture_output=True,text=True)
    try: print(n, json.loads(r.stdout)['candidates'][0]['content']['parts'][0]['text'])
    except Exception: print(n, r.stdout[:300])
