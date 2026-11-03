"""11 pull-back reveal: we start full-screen on the speaker, then the camera pulls back and reveals that
the shot is playing inside an editor window: a task list ticks off, the render counter climbs, the
timeline fills and turns green at 100. Reference: @tenfoldmarc 11/17."""
import json
import numpy as np, cv2
from fxlib import over, rounded_mask, prog, ease_in_out, lerp, FPS, W, H

NAME_EN, NAME_RU = "pull-back reveal", "отъезд с раскрытием"

SLOT = (330, 400, 600, 1067)          # x, y, w, h of the video inside the editor (canvas px)

BASE_CSS = """
body{width:1080px;height:1920px;background:#EFEAE0}
#win{position:absolute;left:300px;top:330px;width:660px;height:1340px;border-radius:30px;background:#fff;
     box-shadow:0 40px 90px rgba(70,50,20,.18);border:1.5px solid rgba(0,0,0,.06)}
.tb{height:56px;display:flex;align-items:center;gap:10px;padding:0 22px;font:600 20px Manrope;color:#6b655c}
.tb i{width:13px;height:13px;border-radius:50%;background:#E3DED4;display:block}
.tb .nm{margin-left:auto;margin-right:auto;font:700 20px Manrope;color:#2b2722}
.tb .as{font:700 20px Manrope;color:#2b2722}
#slot{position:absolute;left:30px;top:70px;width:600px;height:1067px;border-radius:18px;background:#1b1b1b}
"""

TOP_CSS = """
body{width:1080px;height:1920px}
#tl{position:absolute;left:330px;top:1490px;width:600px;height:150px;border-radius:16px;background:#F5F2EC;padding:16px 18px;
    font:700 20px Manrope;color:#6b655c}
#tl .row{display:flex;justify-content:space-between}
#trk{position:absolute;left:18px;right:18px;bottom:18px;height:70px;border-radius:10px;background:#E8E3DA;overflow:hidden}
#fill{height:100%;width:0;background:repeating-linear-gradient(90deg,#5B6CFF 0 6px,#7c89ff 6px 9px)}
#ph{position:absolute;top:0;bottom:0;width:4px;background:#1d1a16}
#side{position:absolute;left:60px;top:760px;width:390px;border-radius:24px;background:#fff;padding:24px 26px;
      box-shadow:0 30px 70px rgba(70,50,20,.22);font:600 25px Manrope;color:#2b2722}
#side .h{display:flex;align-items:center;gap:10px;font:700 21px Manrope;color:#6b655c;margin-bottom:12px}
#side .h b{padding:3px 12px;border-radius:9px;background:#5B6CFF;color:#fff;font:700 18px Manrope}
.st{display:flex;align-items:center;gap:14px;height:52px;opacity:.35}
.st i{width:30px;height:30px;border-radius:50%;border:2.5px solid #bdb6aa;flex:none;display:flex;align-items:center;
      justify-content:center;color:#fff;font:800 18px Manrope;font-style:normal}
.st.on{opacity:1}.st.on i{background:#2BB673;border-color:#2BB673}
#cnt{position:absolute;left:40px;top:330px;font:700 112px/1 'Playfair Display';color:#1d1a16;letter-spacing:-.03em}
#cnt small{font-size:32px;color:#8a8378;letter-spacing:0}
"""

JS = """
window.seek=t=>{
  const p=Math.min(1,Math.max(0,(t-CFG.c0)/(CFG.c1-CFG.c0))); const n=Math.round(p*100);
  const c=document.getElementById('cnt'); c.innerHTML=n+'<small>/100</small>'; c.style.opacity=t<CFG.c0?0:1;
  document.getElementById('fill').style.width=(p*100)+'%';
  document.getElementById('fill').style.background=n>=100?'#2BB673':'';
  document.getElementById('ph').style.left=(18+p*(564-4))+'px';
  document.getElementById('fr').textContent=String(Math.round(p*150)).padStart(3,'0')+' / 150';
  CFG.steps.forEach((s,j)=>{document.getElementById('s'+j).className='st'+(t>=s[1]?' on':'');});
};
"""

DEMO = dict(t0=53.30, t1=58.85, hold=0.7, pull=1.1, file="reel-11.mp4",
            steps=[("Расшифровал клип", 54.3), ("Выбрал дубль", 55.0), ("Нарезал 3 плана", 55.9),
                   ("Добавил субтитры", 56.9), ("Отрендерил 150 кадров", 58.3)],
            counter=(54.2, 58.3))


def frames(clip, html, t0, hold, pull, file, steps, counter):
    S = 2  # UI rendered at 2x so it stays sharp while the camera is pushed in
    base = html.still(f'<div id=win><div class=tb><i></i><i></i><i></i><span class=nm>▶ {file}</span>'
                      f'<span class=as>Ассистент</span></div><div id=slot></div></div>', BASE_CSS, scale=S)
    top_body = ('<div id=cnt></div><div id=tl><div class=row><span>● рендер</span><span id=fr></span></div>'
                '<div id=trk><div id=fill></div><div id=ph></div></div></div>'
                '<div id=side><div class=h>● Работаю над <b>монтажом</b></div>' +
                "".join(f'<div class=st id=s{j}><i>✓</i>{s}</div>' for j, (s, _) in enumerate(steps)) + '</div>')
    cfg = json.dumps(dict(c0=counter[0], c1=counter[1], steps=steps), ensure_ascii=False)
    times = [t0 + i / FPS for i in range(len(clip))]
    tops = html.frames(top_body, TOP_CSS, f"const CFG={cfg};" + JS, times, scale=S)
    sx, sy, sw, sh = SLOT
    z0 = W / sw                                         # camera zoom where the slot fills the screen
    c_slot = np.array([sx + sw / 2, sy + sh / 2])
    c_full = np.array([W / 2, H / 2])
    for i, top in enumerate(tops):
        t = times[i]
        k = ease_in_out(prog(t, t0 + hold, t0 + hold + pull))
        z = z0 ** (1 - k)                               # geometric interpolation feels like a real dolly
        c = c_slot * (1 - k) + c_full * k
        # canvas -> screen: p' = (p - c) * z + screen centre
        A = np.float32([[z, 0, W / 2 - z * c[0]], [0, z, H / 2 - z * c[1]]])
        A2 = A.copy(); A2[:, :2] /= S                   # for the 2x UI layers
        out = cv2.warpAffine(base[..., :3], A2, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
        f = clip.frame(i)
        vid = cv2.resize(f, (sw * 2, sh * 2), interpolation=cv2.INTER_AREA)
        vlayer = np.dstack([vid, rounded_mask(sw * 2, sh * 2, max(1, int(36 * min(1, k * 3))))])
        Av = A.copy(); Av[:, :2] /= 2; Av[0, 2] += z * sx; Av[1, 2] += z * sy
        over(out, cv2.warpAffine(vlayer, Av, (W, H), flags=cv2.INTER_LINEAR))
        over(out, cv2.warpAffine(top, A2, (W, H), flags=cv2.INTER_AREA), opacity=min(1, k * 1.6))
        yield out
