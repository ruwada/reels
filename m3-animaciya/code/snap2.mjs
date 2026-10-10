import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const times = process.argv.slice(3).map(Number), out = process.argv[2];
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await (await b.newContext({ viewport: { width: 1080, height: 1920 } })).newPage();
pg.on('pageerror', e => console.log('ERR', e.message));
await pg.goto('file://' + process.cwd() + '/index.html');
await pg.evaluate(async () => { const v = document.querySelector('#bg'); const i = document.createElement('img'); i.src = 'assets/mac-frame.png'; i.id = 'bg'; i.style.cssText = 'position:absolute;left:0;top:0;width:1080px;height:1920px'; v.replaceWith(i); await document.fonts.ready; });
await pg.waitForTimeout(700);
for (const t of times) { await pg.evaluate(t => { const tl = window.__timelines.main; tl.seek(0); tl.seek(t, false); }, t); await pg.screenshot({ path: `${out}/t${String(t.toFixed(1)).padStart(5,'0')}.png` }); }
await b.close();
