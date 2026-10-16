import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const [,, file, out, w, h] = process.argv;
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const pg = await b.newPage({ viewport: { width: +w, height: +h } });
await pg.goto('file://' + file); await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(300);
await pg.screenshot({ path: out }); await b.close();
