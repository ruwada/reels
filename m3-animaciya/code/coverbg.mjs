import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await (await b.newContext({ viewport: { width: 1080, height: 1920 } })).newPage();
await pg.goto('file://' + process.cwd() + '/index.html');
await pg.evaluate(async () => { await document.fonts.ready; });
await pg.waitForTimeout(500);
await pg.evaluate(() => { const tl = window.__timelines.main; tl.seek(0); tl.seek(2.3, false); document.querySelector('#subs').style.display='none'; document.querySelector('#ens').style.display='none'; });
await pg.screenshot({ path: 'assets/cover-bg.png' });
await b.close();
