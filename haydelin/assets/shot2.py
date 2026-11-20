# Redrawn app screens at the iPhone screen ratio (1080x2337) so they sit in the phone frame like the recording.
import sys
from playwright.sync_api import sync_playwright
G = sys.argv[1]  # path to gfx.html
J = [("lock_child", [("lockbg", ["20:30", "пятница, 2 октября"]), ("notif", ["Пора чистить зубки", "сейчас", "Спокойной ночи скоро! Почистим зубки со зверьком."])]),
     ("lock_child_bg", [("lockbg", ["20:30", "пятница, 2 октября"])]),
     ("lock_parent_bg", [("lockbg", ["21:31", "пятница, 2 октября"])]),
     ("n_child", [("notif", ["Пора чистить зубки", "сейчас", "Спокойной ночи скоро! Почистим зубки со зверьком."])]),
     ("n_parent", [("notif", ["Вечерняя чистка пропущена", "сейчас", "Ребёнок не почистил зубы. Будильник был в 20:30."])]),
     ("tyagi_off", [("tyagi", [False])]), ("tyagi_on", [("tyagi", [True])])]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1080, "height": 2337})
    pg.goto("file://" + G)
    pg.add_style_tag(content="body{height:2337px!important}.lock,.scr{inset:0}")
    for name, parts in J:
        pg.evaluate("""(parts)=>{document.getElementById('root').innerHTML=parts.map(([k,a])=>{show(k,...a);return document.getElementById('root').innerHTML}).join('')}""", parts)
        pg.wait_for_timeout(150)
        pg.screenshot(path=f"{name}.png", omit_background=name.startswith("n_"))
    b.close()
