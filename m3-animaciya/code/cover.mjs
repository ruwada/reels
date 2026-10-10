import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await (await b.newContext({ viewport: { width: 1080, height: 1920 } })).newPage();
await pg.goto('file://' + process.cwd() + '/cover.html');
await pg.evaluate(async () => { for (const f of ['800 60px Unbounded', '800 60px Manrope']) await document.fonts.load(f, 'Её Claude 3'); await document.fonts.ready; });
await pg.waitForTimeout(600);
await pg.screenshot({ path: '../oblozhka.png' });
await b.close();
