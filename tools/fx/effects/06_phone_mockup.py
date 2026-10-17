"""06 phone mockup: a phone floats next to the speaker's head, slightly turned in 3D, with a live app
screen: a message arrives, a button gets tapped, the result appears. Reference: @tenfoldmarc 06/17."""
import json, math
import numpy as np, cv2
from fxlib import (person_mattes, head_track, over, warp_quad, card_quad, shadow, person_over, prog, ease_out,
                   ease_out_back, lerp, FPS, W, H)

NAME_EN, NAME_RU = "phone mockup", "телефон рядом"

PW, PH = 420, 870
CSS = f"""
body{{width:{PW}px;height:{PH}px}}
#ph{{position:absolute;inset:0;border-radius:64px;background:#0C0D10;padding:14px;
     box-shadow:inset 0 0 0 3px #3A3D45, inset 0 0 0 6px #121317}}
#sc{{position:absolute;inset:14px;border-radius:52px;overflow:hidden;background:#17181C;color:#EDEFF3;font:500 24px/1.35 Manrope}}
#isl{{position:absolute;top:26px;left:50%;width:120px;height:34px;margin-left:-60px;border-radius:20px;background:#000;z-index:5}}
.st{{display:flex;justify-content:space-between;padding:22px 34px 0;font:700 19px Manrope}}
.hd{{display:flex;align-items:center;gap:12px;padding:46px 22px 14px;border-bottom:1px solid rgba(255,255,255,.07)}}
.av{{width:46px;height:46px;border-radius:50%;background:#2AABEE;display:flex;align-items:center;justify-content:center;font:800 20px Unbounded;color:#fff}}
.nm{{font:700 21px Manrope}} .sub{{font:500 16px Manrope;opacity:.55}}
.msg{{margin:14px 16px;padding:16px 18px;border-radius:20px;background:#22252C;opacity:0}}
.msg b{{display:block;font:800 22px Manrope;margin-bottom:6px}}
.btns{{display:flex;gap:10px;margin-top:12px}}
.bt{{flex:1;text-align:center;padding:12px 0;border-radius:14px;background:#2AABEE;color:#fff;font:700 19px Manrope}}
.bt.g{{background:rgba(255,255,255,.08);color:#cfd3dc}}
#cur{{position:absolute;width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,.75);
      box-shadow:0 0 0 6px rgba(255,255,255,.25);opacity:0;z-index:9}}
.ok{{color:#2BD576;font:800 21px Manrope}}
"""


def body(chat, msgs):
    m = "".join(f'<div class=msg id=m{j}>{x["html"]}</div>' for j, x in enumerate(msgs))
    return (f'<div id=ph><div id=isl></div><div id=sc><div class=st><span>9:41</span><span>●●● ▮</span></div>'
            f'<div class=hd><div class=av>{chat[0]}</div><div><div class=nm>{chat}</div><div class=sub>бот · онлайн</div></div></div>'
            f'{m}<div id=cur></div></div></div>')


JS = """
const E=t=>1-Math.pow(1-Math.min(1,Math.max(0,t)),3);
window.seek=t=>{
  CFG.msgs.forEach((x,j)=>{const el=document.getElementById('m'+j);const p=E((t-x.t)/0.35);
    el.style.opacity=p; el.style.transform=`translateY(${(1-p)*24}px)`;});
  const c=document.getElementById('cur'), tp=CFG.tap;
  const p=E((t-(tp-0.6))/0.6); c.style.opacity=t<tp-0.6||t>tp+0.5?0:1;
  c.style.left=(330+(CFG.tapX-330)*p)+'px'; c.style.top=(780+(CFG.tapY-780)*p)+'px';
  const press=t>tp&&t<tp+0.18; c.style.transform=`scale(${press?0.75:1})`;
  const b=document.getElementById('tapbtn'); if(b) b.style.filter=press?'brightness(1.35)':'none';
};
"""

DEMO = dict(t0=76.85, t1=80.10, enter=76.90, chat="Islam Dev AI",
            msgs=[dict(t=77.0, html='<b>Гайд: агент под вашу нишу</b>Схема, промпты и чек-лист запуска.'
                                    '<div class=btns><div class=bt id=tapbtn>Открыть</div><div class="bt g">Позже</div></div>'),
                  dict(t=79.35, html='<span class=ok>✓ Гайд открыт</span><br>Начните с шага 1: что повторяется.')],
            tap=78.95, tap_xy=(100, 290))


def frames(clip, html, t0, enter, chat, msgs, tap, tap_xy):
    cfg = json.dumps(dict(msgs=msgs, tap=tap, tapX=tap_xy[0], tapY=tap_xy[1]), ensure_ascii=False)
    times = [t0 + i / FPS for i in range(len(clip))]
    screens = html.frames(body(chat, msgs), CSS, f"const CFG={cfg};" + JS, times, size=(PW, PH))
    mattes = person_mattes(clip)
    heads = head_track(mattes)
    for i, ph in enumerate(screens):
        t = times[i]
        f = clip.frame(i)
        hx, hy, hw = heads[i]
        k = prog(t, enter, enter + 0.7)
        if k <= 0:
            yield f
            continue
        s = ease_out_back(k, 1.2) * 0.74
        cx = max(hx + 0.62 * hw + PW * 0.37, min(W - 130 - PW * 0.37, hx + 1.3 * hw))
        cy = hy + 2.0 * hw + 120 * (1 - ease_out(k)) + 10 * math.sin(t * 2.1)
        q = card_quad(cx, cy, PW * s, PH * s, ry=lerp(-38, -16, ease_out(k)) + 3 * math.sin(t * 1.3), rx=4, rz=3)
        layer = warp_quad(ph, q)
        layer[..., 3] *= min(1, k * 3)
        out = f.copy()                             # the phone floats in front, beside his head, readable
        over(out, shadow(layer, blur=26, opacity=0.5, dx=-18, dy=26))
        over(out, layer)
        yield out
