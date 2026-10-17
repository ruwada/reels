"""10 chart grow: a line chart is drawn ON THE WALL behind the speaker (weekday axis, guide lines), the
glowing line climbs point by point and a tag pops at the peak; he steps back a little so it shows, his head covers a part.
Reference: @tenfoldmarc 10/17."""
import json
from fxlib import person_mattes, over, transform, with_alpha, clean_plate, prog, ease_out, lerp, FPS, W, H

NAME_EN, NAME_RU = "chart grow", "растущий график"

CSS = """
body{width:1080px;height:1920px}
svg{position:absolute;left:0;top:0}
.ax{font:700 30px Manrope;fill:rgba(255,255,255,.85);text-anchor:middle;letter-spacing:.05em}
#tag{position:absolute;padding:12px 22px;border-radius:14px;background:#E9FF57;color:#121212;font:800 30px Unbounded;
     box-shadow:0 0 40px rgba(233,255,87,.55);transform-origin:50% 100%}
"""

JS = """
const E=t=>1-Math.pow(1-Math.min(1,Math.max(0,t)),3);
window.seek=t=>{
  const g=E((t-CFG.grid)/0.5); document.getElementById('grid').style.opacity=g*0.9;
  const P=CFG.pts, n=P.length; let d='', last=null;
  for(let j=0;j<n;j++){ const tj=CFG.t[j]; if(t<tj) break;
    const [x,y]=P[j]; let px=x, py=y;
    if(j>0){ const k=E((t-tj)/0.35); const [x0,y0]=P[j-1]; px=x0+(x-x0)*k; py=y0+(y-y0)*k; }
    d += (j?'L':'M')+px+' '+py; last=[px,py]; }
  ['ln','glow'].forEach(id=>document.getElementById(id).setAttribute('d',d));
  const dot=document.getElementById('dot'); dot.style.opacity=last?1:0; if(last){dot.setAttribute('cx',last[0]);dot.setAttribute('cy',last[1]);}
  for(let j=0;j<n;j++){const v=document.getElementById('v'+j); v.style.opacity=t>=CFG.t[j]+0.3?1:0;}
  const tg=document.getElementById('tag'), k=E((t-CFG.tag)/0.3);
  tg.style.opacity=k; tg.style.left=(P[n-1][0]-150)+'px'; tg.style.top=(P[n-1][1]-120)+'px';
  tg.style.transform=`scale(${0.5+0.5*k})`;
};
"""

DEMO = dict(t0=68.85, t1=71.45, grid=68.90, labels=["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"],
            values=[0.10, 0.14, 0.12, 0.30, 0.45, 0.72, 1.0],
            times=[69.0, 69.3, 69.55, 69.95, 70.4, 70.8, 71.05], tag=71.15, tag_text="×3 ↗",
            box=(130, 280, 930, 640), person_scale=0.80)


def frames(clip, html, t0, grid, labels, values, times, tag, tag_text, box, person_scale=0.80):
    x0, y0, x1, y1 = box
    n = len(values)
    xs = [x0 + (x1 - x0) * j / (n - 1) for j in range(n)]
    pts = [[round(x), round(y1 - (y1 - y0 - 90) * v)] for x, v in zip(xs, values)]
    grid_svg = "".join(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1}" stroke="rgba(255,255,255,.55)" stroke-width="3" '
                       f'stroke-dasharray="6 10"/><text class=ax x="{x}" y="{y1 + 56}">{l}</text>' for x, l in zip(xs, labels))
    grid_svg += f'<line x1="{x0 - 40}" y1="{y1}" x2="{x1 + 40}" y2="{y1}" stroke="rgba(255,255,255,.4)" stroke-width="2"/>'
    vdots = "".join(f'<circle id=v{j} cx="{x}" cy="{y}" r="9" fill="#E9FF57" opacity="0"/>' for j, (x, y) in enumerate(pts))
    body = (f'<svg width=1080 height=1920><defs><filter id=b><feGaussianBlur stdDeviation="10"/></filter></defs>'
            f'<g id=grid>{grid_svg}</g>'
            f'<path id=glow fill="none" stroke="#E9FF57" stroke-width="18" opacity=".55" filter="url(#b)"/>'
            f'<path id=ln fill="none" stroke="#E9FF57" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"/>'
            f'{vdots}<circle id=dot r="16" fill="#fff" stroke="#E9FF57" stroke-width="6"/></svg><div id=tag>{tag_text}</div>')
    cfg = json.dumps(dict(grid=grid, pts=pts, t=times, tag=tag))
    tl = [t0 + i / FPS for i in range(len(clip))]
    mattes = person_mattes(clip)
    for i, ui in enumerate(html.frames(body, CSS, f"const CFG={cfg};" + JS, tl)):
        f = clip.frame(i)
        k = ease_out(prog(tl[i], grid - 0.1, grid + 0.4))   # he steps back so the whole chart shows
        back = (clean_plate(f, mattes[i]) if k > 0 else f) * lerp(1.0, 0.68, k)
        over(back, ui)
        ps = lerp(1.0, person_scale, k)
        over(back, transform(with_alpha(f, mattes[i]), ps, 0, cx=W / 2, cy=H, tx=W / 2, ty=H))
        yield back
