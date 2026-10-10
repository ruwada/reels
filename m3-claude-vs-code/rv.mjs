import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await (await b.newContext({ viewport: { width: 1080, height: 1920 } })).newPage();
for (const v of ['A', 'B', 'C']) {
  await pg.goto('file://' + process.cwd() + '/v.html#' + v); await pg.reload();
  await pg.evaluate(async () => { for (const f of ['800 60px U', '800 60px M']) await document.fonts.load(f, 'Ты Claude ≠ 50%'); await document.fonts.ready; });
  await pg.waitForTimeout(400); await pg.screenshot({ path: `../oblozhka-${v}.png` });
}
await b.close();
