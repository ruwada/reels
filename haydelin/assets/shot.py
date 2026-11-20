from playwright.sync_api import sync_playwright
J=[("lock_child","lockbg",["20:30","пятница, 2 октября"]),("n_child","notif",["Пора чистить зубки","20:30","Спокойной ночи скоро! Почистим зубки со зверьком."]),
   ("lock_parent","lockbg",["21:31","пятница, 2 октября"]),("n_parent","notif",["Вечерняя чистка пропущена","21:31","Ребёнок не почистил зубы. Будильник был в 20:30."]),
   ("tyagi_off","tyagi",[False]),("tyagi_on","tyagi",[True]),("store","store",[])]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/opt/pw-browsers/chromium"); pg=b.new_page(viewport={"width":1080,"height":1920})
    pg.goto("file:///tmp/claude-0/reels/haydelin/assets/gfx.html")
    for n,k,a in J:
        pg.evaluate("([k,a])=>show(k,...a)",[k,a]); pg.wait_for_timeout(200)
        pg.screenshot(path=f"{n}.png",omit_background=True)
    b.close()
