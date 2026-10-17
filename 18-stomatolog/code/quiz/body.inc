<style>
.prog{margin-top:22px;height:14px;border-radius:7px;background:#E8E5DA;overflow:hidden}
.prog b{display:block;height:100%;width:100%;background:#FFD43B;transform-origin:left center;transform:scaleX(0)}
.stage{position:relative;height:640px;margin-top:40px}
.q{position:absolute;inset:0;opacity:0}
.q h2{font:800 54px/1.12 "Unbounded";letter-spacing:-.02em;color:#14201C;margin-bottom:38px}
.opt{position:relative;display:flex;align-items:center;gap:26px;height:116px;margin-bottom:22px;padding:0 34px;border-radius:28px;border:3px solid #E3DFD2;background:#fff;font:700 42px "Manrope";color:#2A3531}
.opt .r{flex:0 0 46px;height:46px;border-radius:50%;border:4px solid #CFCABA;position:relative}
.opt .r s{position:absolute;inset:7px;border-radius:50%;background:#14201C;display:block;transform:scale(0)}
.opt .hl{position:absolute;inset:-3px;border-radius:28px;background:#FFD43B;opacity:0}
.opt span,.opt .r{position:relative}
.tap{position:absolute;width:120px;height:120px;border-radius:50%;background:rgba(20,32,28,.22);opacity:0;pointer-events:none}
.res{position:absolute;inset:0;opacity:0}
.res .lab{font:700 34px "Manrope";color:#6E6A5D}
.res .big{font:800 76px/1.05 "Unbounded";letter-spacing:-.03em;margin:18px 0 26px}
.res .big em{font-style:normal;background:#FFD43B;padding:0 12px;border-radius:14px;box-decoration-break:clone;-webkit-box-decoration-break:clone}
.res .meta{display:flex;gap:16px;flex-wrap:wrap}
.res .meta div{font:700 30px "Manrope";padding:14px 24px;border-radius:20px;background:#EFEDE6;color:#2A3531}
.btn{margin-top:44px;height:124px;border-radius:30px;background:#14201C;color:#FFD43B;font:800 44px/124px "Unbounded";text-align:center}
.match{position:absolute;right:0;top:-6px;font:800 30px "Manrope";color:#1D6B5A;background:#DDF0EA;padding:10px 20px;border-radius:18px}
</style>
<div id="root" data-composition-id="main" data-start="0" data-duration="7.9" data-width="1080" data-height="1920">
 <div class="bg"></div><div class="dots" id="dots"></div>
 <div class="page" id="page">
  <div class="bar"><i></i><i></i><i></i><div class="url">сайт врача / обучение</div></div>
  <div class="in">
   <div class="kick" id="kick">Подбор обучения · вопрос <span id="n1">1</span><span id="n2" style="display:none">2</span><span id="n3" style="display:none">3</span> из 3</div>
   <div class="prog"><b id="prog"></b></div>
   <div class="stage">
    <div class="q" id="q1"><h2>Какой у вас уровень?</h2>
     <div class="opt"><div class="hl"></div><div class="r"><s></s></div><span>Студент</span></div>
     <div class="opt" id="q1s"><div class="hl"></div><div class="r"><s></s></div><span>Молодой врач</span></div>
     <div class="opt"><div class="hl"></div><div class="r"><s></s></div><span>Опытный практик</span></div></div>
    <div class="q" id="q2"><h2>Что хотите получить?</h2>
     <div class="opt"><div class="hl"></div><div class="r"><s></s></div><span>Теорию в записи</span></div>
     <div class="opt" id="q2s"><div class="hl"></div><div class="r"><s></s></div><span>Практику на пациентах</span></div>
     <div class="opt"><div class="hl"></div><div class="r"><s></s></div><span>Личного наставника</span></div></div>
    <div class="q" id="q3"><h2>Какое направление интересно?</h2>
     <div class="opt" id="q3s"><div class="hl"></div><div class="r"><s></s></div><span>Терапия</span></div>
     <div class="opt"><div class="hl"></div><div class="r"><s></s></div><span>Хирургия</span></div>
     <div class="opt"><div class="hl"></div><div class="r"><s></s></div><span>Ортопедия</span></div></div>
    <div class="res" id="res"><div class="match" id="match">совпадение 96%</div>
     <div class="lab">Вам подходит</div>
     <div class="big" id="rb"><em>Стажировка</em> по&nbsp;терапии</div>
     <div class="meta"><div>практика в клинике</div><div>для молодых врачей</div></div>
     <div class="btn" id="btn">Записаться</div></div>
   </div>
  </div>
 </div>
</div>
<script>
const OUT="expo.out",SOFT="power3.out",IN="power2.in";
const tl=gsap.timeline({paused:true});
tl.fromTo("#dots",{y:0},{y:-120,duration:7.9,ease:"none"},0);
tl.fromTo("#page",{opacity:0,y:140,scale:.94},{opacity:1,y:0,scale:1,duration:.55,ease:OUT},0);
const Q=[["#q1",0.25,1.35],["#q2",1.95,3.0],["#q3",3.3,4.75]];
Q.forEach(([id,a,pick],i)=>{
  const s=id+"s";
  tl.fromTo(id,{opacity:0,x:120},{opacity:1,x:0,duration:.4,ease:OUT},a);
  tl.fromTo(id+" .opt",{opacity:0,y:24},{opacity:1,y:0,duration:.3,ease:SOFT,stagger:.07},a+.1);
  tl.to("#prog",{scaleX:(i+1)/3,duration:.45,ease:SOFT},pick);
  tl.to(s,{scale:.97,duration:.08,ease:IN},pick-.08);
  tl.to(s,{scale:1,duration:.25,ease:"back.out(2)"},pick);
  tl.to(s+" .hl",{opacity:1,duration:.15},pick);
  tl.to(s,{borderColor:"#FFD43B",duration:.15},pick);
  tl.to(s+" s",{scale:1,duration:.25,ease:"back.out(2.5)"},pick);
  const nxt=i<2?Q[i+1][1]:5.35;
  tl.to(id,{opacity:0,x:-120,duration:.28,ease:IN},nxt-.25);
  if(i<2){tl.set("#n"+(i+1),{display:"none"},nxt);tl.set("#n"+(i+2),{display:"inline"},nxt);}
});
tl.to("#kick",{opacity:0,duration:.2},5.2);
tl.fromTo("#res",{opacity:0,y:60},{opacity:1,y:0,duration:.5,ease:OUT},5.4);
tl.fromTo("#rb em",{backgroundSize:"0% 100%"},{backgroundSize:"100% 100%",duration:.4},5.6);
tl.fromTo("#match",{opacity:0,scale:.6},{opacity:1,scale:1,duration:.4,ease:"back.out(2)"},5.9);
tl.fromTo("#btn",{opacity:0,y:30},{opacity:1,y:0,duration:.4,ease:SOFT},6.1);
tl.to("#btn",{scale:1.04,duration:.35,ease:"sine.inOut",yoyo:true,repeat:3},6.6);
tl.to("#page",{opacity:0,y:-60,duration:.25,ease:IN},7.62);
window.__timelines["main"]=tl; tl.seek(0);
</script></body></html>
