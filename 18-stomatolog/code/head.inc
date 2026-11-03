<!doctype html>
<html lang="ru"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<script src="assets/gsap.min.js"></script>
<style>
@font-face { font-family: "Unbounded"; src: url("assets/fonts/unbounded-cyr.woff2") format("woff2"); font-weight: 200 900; unicode-range: U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116; }
@font-face { font-family: "Unbounded"; src: url("assets/fonts/unbounded-lat.woff2") format("woff2"); font-weight: 200 900; unicode-range: U+0000-00FF, U+2000-206F, U+2212; }
@font-face { font-family: "Manrope"; src: url("assets/fonts/manrope-cyr.woff2") format("woff2"); font-weight: 200 800; unicode-range: U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116; }
@font-face { font-family: "Manrope"; src: url("assets/fonts/manrope-lat.woff2") format("woff2"); font-weight: 200 800; unicode-range: U+0000-00FF, U+2000-206F, U+2212; }
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0C1714}
#root{width:100%;height:100%;position:relative;overflow:hidden;font-family:"Manrope";color:#14201C}
.bg{position:absolute;inset:-200px;background:radial-gradient(900px 700px at 25% 20%,#1D4A3F 0%,transparent 65%),radial-gradient(800px 800px at 85% 75%,#3A3410 0%,transparent 60%),#0C1714}
.dots{position:absolute;inset:-100px;background-image:radial-gradient(rgba(255,212,59,.10) 2px,transparent 2.5px);background-size:46px 46px}
.page{position:absolute;left:90px;top:230px;width:860px;background:#FBFAF6;border-radius:40px;box-shadow:0 50px 140px rgba(0,0,0,.55);overflow:hidden}
.bar{height:84px;background:#EFEDE6;display:flex;align-items:center;gap:14px;padding:0 34px}
.bar i{width:18px;height:18px;border-radius:50%;background:#D4D0C4;display:block}
.bar .url{margin-left:18px;flex:1;height:44px;border-radius:22px;background:#fff;font:700 24px/44px "Manrope";color:#8A8678;padding-left:24px}
.in{padding:44px 56px 56px}
.kick{font:800 24px "Manrope";letter-spacing:.16em;text-transform:uppercase;color:#1D6B5A}
</style></head><body>
