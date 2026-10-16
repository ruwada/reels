import json,sys
D=json.load(open('data.json'));EN=json.load(open('en.json'))
C=['#3DF5A0','#FFD166','#7CC8FF','#FF8A7A','#C9A7FF','#9BE564']
names=[("Магомед","Цена 48 000 — только для вас","3"),("Руслан","Скидку 15% держу до пятницы","1"),("Тимур","Отгрузка 24-го, как договорились","2"),("ООО «Строймаркет»","Счёт выставлю со своего, ок?","5"),("Ахмед","Пришлите реквизиты","1"),("Ислам","Беру 40 штук, если по 1 200","4"),("Карим","Когда будет поставка?","2"),("Саид","Договорились, жду предоплату","1"),("Билал","Можно в рассрочку?","3"),("Юсуф","Перезвоните мне","1"),("Амир","Сделаете как в прошлый раз?","2"),("Хасан","Ок, по старой цене","1"),("Мурад","Где мой заказ?","6"),("Рамазан","Скинул оплату","1")]
rows=''.join(f'<div class="row"><div class="a" style="background:{C[i%6]}">{n[0][0]}</div><div class="t"><div class="nm">{n[0]}</div><div class="sn">{n[1]}</div></div><div class="bd">{n[2]}</div></div>' for i,n in enumerate(names))
cnt=''.join(f'<span>{v}</span>' for v in [0,12,37,68,104,141,176,209,238,262,281,293,300])
dots=''.join(f'<div class="dot" style="left:{680+(i%4)*40}px;top:{720+(i//4)*50}px;background:{C[i%6]};color:#0C1210">{n[0][0]}</div>' for i,n in enumerate(names[:8]))
cl=''.join(f'<div class="cl" style="left:{150+i*140-43}px;background:{C[i%6]}">{n[0][0]}</div>' for i,n in enumerate(names[:6]))
chk='<svg width="30" height="30" viewBox="0 0 24 24"><path d="M4 12.5l5 5L20 6.5" fill="none" stroke="#0E8F57" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
evs=[("Цена 48 000 ₽ — для вас","менеджер Артём · 12.09"),("Скидка 15% до пятницы","менеджер Артём · 03.10"),("Отгрузка 24.10, оплачено","менеджер Тимур · сегодня")]
ev=''.join(f'<div class="ev"><div class="ic">{chk}</div><div style="flex:1"><div class="tx">{a.replace(" ₽","")}</div><div class="who">{b}</div></div><div class="ok">сохранено</div></div>' for a,b in evs)
s=open('index.tpl.html').read()
for a,b in [('/*DATA*/',json.dumps(D,ensure_ascii=False)),('/*EN*/',json.dumps(EN,ensure_ascii=False)),('/*END*/',str(D['END'])),('/*ROWS*/',rows),('/*CNT*/',cnt),('/*DOTS*/',dots),('/*CL*/',cl),('/*EV*/',ev)]:
    s=s.replace(a,b)
open(sys.argv[1],'w').write(s)
