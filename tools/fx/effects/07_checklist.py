"""07 checklist: a dark glass panel ("всё, что нужно · 0 из N") drops in at the top; each item types itself
in on its word and gets a check, the counter ticks up. Reference: @tenfoldmarc 07/17."""
import json
from fxlib import over, frost, prog, ease_out, FPS, W, H

NAME_EN, NAME_RU = "checklist", "чек-лист"

CSS = """
body{width:1080px;height:1920px}
#p{position:absolute;left:90px;right:90px;top:1060px;border-radius:30px;padding:26px 34px 18px;
   background:rgba(20,22,27,.78);backdrop-filter:blur(18px);border:1.5px solid rgba(255,255,255,.12);
   box-shadow:0 30px 60px rgba(0,0,0,.35);color:#fff;font:700 38px Manrope}
.hd{display:flex;justify-content:space-between;font:800 20px Unbounded;letter-spacing:.12em;color:rgba(255,255,255,.55);margin-bottom:14px}
.hd b{color:#C8F25A}
.row{display:flex;align-items:center;gap:22px;height:74px;border-top:1px solid rgba(255,255,255,.07)}
.bx{width:42px;height:42px;border-radius:50%;border:3px solid rgba(255,255,255,.45);flex:none;position:relative}
.bx.on{background:#C8F25A;border-color:#C8F25A}
.bx svg{position:absolute;inset:6px}
.ln{height:14px;border-radius:7px;background:rgba(255,255,255,.12)}
.tx{white-space:nowrap}
.bar{height:6px;border-radius:3px;background:rgba(255,255,255,.1);margin-top:10px}
.bar i{display:block;height:100%;border-radius:3px;background:#C8F25A}
"""

JS = """
const E=t=>1-Math.pow(1-Math.min(1,Math.max(0,t)),3);
window.seek=t=>{
  const p=document.getElementById('p'); const k=E((t-CFG.enter)/0.5);
  p.style.opacity=k; p.style.transform=`translateY(${(1-k)*60}px) scale(${0.96+0.04*k})`;
  let done=0;
  CFG.items.forEach((it,j)=>{
    const [txt,ts,tc]=it; const tx=document.getElementById('t'+j), ln=document.getElementById('l'+j), bx=document.getElementById('b'+j);
    const n=Math.max(0,Math.min(txt.length,Math.floor((t-ts)*40)));
    tx.textContent=txt.slice(0,n); ln.style.display=n?'none':'block';
    const on=t>=tc; bx.className='bx'+(on?' on':''); if(on) done++;
    const ck=document.getElementById('c'+j); const q=E((t-tc)/0.2); ck.style.strokeDashoffset=40*(1-q);
    bx.style.transform=`scale(${on?1+0.25*Math.sin(Math.min(1,(t-tc)/0.25)*Math.PI):1})`;
  });
  document.getElementById('n').textContent=done+' из '+CFG.items.length;
  document.getElementById('bar').style.width=(100*done/CFG.items.length)+'%';
};
"""

DEMO = dict(t0=38.00, t1=43.40, enter=38.05, title="АГЕНТ ДЕЛАЕТ САМ",
            # text, starts typing, gets checked
            items=[("Квалифицирует лида", 38.17, 38.85), ("Заносит в CRM", 39.68, 40.30),
                   ("Готовит КП", 40.68, 41.30), ("Формирует отчёт", 41.84, 42.70)])


def frames(clip, html, t0, enter, title, items):
    rows = "".join(
        f'<div class=row><div class=bx id=b{j}><svg viewBox="0 0 30 30"><path id=c{j} d="M6 15 L13 22 L25 8" fill="none" '
        f'stroke="#14161B" stroke-width="4" stroke-linecap="round" stroke-dasharray="40" stroke-dashoffset="40"/></svg></div>'
        f'<span class=tx id=t{j}></span><div class=ln id=l{j} style="width:{300 + 60 * (j % 3)}px"></div></div>'
        for j in range(len(items)))
    body = f'<div id=p><div class=hd><span>● {title}</span><b id=n></b></div>{rows}<div class=bar><i id=bar></i></div></div>'
    cfg = json.dumps(dict(enter=enter, items=items), ensure_ascii=False)
    times = [t0 + i / FPS for i in range(len(clip))]
    for i, ui in enumerate(html.frames(body, CSS, f"const CFG={cfg};" + JS, times)):
        out = frost(clip.frame(i), ui[..., 3])
        over(out, ui)
        yield out
