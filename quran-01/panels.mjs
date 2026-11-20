import fs from 'fs'; import { createRequire } from 'module';
const { chromium } = createRequire(import.meta.url)('playwright');
const ayat = JSON.parse(fs.readFileSync('../src/ayat.json', 'utf8'));
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
const boxes = [];
for (const [i, a] of ayat.entries()) {
  for (const mode of ['text', 'mask']) {
    await p.setContent(`<html><head><link href="https://fonts.googleapis.com/css2?family=Amiri+Quran&family=Manrope:wght@600;700&display=block" rel="stylesheet">
<style>body{margin:0;width:1080px;height:1920px;background:transparent;font-family:Manrope}
.panel{position:absolute;left:64px;right:64px;top:900px;transform:translateY(-50%);padding:52px 50px 54px;border-radius:44px;text-align:center;color:#fff;
background:${mode === 'mask' ? '#fff' : 'rgba(12,22,28,.34)'}}
.mask *{visibility:hidden}
.ar{font-family:'Amiri Quran';font-size:60px;line-height:1.95;direction:rtl;text-shadow:0 2px 10px rgba(0,0,0,.35)}
.sep{width:90px;height:3px;margin:20px auto 24px;background:#f2d38a;border-radius:3px}
.ru{font-size:40px;font-weight:700;line-height:1.32;text-shadow:0 2px 8px rgba(0,0,0,.35)}
.ref{margin-top:24px;font-size:26px;font-weight:600;opacity:.85;letter-spacing:.08em}</style></head>
<body><div class="panel ${mode}"><div class="ar">${a.ar} ﴿${a.end}﴾</div><div class="sep"></div><div class="ru">${a.ru}</div>
<div class="ref">АЛЬ-БАКАРА · ${a.key}</div></div></body></html>`);
    await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(400);
    await p.screenshot({ path: `${mode}-${i + 1}.png`, omitBackground: true });
    if (mode === 'text') boxes.push(await p.$eval('.panel', e => e.getBoundingClientRect().toJSON()));
  }
}
// watermark layer
await p.setContent(`<html><head><link href="https://fonts.googleapis.com/css2?family=Manrope:wght@800&display=block" rel="stylesheet"></head>
<body style="margin:0;width:1080px;height:1920px;background:transparent"><div style="position:absolute;bottom:250px;width:100%;text-align:center;color:#fff;font:800 34px Manrope;opacity:.85;text-shadow:0 2px 8px rgba(0,0,0,.45)">@islam.devai</div></body></html>`);
await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
await p.screenshot({ path: 'wm.png', omitBackground: true });
console.log(JSON.stringify(boxes)); await b.close();
