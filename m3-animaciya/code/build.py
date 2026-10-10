# ../index.src.html + ../words.json + ../en.json -> index.html
import json
d = json.load(open('../words.json')); W = d['words']
en, j = [], 0
for first, txt in json.load(open('../en.json')):
    while W[j]['w'].strip('.,') != first: j += 1
    en.append([j, txt]); j += 1
s = open('../index.src.html').read()
s = s.replace('/*WORDS*/', json.dumps(d, ensure_ascii=False)).replace('/*EN*/', json.dumps(en, ensure_ascii=False)).replace('/*DUR*/', str(d['duration']))
open('index.html', 'w').write(s)
print([(W[i]['w'], t) for i, t in en])
