"""16 cover story: the shot turns into a magazine cover. A big serif masthead rises letter by letter BEHIND
the speaker's head, cover lines and an issue line appear around him. Reference: @tenfoldmarc 16/17."""
import json
from fxlib import person_mattes, over, person_over, prog, FPS, W, H

NAME_EN, NAME_RU = "cover story", "обложка журнала"

CSS = """
body{width:1080px;height:1920px;color:#FFF8EE}
#mast{position:absolute;left:0;right:0;top:250px;text-align:center;font:900 200px/1 'Playfair Display';letter-spacing:0;text-shadow:0 4px 24px rgba(0,0,0,.45);
      white-space:nowrap}
#mast span{display:inline-block;clip-path:inset(-20% -10% 0 -10%)}
#mast span i{display:inline-block;font-style:normal}
#kick{position:absolute;left:0;right:0;top:215px;text-align:center;font:700 26px Manrope;letter-spacing:.5em}
.cl{position:absolute;font:700 40px/1.1 'Playfair Display';width:300px;text-shadow:0 2px 12px rgba(0,0,0,.4)}
.cl small{display:block;font:700 20px Manrope;letter-spacing:.2em;color:#FFD84D;margin-bottom:6px}
#iss{position:absolute;left:70px;top:470px;font:600 22px Manrope;letter-spacing:.2em;opacity:.9}
#bar{position:absolute;right:150px;top:1440px;width:150px;height:96px;background:#fff;padding:8px;
     background-image:repeating-linear-gradient(90deg,#111 0 3px,transparent 3px 5px,#111 5px 6px,transparent 6px 10px);
     background-clip:content-box;border:8px solid #fff}
"""

JS = """
const E=t=>1-Math.pow(1-Math.min(1,Math.max(0,t)),3);
window.seek=t=>{
  document.querySelectorAll('#mast i').forEach((el,j)=>{const p=E((t-CFG.mast-j*0.07)/0.45);
    el.style.transform=`translateY(${(1-p)*110}%)`;});
  const k=E((t-CFG.kick)/0.4); ['kick','iss'].forEach(id=>{const e=document.getElementById(id); if(e) e.style.opacity=k;});
  document.querySelectorAll('.cl').forEach((el,j)=>{const p=E((t-CFG.lines[j][2])/0.4);
    el.style.opacity=p; el.style.transform=`translateX(${(1-p)*(j%2?40:-40)}px)`;});
  const b=document.getElementById('bar'); if(b) b.style.opacity=E((t-CFG.bar)/0.3);
};
"""

DEMO = dict(t0=14.15, t1=15.95, mast_text="ШКОЛА", mast=14.25, kick=14.70, kicker="ОНЛАЙН · ВЫПУСК № 11",
            issue="ОКТЯБРЬ 2026",
            lines=[("Кейс", "Агент отвечает ученикам за 0,8 сек", 14.9, 60, 1250),
                   ("Разбор", "Рост без нового найма", 15.1, 640, 1080)],
            bar=15.3)


def frames(clip, html, t0, mast_text, mast, kick, kicker, issue, lines, bar, ink=None):
    """ink: colour of the masthead, kicker and issue line (default cream; use a dark one on a light wall)."""
    m_html = "".join(f"<span><i>{c}</i></span>" for c in mast_text)
    cl = "".join(f'<div class=cl style="left:{x}px;top:{y}px"><small>{a}</small>{b}</div>' for a, b, _, x, y in lines)
    back_body = f'<div id=kick>{kicker}</div><div id=mast>{m_html}</div><div id=iss>{issue}</div>'
    front_body = f'{cl}<div id=bar></div>'
    cfg = json.dumps(dict(mast=mast, kick=kick, lines=lines, bar=bar), ensure_ascii=False)
    times = [t0 + i / FPS for i in range(len(clip))]
    mattes = person_mattes(clip)
    js = f"const CFG={cfg};" + JS
    back_css = CSS + (f"#mast,#kick,#iss{{color:{ink};text-shadow:none}}" if ink else "")
    for i, (ui, fr) in enumerate(zip(html.frames(back_body, back_css, js, times), html.frames(front_body, CSS, js, times))):
        f = clip.frame(i)
        graded = (f - 0.5) * 1.12 + 0.5                  # a touch of "print" contrast
        back = graded.copy()
        over(back, ui)                                   # masthead and lines live behind him
        out = person_over(back, graded, mattes[i])
        over(out, fr)                                    # cover lines and barcode sit on top
        yield out
