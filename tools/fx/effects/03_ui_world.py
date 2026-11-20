"""03 ui world: the screen splits; an app interface slides in on top (files fly into a drop zone, a command
gets typed, results tick in) while the speaker continues in the bottom half. Reference: @tenfoldmarc 03/17."""
import numpy as np, cv2
from fxlib import person_mattes, head_track, over, prog, ease_out, ease_in_out, lerp, FPS, W, H

NAME_EN, NAME_RU = "ui world", "мир интерфейса"

CSS = """
body{width:1080px;height:1920px;overflow:hidden}
#ui{position:absolute;left:0;top:0;width:1080px;height:980px;background:#F6F1E7;color:#1D1A16;font:600 30px Manrope;
    border-bottom:1px solid rgba(0,0,0,.08)}
.brand{position:absolute;top:250px;left:0;right:0;text-align:center;font:700 40px 'Playfair Display';letter-spacing:.01em}
.brand b{color:#D9622B;font-family:Manrope}
#box{position:absolute;left:70px;right:70px;top:330px;height:400px;border-radius:34px;background:#fff;
     box-shadow:0 20px 50px rgba(60,40,10,.12);border:2px solid rgba(0,0,0,.06)}
#drop{position:absolute;left:28px;right:28px;top:28px;height:200px;border-radius:24px;border:3px dashed rgba(0,0,0,.18);
      display:flex;align-items:center;justify-content:center;color:rgba(0,0,0,.4);font:600 30px Manrope}
.file{position:absolute;width:150px;height:186px;border-radius:18px;background:#fff;box-shadow:0 10px 26px rgba(0,0,0,.18);
      display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;font:700 22px Manrope}
.file i{display:block;width:84px;height:100px;border-radius:12px;font:800 26px Unbounded;color:#fff;font-style:normal;
        display:flex;align-items:center;justify-content:center}
#tag{position:absolute;top:-24px;right:40px;padding:12px 20px;border-radius:12px;background:#FFE34D;font:800 26px Unbounded}
#input{position:absolute;left:34px;right:34px;bottom:30px;height:90px;border-radius:20px;background:#F4F1EC;
       display:flex;align-items:center;padding:0 28px;font:600 34px Manrope;color:#1D1A16}
#input span.ph{color:rgba(0,0,0,.35)}
#send{position:absolute;right:26px;bottom:18px;width:56px;height:56px;border-radius:16px;background:#D9622B}
.res{position:absolute;left:90px;display:flex;align-items:center;gap:18px;font:700 32px Manrope;opacity:0}
.res em{width:44px;height:44px;border-radius:50%;background:#2BB673;display:flex;align-items:center;justify-content:center;
        color:#fff;font:800 26px Manrope;font-style:normal}
"""


def body(files, results):
    fh = "".join(f'<div class=file id=f{j}><i style="background:{c}">{e}</i>{n}</div>' for j, (n, e, c, _) in enumerate(files))
    rh = "".join(f'<div class=res id=r{j} style="top:{760 + j * 52}px"><em>✓</em>{txt}</div>' for j, (txt, _) in enumerate(results))
    return (f'<div id=ui><div class=brand><b>✳</b> AI-ассистент</div><div id=box><div id=drop>Перетащите файлы сюда</div>'
            f'<div id=tag>МАТЕРИАЛЫ</div><div id=input><span id=txt></span></div><div id=send></div></div>{rh}</div>{fh}')


JS = """
const E=t=>1-Math.pow(1-Math.min(1,Math.max(0,t)),3);
window.seek=t=>{
  const ui=document.getElementById('ui'); const k=E((t-CFG.split)/0.55);
  ui.style.transform=`translateY(${(k-1)*1000}px)`;
  CFG.files.forEach((f,j)=>{const el=document.getElementById('f'+j); const p=E((t-f[3])/0.55);
    const x0=180+j*260, y0=1500, x1=110+j*172, y1=(k-1)*1000+358;
    el.style.left=(x0+(x1-x0)*p)+'px'; el.style.top=(y0+(y1-y0)*p - Math.sin(p*Math.PI)*260)+'px';
    el.style.transform=`rotate(${(1-p)*(-14+j*9)}deg) scale(${1-0.12*p})`; el.style.opacity=t<f[3]?0:1;});
  document.getElementById('drop').style.color=t>CFG.files[0][3]+0.3?'transparent':'rgba(0,0,0,.4)';
  const tg=document.getElementById('tag'); const tp=E((t-CFG.tag)/0.3); tg.style.opacity=tp; tg.style.transform=`scale(${0.6+0.4*tp})`;
  const s=CFG.cmd, n=Math.max(0,Math.min(s.length,Math.floor((t-CFG.type)*22)));
  document.getElementById('txt').innerHTML = t<CFG.type?'<span class=ph>Чем помочь?</span>':s.slice(0,n)+(Math.floor(t*3)%2?'|':'');
  CFG.results.forEach((r,j)=>{const el=document.getElementById('r'+j); const p=E((t-r[1])/0.35);
    el.style.opacity=p; el.style.transform=`translateX(${(1-p)*-40}px)`;});
};
"""

DEMO = dict(t0=21.30, t1=27.95, split=21.40,
            files=[("урок 5", "PDF", "#E5484D", 21.75), ("урок 6", "PDF", "#E5484D", 21.95),
                   ("расписание", "XLS", "#2BB673", 22.15), ("FAQ", "TXT", "#5B6CFF", 22.35)],
            tag=22.55, type=22.65, cmd="/агент-школы отвечай ученикам",
            results=[("ответил за 0,8 сек", 23.66), ("выдал материалы", 24.62),
                     ("напомнил о занятии", 25.54), ("собрал обратную связь", 26.82)])


def frames(clip, html, t0, split, files, tag, type, cmd, results):
    import json
    cfg = json.dumps(dict(split=split, files=files, tag=tag, type=type, cmd=cmd, results=results), ensure_ascii=False)
    times = [t0 + i / FPS for i in range(len(clip))]
    uis = html.frames(body(files, results), CSS, f"const CFG={cfg};" + JS, times)
    heads = head_track(person_mattes(clip))
    y_face = float(np.median([h[1] for h in heads]))
    for i, ui in enumerate(uis):
        t = times[i]
        f = clip.frame(i)
        k = ease_in_out(prog(t, split, split + 0.55))
        # the video slides down so that the speaker's head lands just under the interface
        shift = int(k * (960 - (y_face - 140)))
        out = np.full_like(f, 0.08)
        if shift >= 0:
            out[shift:] = f[:H - shift]
        else:
            out[:H + shift] = f[-shift:]
        over(out, ui)
        yield out
