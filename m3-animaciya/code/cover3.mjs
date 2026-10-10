import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
for (const v of ['A', 'B', 'C']) {
  const pg = await (await b.newContext({ viewport: { width: 1080, height: 1920 } })).newPage();
  await pg.goto('file://' + process.cwd() + '/cover3.html#' + v);
  await pg.evaluate(async () => { for (const f of ['900 60px Unbounded', '800 60px Manrope']) await document.fonts.load(f, 'ЁёAfter Ключ Claude →'); await document.fonts.ready; });
  await pg.waitForTimeout(400);
  await pg.screenshot({ path: `../oblozhka-${v}.png` });
}
await b.close();
