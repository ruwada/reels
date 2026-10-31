// Text layers for build.py: one transparent PNG per ayah (+ mask for "glass"), a constant shade (under.png)
// and the watermark (base.png). The Arabic, the ayah-end number and Kuliev's translation are inserted exactly
// as they come in ayat.json: no string here is typed by hand except the surah name label.
import fs from 'fs';
import { createRequire } from 'module';
const { chromium } = createRequire(import.meta.url)('playwright');

const L = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const FONTS = 'https://fonts.googleapis.com/css2?family=Amiri+Quran&family=Scheherazade+New:wght@400;700' +
  '&family=Cormorant+Garamond:ital,wght@1,600;1,700&family=Manrope:wght@600;700;800&display=block';
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');

const STYLES = {
  // Frosted panel in the middle (test 1 look).
  glass: (a) => `
    .box{position:absolute;left:64px;right:64px;top:900px;transform:translateY(-50%);padding:50px 50px 52px;border-radius:44px;
      text-align:center;color:#fff;background:rgba(12,22,28,.32)}
    .mask .box{background:#fff}.mask .box *{visibility:hidden}
    .ar{font-family:'Amiri Quran';font-size:60px;line-height:1.95;direction:rtl;text-shadow:0 2px 10px rgba(0,0,0,.35)}
    .sep{width:90px;height:3px;margin:18px auto 22px;background:#f2d38a;border-radius:3px}
    .ru{font:700 40px/1.32 Manrope;text-shadow:0 2px 8px rgba(0,0,0,.35)}
    .ref{margin-top:22px;font:600 26px Manrope;opacity:.85;letter-spacing:.08em}`,
  // No panel: simplified script, elegant serif translation, soft shadow only.
  clean: (a) => `
    .box{position:absolute;left:70px;right:70px;top:880px;transform:translateY(-50%);text-align:center;color:#fff}
    .ar{font-family:'Scheherazade New';font-weight:700;font-size:84px;line-height:1.7;direction:rtl;
      text-shadow:0 0 2px rgba(0,0,0,.55),0 3px 18px rgba(0,0,0,.55),0 0 50px rgba(0,0,0,.35)}
    .sep{display:none}
    .ru{margin-top:26px;font:italic 700 50px/1.25 'Cormorant Garamond';
      text-shadow:0 0 2px rgba(0,0,0,.6),0 2px 14px rgba(0,0,0,.6),0 0 40px rgba(0,0,0,.35)}
    .ref{margin-top:26px;font:700 24px Manrope;letter-spacing:.14em;opacity:.95;text-shadow:0 1px 8px rgba(0,0,0,.6)}`,
  // Lower third over a soft shade; ayah number in a gold ring.
  bottom: (a) => `
    .box{position:absolute;left:70px;right:70px;bottom:520px;text-align:center;color:#fff}
    .num{display:inline-flex;align-items:center;justify-content:center;width:64px;height:64px;border:3px solid #f2d38a;
      border-radius:50%;font:700 30px 'Amiri Quran';color:#f2d38a;margin-bottom:14px;text-shadow:0 1px 6px rgba(0,0,0,.4)}
    .ar{font-family:'Amiri Quran';font-size:68px;line-height:1.9;direction:rtl;text-shadow:0 2px 12px rgba(0,0,0,.45)}
    .sep{display:none}
    .ru{margin-top:14px;font:600 40px/1.3 Manrope;color:#fff;text-shadow:0 2px 10px rgba(0,0,0,.5)}
    .ref{margin-top:18px;font:700 24px Manrope;letter-spacing:.14em;color:#f2d38a;text-shadow:0 1px 6px rgba(0,0,0,.5)}`,
};

const body = (a, i, mode) => {
  const label = `${L.surah_name} · ${a.key}`;
  if (L.style === 'bottom')
    return `<div class="box"><div class="num">${esc(a.end)}</div><div class="ar">${esc(a.uthmani)}</div>
      <div class="ru">${esc(a.ru)}</div><div class="ref">${esc(label)}</div></div>`;
  const ar = L.style === 'clean' ? a.imlaei : `${a.uthmani} ﴿${a.end}﴾`;
  return `<div class="box"><div class="ar">${esc(ar)}</div><div class="sep"></div><div class="ru">${esc(a.ru)}</div>
    <div class="ref">${esc(label)}</div></div>`;
};

const page = (css, inner, cls = '') => `<html><head><link href="${FONTS}" rel="stylesheet"><style>
  body{margin:0;width:1080px;height:1920px;background:transparent;position:relative;overflow:hidden}${css}</style></head>
  <body class="${cls}">${inner}</body></html>`;

const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
const shot = async (html, path) => {
  await p.setContent(html); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(250);
  await p.screenshot({ path, omitBackground: true });
};
const css = STYLES[L.style]();
for (const [i, a] of L.ayat.entries()) {
  await shot(page(css, body(a, i)), `${L.out}/text-${i + 1}.png`);
  if (L.style === 'glass') await shot(page(css, body(a, i), 'mask'), `${L.out}/mask-${i + 1}.png`);
  const h = await p.$eval('.box', e => e.getBoundingClientRect().top);
  if (h < 160) console.error(`ayah ${a.key}: text block reaches y=${Math.round(h)}, too tall`);
}
if (L.style === 'bottom')
  await shot(page('', '<div style="position:absolute;left:0;right:0;top:820px;bottom:0;background:linear-gradient(to bottom,rgba(0,0,0,0),rgba(0,0,0,.42) 40%,rgba(0,0,0,.5))"></div>'), `${L.out}/under.png`);
else if (fs.existsSync(`${L.out}/under.png`)) fs.unlinkSync(`${L.out}/under.png`);
await shot(page('', `<div style="position:absolute;bottom:${L.style === 'bottom' ? 330 : 250}px;width:100%;text-align:center;color:#fff;
  font:800 32px Manrope;opacity:.85;text-shadow:0 2px 8px rgba(0,0,0,.5)">@islam.devai</div>`), `${L.out}/base.png`);
await b.close();
