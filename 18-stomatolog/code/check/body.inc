<style>
.ttl{font:800 60px/1.1 "Unbounded";letter-spacing:-.025em;margin:20px 0 36px}
.ttl em{font-style:normal;background:#FFD43B;padding:0 10px;border-radius:12px}
.row{display:flex;align-items:center;gap:30px;padding:28px 0;border-top:3px solid #ECE9DF;opacity:0}
.row:first-of-type{border-top:0}
.no{flex:0 0 74px;height:74px;border-radius:22px;background:#EFEDE6;font:800 34px/74px "Unbounded";text-align:center;color:#8A8678;position:relative;overflow:hidden}
.no s{position:absolute;inset:0;background:#14201C;display:block;transform:scale(0);border-radius:22px}
.no svg{position:absolute;inset:15px;width:44px;height:44px}
.row span{font:800 46px/1.15 "Manrope";color:#14201C}
.row small{display:block;font:700 28px "Manrope";color:#7C786B;margin-top:4px}
.timer{position:absolute;right:56px;top:128px;font:800 28px "Manrope";color:#1D6B5A;background:#DDF0EA;padding:10px 20px;border-radius:18px}
</style>
<div id="root" data-composition-id="main" data-start="0" data-duration="4.9" data-width="1080" data-height="1920">
 <div class="bg"></div><div class="dots" id="dots"></div>
 <div class="page" id="page">
  <div class="bar"><i></i><i></i><i></i><div class="url">сайт врача / главная</div></div>
  <div class="in">
   <div class="kick">Первый экран</div>
   <div class="ttl" id="ttl">Отвечает <em>за 5 секунд</em></div>
   <div class="row" id="r1"><div class="no">1<s></s><svg viewBox="0 0 24 24"><path d="M4 12.5l5 5L20 6.5" fill="none" stroke="#FFD43B" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/></svg></div><span>Кто этот врач<small>опыт, специализация</small></span></div>
   <div class="row" id="r2"><div class="no">2<s></s><svg viewBox="0 0 24 24"><path d="M4 12.5l5 5L20 6.5" fill="none" stroke="#FFD43B" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/></svg></div><span>Почему ему доверять<small>кейсы, отзывы, лицензии</small></span></div>
   <div class="row" id="r3"><div class="no">3<s></s><svg viewBox="0 0 24 24"><path d="M4 12.5l5 5L20 6.5" fill="none" stroke="#FFD43B" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/></svg></div><span>Какие есть продукты<small>курсы, стажировки, менторство</small></span></div>
   <div class="row" id="r4"><div class="no">4<s></s><svg viewBox="0 0 24 24"><path d="M4 12.5l5 5L20 6.5" fill="none" stroke="#FFD43B" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/></svg></div><span>Что делать дальше<small>одна понятная кнопка</small></span></div>
  </div>
 </div>
</div>
<script>
const OUT="expo.out",SOFT="power3.out",IN="power2.in";
const tl=gsap.timeline({paused:true});
tl.fromTo("#dots",{y:0},{y:-90,duration:4.9,ease:"none"},0);
tl.fromTo("#page",{opacity:0,x:200},{opacity:1,x:0,duration:.45,ease:OUT},0);
tl.fromTo("#ttl em",{opacity:0,scale:.8},{opacity:1,scale:1,duration:.35,ease:"back.out(2)"},.3);
[.25,1.3,2.65,3.95].forEach((t,i)=>{const id="#r"+(i+1);
  tl.fromTo(id,{opacity:0,y:30},{opacity:1,y:0,duration:.35,ease:SOFT},t);
  tl.fromTo(id+" s",{scale:0},{scale:1,duration:.28,ease:"back.out(2)"},t+.3);
  tl.fromTo(id+" path",{strokeDasharray:1,strokeDashoffset:1},{strokeDashoffset:0,duration:.3,ease:"power2.out"},t+.42);
});
tl.to("#page",{opacity:0,scale:.97,duration:.25,ease:IN},4.65);
window.__timelines["main"]=tl; tl.seek(0);
</script></body></html>
