import json
d = json.load(open('words.json')); W = d['words']; PH = d['phrases']
en, j = [], 0
for first, txt in json.load(open('en.json')):
    while W[j]['w'].strip('.,:') != first.strip('.,:'): j += 1
    en.append([j, txt]); j += 1
P0 = lambda p: round(PH[p]['s'] - .02, 3)
s = open('index.src.html').read()
s = s.replace('/*WORDS*/', json.dumps(d, ensure_ascii=False)).replace('/*EN*/', json.dumps(en, ensure_ascii=False)).replace('/*DUR*/', str(d['duration']))
for k, p in (('S2A', 3), ('S4A', 6), ('S6A', 10), ('S7A', 11), ('S8A', 12)): s = s.replace(f'/*{k}*/', str(P0(p)))
open('code/index.html', 'w').write(s)
print([(W[i]['w'], t) for i, t in en])
