const {chromium}=require('playwright');(async()=>{
const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+process.cwd()+'/gfx/g.html'); await p.evaluate(()=>document.fonts.ready);
for(const s of ['p95','title','halls','h1','h2','h3','cta']){await p.evaluate(s=>document.body.dataset.s=s,s); await p.waitForTimeout(150); await p.screenshot({path:`gfx/${s}.png`,omitBackground:true});}
await b.close();})();
