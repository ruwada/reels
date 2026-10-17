"""Subtitle style "pop" (from the client reel that passed 100K views, 2026-10-10):
2-3 words per screen, the longest word big in yellow Unbounded, the rest small and white above / below it,
all lowercase, no box, a soft shadow; every screen pops in from 118 % in 0.15 s.

Used by render.py when edit.json has "subs": {"style": "pop", ...}. Options (all optional):
  "hl": "#FFD43B"  key-word colour     "text": "#FFFFFF"  small words
  "top": 1230      top of the block    "big": 112          max key-word size, px
Hook / CTA plates with "style": "pop" use the same look: small line, big word, coloured tag.
"""
import html, re

PUNCT = ".,:;?!…—«»\"'"


def chunks(words, gap=0.45):
    out, cur = [], []
    for w in words:
        if cur and w["s"] - cur[-1]["e"] > gap:
            out.append(cur); cur = []
        cur.append(w)
        t = w["w"]
        if len(cur) == 3 or t[-1] in ".,:;?!»—" or (len(cur) == 2 and len(t.strip(PUNCT)) > 8):
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def clean(t):
    return t.lower().strip(PUNCT).replace("«", "").replace("»", "")


def plan(words, total):
    """[(shown words, key index, start, end)] in source seconds."""
    cs = [[w for w in c if clean(w["w"])] for c in chunks(words)]
    cs = [c for c in cs if c]
    res = []
    for i, c in enumerate(cs):
        key = max(range(len(c)), key=lambda k: len(clean(c[k]["w"])))
        a = c[0]["s"]
        nxt = cs[i + 1][0]["s"] if i + 1 < len(cs) else total
        b = min(c[-1]["e"] + 0.35, nxt)
        res.append(([clean(w["w"]) for w in c], key, a, max(b, a + 0.3)))
    return res


def css(o):
    hl, tx = o.get("hl", "#FFD43B"), o.get("text", "#FFFFFF")
    return f"""
.pop{{position:absolute;left:40px;right:40px;top:{o.get('top', 1230)}px;text-align:center}}
.pop .big{{font:800 112px/1.0 Unbounded;color:{hl};letter-spacing:-4px;
  text-shadow:0 6px 22px rgba(0,0,0,.55),0 0 2px rgba(0,0,0,.6)}}
.pop .sm{{font:600 50px/1.2 Unbounded;color:{tx};letter-spacing:-1px;text-shadow:0 4px 16px rgba(0,0,0,.75);margin:6px 0}}
.pop .tag{{display:inline-block;margin-top:26px;background:{hl};color:#14201C;font:800 38px/1.15 Unbounded;
  padding:18px 30px;border-radius:18px;letter-spacing:-1px;box-shadow:0 10px 30px rgba(0,0,0,.35)}}
"""


def chunk_html(ws, key, o):
    e = html.escape
    k = ws[key]
    fs = min(o.get("big", 112), int(1000 / (max(len(k), 1) * 0.74)))
    top = f'<div class="sm">{e(" ".join(ws[:key]))}</div>' if key else ""
    bot = f'<div class="sm">{e(" ".join(ws[key + 1:]))}</div>' if key + 1 < len(ws) else ""
    return f'<div class="pop">{top}<div class="big" style="font-size:{fs}px">{e(k)}</div>{bot}</div>'


def plate_html(p, o):
    """{"small": "...", "big": "...", "tag": "...", "top": 860}"""
    e = html.escape
    fs = min(120, int(1000 / (max(len(p["big"]), 1) * 0.74)))
    sm = f'<div class="sm" style="font-size:46px">{e(p["small"])}</div>' if p.get("small") else ""
    tag = f'<div class="tag">{e(p["tag"])}</div>' if p.get("tag") else ""
    return (f'<div class="pop" style="top:{p.get("top", 860)}px">{sm}'
            f'<div class="big" style="font-size:{fs}px">{e(p["big"])}</div>{tag}</div>')


def render_png(page, body, o, path):
    page.set_content(f"<html><head><meta charset='utf-8'><style>*{{margin:0;box-sizing:border-box}}"
                     f"html,body{{width:1080px;height:1920px;background:transparent;overflow:hidden}}{css(o)}</style>"
                     f"</head><body>{body}</body></html>")
    page.evaluate("document.fonts.ready")
    page.screenshot(path=path, omit_background=True)
