import json,sys
D=json.load(open('data.json'));EN=json.load(open('en.json'))
names=["Ахмад","Ислам","Руслан","Тимур","Карим","Билал","Юсуф","Мурад","Саид","Амир","Рамазан","Хасан"]
feed=''.join(f'<div class="b"><div class="to">→ {n}</div>Напоминаем, завтра в {14+i%4}:00. Придёте?<div class="tk">✓✓</div></div>' for i,n in enumerate(names))
fmt=lambda v:f"{v:,}".replace(","," ")
cnt=''.join(f'<span>{i}</span>' for i in range(0,41))
tot=''.join(f'<span>{fmt(v)} ₽</span>' for v in [0,6000,18000,32000,52000,74000,96000,118000,134000,146000,152000,156000])
zero=''.join(f'<span>{i}</span>' for i in [40,33,25,17,10,5,2,0])
s=open('index.tpl.html').read()
for a,b in [('/*DATA*/',json.dumps(D,ensure_ascii=False)),('/*EN*/',json.dumps(EN,ensure_ascii=False)),('/*END*/',str(D['END'])),('/*FEED*/',feed),('/*CNT*/',cnt),('/*TOT*/',tot),('/*ZERO*/',zero)]:
    s=s.replace(a,b)
open(sys.argv[1],'w').write(s)
