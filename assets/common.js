/* ============================================================
   COMMON —— 全站共享行为：滚动显现 / 数字滚动 / EDDIES /
   光标光晕 / 移动端菜单 / 偶发故障闪动
   ============================================================ */
(function(){
  /* 滚动显现 + 属性条动画 */
  const io = new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(!e.isIntersecting) return;
      e.target.classList.add('in');
      e.target.querySelectorAll('.bar i').forEach(b=> b.style.right = (100 - parseFloat(b.dataset.w)) + '%');
      io.unobserve(e.target);
    });
  }, {threshold:.15});
  document.querySelectorAll('.reveal').forEach(el=>io.observe(el));

  /* 数字滚动（仅首页统计区有 data-count，其余页面自动跳过） */
  const cio = new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(!e.isIntersecting) return;
      const el = e.target, target = +el.dataset.count, dur = 1600, t0 = performance.now();
      (function step(t){
        const p = Math.min((t - t0)/dur, 1);
        el.textContent = Math.round(target * (1 - Math.pow(1-p, 3))).toLocaleString();
        if(p < 1) requestAnimationFrame(step);
      })(t0);
      cio.unobserve(el);
    });
  }, {threshold:.5});
  document.querySelectorAll('[data-count]').forEach(el=>cio.observe(el));

  /* EDDIES 计数（导航栏装饰） */
  const ed = document.getElementById('eddies');
  if(ed){
    const target = 528888; let cur = 0;
    const t = setInterval(()=>{
      cur += 2200;
      if(cur >= target){ cur = target; clearInterval(t); }
      ed.textContent = cur.toLocaleString();
    }, 40);
  }

  /* 光标光晕 */
  const glow = document.getElementById('cursor-glow');
  if(glow){
    let gx = innerWidth/2, gy = innerHeight/2, cx = gx, cy = gy;
    addEventListener('mousemove', e=>{ gx = e.clientX; gy = e.clientY; });
    (function loop(){
      cx += (gx-cx)*.08; cy += (gy-cy)*.08;
      glow.style.left = cx+'px'; glow.style.top = cy+'px';
      requestAnimationFrame(loop);
    })();
  }

  /* 移动端菜单：点击链接后收起 */
  const burger = document.getElementById('nav-burger');
  const links = document.getElementById('nav-links');
  if(burger && links){
    burger.addEventListener('click', ()=> links.classList.toggle('open'));
    links.querySelectorAll('a').forEach(a=>
      a.addEventListener('click', ()=> links.classList.remove('open')));
  }

  /* 偶发全局故障闪动 */
  setInterval(()=>{
    if(Math.random() < .3){
      document.body.animate(
        [{filter:'none'},{filter:'hue-rotate(15deg) contrast(1.1) saturate(1.3)'},{filter:'none'}],
        {duration:180, iterations:1}
      );
    }
  }, 9000);
})();
