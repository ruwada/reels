import json
S='/mnt/project-files/reels/anthropic-agenty/'
d = json.load(open(S+'words.json')); W = d['words']
en, j = [], 0
for first, txt in json.load(open(S+'en.json')):
    while W[j]['w'].strip('.,') != first: j += 1
    en.append([j, txt]); j += 1
s = open(S+'index.src.html').read()
s = s.replace('/*WORDS*/', json.dumps(d, ensure_ascii=False)).replace('/*EN*/', json.dumps(en, ensure_ascii=False)).replace('/*DUR*/', str(d['duration']))
open('index.html', 'w').write(s)
print([(W[i]['w'], t) for i, t in en])
