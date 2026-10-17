"""12 green screen: the speaker is keyed out of his room and stands in front of an app screen (here a
support inbox drowning in the same questions), placed lower and a bit smaller, like a creator over a
screenshot. Reference: @tenfoldmarc 12/17."""
import json
import numpy as np, cv2
from fxlib import person_mattes, over, transform, with_alpha, prog, ease_out, lerp, FPS, W, H

NAME_EN, NAME_RU = "green screen", "замена фона"

CSS = """
body{width:1080px;height:1920px;background:linear-gradient(180deg,#F6F4FF 0%,#F6F4FF 58%,#5B3DF5 58%,#3A1FD1 100%);
     font-family:Manrope;overflow:hidden}
#app{position:absolute;left:50px;right:50px;top:330px;height:860px;border-radius:30px;background:#fff;
     box-shadow:0 30px 70px rgba(40,20,120,.18);overflow:hidden}
.top{position:relative;z-index:2;display:flex;align-items:center;gap:14px;padding:22px 28px;background:#1E1B2E;color:#fff;font:700 30px Manrope}
.top b{margin-left:auto;padding:6px 16px;border-radius:20px;background:#FF4D5E;font:800 26px Unbounded}
#list{position:absolute;left:0;right:0;top:86px}
.it{display:flex;gap:18px;align-items:center;padding:18px 28px;border-bottom:1px solid #EEE;height:112px;background:#fff}
.av{width:66px;height:66px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;
    color:#fff;font:800 26px Unbounded}
.tx{flex:1;min-width:0}.nm{font:700 26px Manrope;color:#1E1B2E}.q{font:500 26px Manrope;color:#6E6A80;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tm{font:600 22px Manrope;color:#A09CB0;text-align:right}.tm i{display:block;margin-top:8px;margin-left:auto;width:34px;height:34px;border-radius:50%;
    background:#5B3DF5;color:#fff;font:800 18px/34px Manrope;text-align:center;font-style:normal}
#cap{position:absolute;left:0;right:0;top:232px;text-align:center;font:800 54px Unbounded;color:#1E1B2E}
#cap span{background:#FFE34D;padding:0 12px;border-radius:10px}
"""

JS = """
window.seek=t=>{
  const n=Math.max(0,Math.floor((t-CFG.flood)/CFG.every)); const L=document.getElementById('list');
  const frac=Math.min(1,((t-CFG.flood)/CFG.every)%1/0.35); const total=Math.min(CFG.q.length*6,n);
  let h='';
  for(let j=total;j>=Math.max(0,total-9);j--){const q=CFG.q[j%CFG.q.length], nm=CFG.n[j%CFG.n.length];
    h+=`<div class=it><div class=av style="background:${CFG.c[j%CFG.c.length]}">${nm[0]}</div><div class=tx><div class=nm>${nm}</div>`+
       `<div class=q>${q}</div></div><div class=tm>${j==total?'сейчас':(total-j)+' мин'}<i>${1+(j*7)%4}</i></div></div>`;}
  L.innerHTML=h; L.style.transform=`translateY(${(frac-1)*112}px)`;
  document.getElementById('cnt').textContent=CFG.base+total;
  const c=document.getElementById('cap'); c.style.opacity=t>=CFG.cap?1:0;
};
"""

DEMO = dict(t0=15.95, t1=20.95, swap=16.02, flood=16.3, every=0.32, cap=17.72,
            questions=["Когда следующий урок?", "Как оплатить курс?", "Не приходит доступ", "Когда следующий урок?",
                       "Можно оплатить частями?", "Где расписание?", "Не открывается урок", "Как оплатить курс?"],
            names=["Артур", "Магомед", "Ислам", "Тимур", "Руслан", "Ахмед", "Саид"],
            colors=["#5B3DF5", "#FF8A3D", "#2BB673", "#E5484D", "#1E9BD7"],
            caption='одни и те же <span>вопросы</span>', person_scale=0.82)


def frames(clip, html, t0, swap, flood, every, cap, questions, names, colors, caption, person_scale):
    body = (f'<div id=app><div class=top>Входящие <b id=cnt></b></div><div id=list></div></div>'
            f'<div id=cap>{caption}</div>')
    cfg = json.dumps(dict(flood=flood, every=every, cap=cap, q=questions, n=names, c=colors, base=31), ensure_ascii=False)
    times = [t0 + i / FPS for i in range(len(clip))]
    bgs = html.frames(body, CSS, f"const CFG={cfg};" + JS, times)
    mattes = person_mattes(clip)
    for i, bg in enumerate(bgs):
        t = times[i]
        f = clip.frame(i)
        k = ease_out(prog(t, swap, swap + 0.35))
        if k <= 0:
            yield f
            continue
        m = np.clip(mattes[i] * 1.08 - 0.04, 0, 1)
        s = lerp(1.0, person_scale, k)
        person = transform(with_alpha(f, m), s, 0, cx=W / 2, cy=H, tx=W / 2, ty=H)
        out = bg[..., :3].copy()
        # the room fades out as the app comes in
        room = transform(with_alpha(f, np.ones_like(m)), s, 0, cx=W / 2, cy=H, tx=W / 2, ty=H)
        over(out, room, opacity=1 - k)
        # light wrap: tint the matte edge with the new background so he sits in it
        edge = cv2.GaussianBlur(person[..., 3], (0, 0), 3) - cv2.erode(person[..., 3], np.ones((7, 7), np.uint8))
        person[..., :3] = person[..., :3] * (1 - 0.35 * np.clip(edge, 0, 1)[..., None]) + \
            cv2.GaussianBlur(out, (0, 0), 12) * 0.35 * np.clip(edge, 0, 1)[..., None]
        over(out, person)
        yield out
