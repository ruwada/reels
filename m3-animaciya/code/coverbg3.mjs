// cover background: real MacBook (no zoom) with the Claude scene on its screen
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await (await b.newContext({ viewport: { width: 1080, height: 1920 } })).newPage();
await pg.goto('file://' + process.cwd() + '/index.html');
await pg.evaluate(async () => { const v = document.querySelector('#bg'); const i = document.createElement('img'); i.src = 'assets/intro-frame.png'; i.id = 'bg'; i.style.cssText = 'position:absolute;left:0;top:0;width:1080px;height:1920px'; v.replaceWith(i); await document.fonts.ready; });
await pg.waitForTimeout(600);
await pg.evaluate(t => { const tl = window.__timelines.main; tl.seek(0); tl.seek(t, false); zi.u = 0; applyZoom(0);
  for (const s of ['#subs', '#ens', '#label', '#grain']) document.querySelector(s).style.display = 'none'; }, Number(process.argv[2] || 2.6));
await pg.screenshot({ path: 'assets/cover-bg3.png' });
await b.close();
