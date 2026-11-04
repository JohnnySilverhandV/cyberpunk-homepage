# 夜之城个人终端 · 开发技术复盘

> **TECH RETROSPECTIVE** · 2026.10.09 — 2026.10.18 · NIGHT CITY PERSONAL TERMINAL

从一句「想要一个赛博朋克 2077 风格的主页」，到一个朋友能打开、六段超梦回放能播、全站 20MB 的线上站点。  
这份笔记不写流水账，只记**做对的决策、被推翻的方案、和真正花时间的坑**——每一条都对应到具体代码或命令。

`单文件 HTML`　`1359 行源码`　`0 前端框架`　`6 段超梦回放`　`92MB → 20.4MiB`　`静态托管`

---

## 关键数据

| 指标      | 数值         | 说明                  |
| ------- | ---------- | ------------------- |
| 交付周期    | **3 天**    | 需求 → 上线             |
| 源码规模    | **1359 行** | 单文件 `index.html`    |
| 视频体积    | **−79.2%** | 90.0 MiB → 18.7 MiB |
| HTML 体积 | **−16.9%** | 77.6 KB → 64.5 KB   |
| 回放可用性   | **6 / 6**  | 六段超梦全部点亮            |
| 运行时依赖   | **0**      | 无框架、无 CDN 运行时       |

---

## 目录

| #  | 章节                                       | 内容重点                            |
| -- | ---------------------------------------- | ------------------------------- |
| 01 | [架构与选型决策](#01-架构与选型决策)                   | 单文件、无框架、CONFIG 集中、源码产物分离        |
| 02 | [视觉系统的实现](#02-视觉系统的实现)                   | 设计令牌、三层字体、故障字、扫描带、噪点、视差         |
| 03 | [交互动效层](#03-交互动效层)                       | 开机序列、打字机、滚动驱动、跑马灯、终端彩蛋          |
| 04 | [超梦播放器（三代演进）](#04-超梦播放器三代演进)             | iframe → 原生 video、结束投影、自动播放、注册表 |
| 05 | [性能压缩：92MB → 20MB](#05-性能压缩92mb--204mib) | sips、ffmpeg 参数逐条、avconvert 弃用原因 |
| 06 | [工程化与构建链](#06-工程化与构建链)                   | 目录结构、构建命令、双份文件的风险               |
| 07 | [调试方法论](#07-调试方法论)                       | CDP 求值、探针注入、canvas 抓帧、环境陷阱      |
| 08 | [部署与验证](#08-部署与验证)                       | 静态托管、发布后必查三件事、旧快照事故             |
| 09 | [踩坑清单](#09-踩坑清单)                         | 12 条真实翻车，附根因与修复                 |
| 10 | [可复用要点](#10-可复用要点)                       | 可直接抄走的清单                        |

---

## 01 架构与选型决策

> 四个决定了后续一切成本的选择

### 决策一：单文件 HTML，不上构建

整个站点是一个 `index.html`：内联 CSS、内联 JS、零外部脚本。理由不是"偷懒"，而是三个具体约束：

- **可双击打开**——朋友拿到文件夹就能看，不需要 `npm install`、不需要 `vite dev`；
- **托管零配置**——任何静态服务器把目录一丢就能跑，发布流程只有"上传"一步；
- **没有构建期就没有构建期故障**——不会出现依赖版本漂移、node_modules 体积、CI 缓存失效这类问题。

代价是作用域污染。解法是**用 IIFE 手动切模块**：每一块独立功能都包在立即执行函数里，只在 `window` 上留必要的一个钩子。

```js
/* 每一段功能 = 一个 IIFE，变量随函数执行结束离开作用域 */
(function(){
  const io = new IntersectionObserver(entries => { /* ... */ }, {threshold: .15});
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));
})();

(function(){
  const track = document.getElementById('ticker-track');
  /* ... */
})();
```

唯一跨模块的耦合点是启动顺序：开机动画结束后要主动调用 `startTyped()`，所以它以**函数声明**（而非 IIFE）暴露在全局，其余全部封闭。

### 决策二：不用框架，用原生 API

页面的"动态性"其实只有四类需求，原生 API 全部覆盖，引入框架反而是净负担：

| 需求             | 原生方案                        | 为什么不用框架                    |
| -------------- | --------------------------- | -------------------------- |
| 滚动到视口触发动画      | `IntersectionObserver`      | 比 scroll 监听省一次重排，且是浏览器原生调度 |
| 逐帧跟随（光标、数字滚动）  | `requestAnimationFrame`     | 需要精确控制每一帧，虚拟 DOM 无能为力      |
| 一次性突发动画（全局故障）  | `element.animate()`（WAAPI）  | 命令式、不污染 CSS、自动销毁           |
| 状态切换（面板/弹窗/菜单） | `classList.toggle` + CSS 过渡 | 状态只有开/关两态，不需要响应式系统         |

> **判断标准**  
> 是否引入框架，看的&#x662F;**「状态派生关系的复杂度」**，不是「页面酷不酷」。这个页面所有状态都是单点布尔值，派生关系为零，所以原生足够。如果要做多视图路由 + 数据驱动的列表渲染，结论会立刻反转。

### 决策三：内容收进一个 CONFIG 对象

文案、代号、语录、文章列表、义体数据全部集中在 `CONFIG`。这样做的好处是**改内容不用碰结构**——后来瑞哥自己把代号改成「张瑞.」、把「网络黑客」整篇换成「高塔晚风」，都只需要动这个对象里的几个字段。

```js
const CONFIG = {
  callsign: '张瑞.',
  handle:   '瑞哥. TERMINAL',
  typedLines: [ '...', '...' ],      // 打字机循环的句子
  posts: [                           // 超梦档案 = 博客卡片
    { tag:'高塔晚风', date:'2077.08.03', videoKey:'tower',
      title:'夜之城没有真东西，她不一样', excerpt:'...' }
  ],
  cyberware: [ /* 义体条目：名称/等级/描述 */ ],
  tickerItems: [ ['NCPD 通缉', '...'] ]
};
```

### 决策四：源码与产物分离（后期补的）

压缩 HTML 之后必须保留可读版本，否则后续维护等于在压缩代码上做手术。最终目录是 `src/index.source.html`（可读源码）+ `index.html`（构建产物）+ 一个 40 行的构建脚本。

> 这个决策的**副作用**在第 6 节会讲——它制造了一个「改哪份」的陷阱。

---

## 02 视觉系统的实现

> 赛博朋克不是"加点霓虹"，而是一套可复用的色彩、字体、噪声语言

### 2.1 设计令牌：先把颜色定死

所有颜色走 CSS 自定义属性，一处改全局生效。CP2077 的标志性黄（`#FCEE0A`）是**低明度高饱和**的黄，它只能在深色底上大面积使用；一旦挪到浅色底就会直接失明——这也是这份笔记没有沿用它的原因。

```css
:root{
  --yellow:#FCEE0A;   /* 主强调：标题、HUD 边框 */
  --cyan:#00F0FF;     /* 次级：数据、扫描线、链接 */
  --red:#FF003C;      /* 警告 / 故障红通道 */
  --pink:#FF2E88;     /* 点缀：广告牌、标签 */
  --bg:#04060A;       /* 近黑，带一点蓝，不是纯黑 */
  --panel:rgba(8,13,20,.82);  /* 半透明面板，让噪点透出来 */
  --line:rgba(0,240,255,.18);  /* 细边界，比实色柔和 */
  --text:#D8E4EC;      /* 冷白，不用 #fff（太刺） */
}
```

> **技术点** — 背景用 `#04060A` 而不是 `#000`：纯黑会让霓虹边缘显得"漂浮"，带一点蓝的近黑能给辉光提供"底色的厚度"，同时降低 OLED 屏上的拖影观感。

### 2.2 字体三层结构

| 层   | 字体              | 用途           | 回退策略                                   |
| --- | --------------- | ------------ | -------------------------------------- |
| 展示层 | Orbitron        | 代号、大标题、数字    | 断网时回退到 `PingFang SC` / 系统等宽，风格打折但可读性不塌 |
| 界面层 | Rajdhani        | 正文、导航、按钮     | 同上                                     |
| 数据层 | Share Tech Mono | HUD、时间码、终端输出 | 同上                                     |

这是刻意的**三档而不是两档**：等宽字体负责"机器感"，无衬线负责"可读性"，展示字体负责"识别度"。三者混用形成了 CP2077 那种"军用设备 + 商业广告"的错位感。

### 2.3 RGB 色差故障字：两个伪元素 + clip-path 切片

这是全站最核心的视觉母题。实现上没有用任何图片或 shader，纯粹是两层伪元素叠在文字背后，分别染成青色和红色，然后用 `clip-path: inset()` 裁成横向条带、做微小位移。

```css
.glitch{position:relative; display:inline-block}

.glitch::before{  /* 青通道 */
  content:attr(data-text);
  color:var(--cyan); z-index:-1;
  animation:gl-a 3.2s infinite steps(1);
}
.glitch::after{   /* 红通道 */
  content:attr(data-text);
  color:var(--red); z-index:-2;
  animation:gl-b 2.7s infinite steps(1);
}

/* 关键帧：88% 之前完全静止，89%~95% 突然切三次条带 */
@keyframes gl-a{
  0%,88%,100%{transform:translate(0); opacity:0}
  89%{transform:translate(-4px,2px); clip-path:inset(10% 0 55% 0)}
  91%{transform:translate(3px,-1px);  clip-path:inset(60% 0 8% 0)}
  93%{transform:translate(-2px,0);   clip-path:inset(30% 0 40% 0)}
  95%{opacity:0}
}
```

| 技术点                  | 为什么这么做                                                                 |
| -------------------- | ---------------------------------------------------------------------- |
| `steps(1)` 而非 ease   | 故障的本质是**瞬间跳变**。加缓动就变成"抖动"，立刻从数字故障变成廉价动画。                               |
| `0%,88%` 长时间定格       | 故障要**稀缺**才有冲击力。持续故障 = 视觉噪声，用户会开始忽略它。                                   |
| `clip-path: inset()` | 做出"横向扫描线撕裂"的形状，比单纯位移更像信号损坏；且不影响布局盒模型。                                  |
| 两层而非一层               | 青 / 红两通道错位 = 色差分离（chromatic aberration），这是 CRT 与廉价镜头的物理特征，比"单色重影"真实得多。 |
| 两个不同周期（3.2s / 2.7s）  | 周期互质，合成后的故障节奏永不重复，避免用户产生"每 3 秒一次"的规律感。                                 |

还有一个交互层：`:hover` 时把周期压到 `.4s / .35s`。鼠标移上去，故障从"偶发"变成"高频"——这是给可交互元素加的**可点击性提示**，不靠下划线、不靠颜色变化。

### 2.4 CRT 扫描带：一条会走完全屏的亮带

```css
.fx-crtbar{
  position:fixed; left:0; right:0; height:120px;
  pointer-events:none;   /* 绝不拦截鼠标 */
  z-index:9001;
  animation:crtbar 7s linear infinite;
}
@keyframes crtbar{ 0%{top:-15%} 100%{top:110%} }
```

> **技术点** — **起止位置要出界**（`-15%` → `110%`）而不是 `0` → `100%`。否则亮带在屏幕边缘会"凭空出现/消失"，破坏运动的连续性；出界 15% 让它从画外滑入、滑出画外。另外 `pointer-events:none` 是全屏特效层的硬性要求，漏了这个整站就点不动了。

### 2.5 胶片噪点：必须动起来，否则只是"脏"

噪点用内联 SVG 的 `feTurbulence` 生成，作为 data URI 平铺。但静态噪点会被眼睛识别为"图片质量差"，所以关键在**每 0.45 秒跳一次位置**：

```css
.fx-noise{
  background-image:url("data:image/svg+xml,...feTurbulence baseFrequency='.8'...");
  opacity:.055;
  animation:noiseShift .45s steps(3) infinite;
}
@keyframes noiseShift{
  0%  {transform:translate(0,0)}
  33% {transform:translate(-2%,1%)}
  66% {transform:translate(1%,-2%)}
  100%{transform:translate(0,0)}
}
```

| 参数         | 取值     | 理由                               |
| ---------- | ------ | -------------------------------- |
| 不透明度       | `.055` | 超过 .1 就看得见颗粒形状，从"胶片"变成"低画质"      |
| `steps(3)` | 3 帧    | 模拟胶片 24fps 下的颗粒跳动；连续位移会变成"飘动的纹理" |
| 位移幅度       | 1~2%   | 大于 3% 会有明显的"图层在滑"的破绽             |

### 2.6 鼠标视差：6% 的 overscan 是硬要求

```js
const img = document.getElementById('hero-img');
addEventListener('mousemove', e => {
  const dx = (e.clientX / innerWidth  - .5) * 14;   // ±7px
  const dy = (e.clientY / innerHeight - .5) * 10;   // ±5px
  img.style.transform = `scale(1.06) translate(${-dx}px,${-dy}px)`;
});
```

`scale(1.06)` 不是装饰，是**位移留出的余量**：图片放大 6%（1920px 图 ≈ 115px 余量）远大于最大位移 7px，所以画面永远不会露出容器底色。少了这个 `scale`，鼠标移到边角就会看到一条白边——这是所有"视差首图"最常见的翻车点。

另外位移方向取**反**（`-dx`）：鼠标右移，画面左移，形成"镜头在物体前面"的深度感。同向移动会变成"画面跟着鼠标走"，更廉价。

### 2.7 光标光晕：lerp 插值，以及它的已知局限

```js
let gx = innerWidth/2, gy = innerHeight/2, cx = gx, cy = gy;
addEventListener('mousemove', e => { gx = e.clientX; gy = e.clientY; });

(function loop(){
  cx += (gx - cx) * .08;          // 线性插值：每帧靠近目标 8%
  cy += (gy - cy) * .08;
  glow.style.left = cx + 'px';
  glow.style.top  = cy + 'px';
  requestAnimationFrame(loop);
})();
```

> **已知局限** — 这个 `0.08` 是**帧率相关**的：60Hz 屏上每秒收敛 4.8 倍，120Hz 屏上会快一倍，观感不一致。更严谨的写法是按帧间隔做指数衰减：`k = 1 - Math.pow(1 - 0.08, dt / 16.67)`，`dt` 取 `requestAnimationFrame` 回调的时间戳差。这一版没改，因为拖尾效果差异在这个视觉强度下不可感知——但这是个值得记下来的正确做法。

---

## 03 交互动效层

> 五个小机制，决定页面是"能看"还是"好用"

### 3.1 开机自检序列：幂等的 finish()

首屏是一段 "WAKE UP, 瑞哥\_" 的神经链路自检。它有三个出口：**逐行走完、点击跳过、3.4 秒兜底超时**。三条路径都能触发 `finish()`，所以必须幂等，否则打字机会被启动两次、滚动锁会被提前释放。

```js
let done = false;
const finish = () => {
  if(done) return;        // ← 幂等守卫，整个机制的核心
  done = true;
  boot.classList.add('done');
  document.body.style.overflow = '';   // 解锁滚动
  startTyped();
};

const timer = setInterval(() => {
  if(i >= seq.length){ clearInterval(timer); bar.style.width = '100%'; setTimeout(finish, 550); return; }
  /* 逐行追加，进度条封顶在 92% —— 最后 8% 留给"收尾"动作 */
  bar.style.width = Math.round(((i+1)/seq.length) * 92) + '%';
}, 300);

boot.addEventListener('click', finish);   // 出口 2：点击跳过
document.body.style.overflow = 'hidden';         // 先锁滚动
setTimeout(finish, 3400);                        // 出口 3：兜底
```

| 细节                | 用意                                                  |
| ----------------- | --------------------------------------------------- |
| 进度条封顶 92%         | 真实进度条不会"走满才算完"，最后一段必须由完成事件补齐。这一下就把"假加载"演成了真的。       |
| 锁 `body.overflow` | 开机层是全屏 fixed，但底下页面仍在滚动上下文里。不锁会出现在动画期间已经滚到中间的诡异状态。   |
| 3.4s 兜底           | 如果某一行数据异常导致循环不结束，用户会被永久锁在黑屏。**任何全屏遮罩都必须有一条超时逃生路径。** |

### 3.2 打字机：节奏不能均匀

```js
if(!deleting){
  el.textContent = line.slice(0, ++ci);
  if(ci === line.length){ deleting = true; setTimeout(tick, 2400); return; }  // 打完停 2.4s
  setTimeout(tick, 55 + Math.random()*60);      // 55~115ms 随机
} else {
  el.textContent = line.slice(0, --ci);
  setTimeout(tick, 22);                            // 删除固定快
}
```

三个节奏参数各自有理由：**打字随机**（人手不是节拍器）、**删除固定且更快**（回退是机器动作）、**打完停顿 2.4 秒**（给读者读完的时间）。全用同一个 interval 会立刻显出"程序在循环"。

### 3.3 滚动驱动：IntersectionObserver 双阈值

```js
// 入场显现 + 属性条填充：阈值 .15
const io = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if(!e.isIntersecting) return;
    e.target.classList.add('in');
    e.target.querySelectorAll('.bar i').forEach(b => {
      b.style.right = (100 - parseFloat(b.dataset.w)) + '%';
    });
    io.unobserve(e.target);          // 只触发一次
  });
}, {threshold: .15});

// 数字滚动：阈值 .5，必须先看到一半才开始数
const p = Math.min((t - t0)/dur, 1);
el.textContent = Math.round(target * (1 - Math.pow(1-p, 3))).toLocaleString();  // easeOutCubic
```

> **技术点** — `unobserve` 是必需的。不加的话每次滚动进出都会重跑动画，用户上下滑动时数字会反复跳到 0 再数上去，非常廉价。
>
> 阈值差异也有效：**显现用 .15**（露一点就开始，避免"滑过去了才出现"的空窗）；**计数用 .5**（数字必须进视口一半再跑，否则用户看不到起始值，滚动感变成"突然变了个数"）。

另一处细节：滚动监听加 `{passive: true}`，告诉浏览器"我不会 `preventDefault`"，浏览器就能把滚动交给合成线程，主线程卡顿不会拖住滚动。

```js
addEventListener('scroll', () => {
  let cur = -1;
  secs.forEach((s,i) => { if(s && s.getBoundingClientRect().top < innerHeight*.4) cur = i; });
  links.forEach((a,i) => a.classList.toggle('active', i === cur));
}, {passive: true});
```

### 3.4 无缝跑马灯：复制一份内容

```js
const items = CONFIG.tickerItems.map(...).join('');
track.innerHTML = items + items;   // 内容复制一份 → 位移 -50% 时首尾严丝合缝

/* CSS 侧 */
.ticker-track{ animation:ticker 32s linear infinite }
@keyframes ticker{ to{ transform:translateX(-50%) } }
```


> **技术点** — 无缝滚动的通用解法：**把轨道内容整体复制一遍，动画位移恰好等于原来那份的宽度**。因为复制后总宽翻倍，`-50%` 就等于一份的宽度，循环回到 0% 时视觉上完全连续。这里用百分比而不是 px，所以内容多少、字体加载后宽度变化，都不会错位。

### 3.5 终端：命令表 + 一个彩蛋

```js
const commands = {
  help(){ /* 列出可用指令 */ },
  whoami(){ /* 输出代号与职业 */ },
  contact(){ /* 输出联系方式 */ },
  clear(){ /* 清屏 */ },
  burn(){                                     /* 彩蛋：烧城 4 秒 */
    const ov = document.getElementById('burn-overlay');
    document.body.classList.add('burning');
    ov.classList.add('on');
    setTimeout(() => { ov.classList.remove('on'); document.body.classList.remove('burning'); }, 4000);
  }
};
commands['sfm'] = () => print('强尼说: 这个指令不存在,武士。', 't-err');  // 后注册

// 分发：查表 + 未知命令兜底
if(commands[cmd]) commands[cmd]();
else print(`未识别指令: ${cmd} — 输入 help`, 't-err');
```

彩蛋的技术实现值得一提：**不改任何布局，只切一个 body class**——`body.burning` 下给首图套上 `filter: saturate(1.6) hue-rotate(-30deg) contrast(1.15)`，再叠一层 `animation: burnPulse` 呼吸式提亮（`brightness .9 ↔ 1.35`）。4 秒后自动清除，不需要"关闭"按钮，也不留状态残留。

---

## 04 超梦播放器（三代演进）

> 这个模块改了三次，每一次都是被一个具体问题推翻的

| 代际    | 时间      | 方案                          | 关键问题                                                 |
| ----- | ------- | --------------------------- | ---------------------------------------------------- |
| GEN 1 | 10.09   | iframe 外链播放器 + 时长推算         | 用 B 站 `player.html` 内嵌，硬编码 `duration: 61`，靠定时器推算"播完" |
| GEN 2 | 10.10   | 发现问题：空白 + 出戏 + 状态不可知        | 嵌入环境下一片黑屏；播放器自带弹幕/推荐/分享 UI 严重破坏沉浸感；跨域 iframe 读不到播放进度 |
| GEN 3 | 10.10 起 | 原生 `<video>` + 自绘 HUD + 注册表 | 视频落本地，用真 `ended` 事件驱动结束特效，进度条/时间码自己画，六个视频走配置注册       |

### 4.1 为什么必须换掉 iframe

| iframe 方案                         | 原生 video 方案                    |
| --------------------------------- | ------------------------------ |
| 跨域，读不到 `currentTime` / `duration` | 同源，全部状态可读可写                    |
| 播放状态只能靠外部定时器猜                     | `ended` 事件 = 唯一可靠的播放结束信号       |
| 第三方 UI 无法移除（弹幕、推荐、logo）           | `controls=false`，UI 100% 自绘    |
| 嵌入环境有加载黑屏风险                       | 首帧加载通常更快（少一层播放器初始化）            |
| 用户暂停 → 推算的时间继续走 → 特效提前触发          | 可以 `playbackRate`、`muted` 自由控制 |

### 4.2 全息投影的视觉构成

打开回放时看到的"投影仪"其实是四层独立元素叠出来的，没有用任何贴图：

| 层     | 实现                                 | 作用             |
| ----- | ---------------------------------- | -------------- |
| 光锥    | `clip-path` 梯形 + 纵向渐变              | 从底部射向幕布的体积光    |
| 地面光斑  | 椭圆 + `blur` + 低透明度青色               | 让光锥"落地"，建立空间关系 |
| 幕布扫描线 | `repeating-linear-gradient` 1px 横线 | 投影面的 CRT 质感    |
| 全息闪烁  | `bdHoloFlicker`：不规则透明度跳变           | "廉价投影仪在抖"的心理暗示 |

闪烁曲线是**刻意不规律**的——如果每 0.5 秒均匀闪一次，大脑会归类为"呼吸灯"；只有长短不一的跳变才会被解读为"不稳定设备"。

### 4.3 结束投影特效：1.5 秒的 6 段时间轴

这是整个项目里技术含量最高的一段动画：视频放完的瞬间，幕布像被断电一样**纵向塌缩成一条光带**。核心是 `scaleY` 从 1 压到 0，配合 `transform-origin: bottom`，并让亮度反向飙升来制造"能量被压缩"的错觉。

```css
#bd-player.ending .bd-frame{
  animation:bdHoloOut 1.5s cubic-bezier(.5,0,.75,0) forwards;
}
@keyframes bdHoloOut{
  0%  {opacity:1; transform:none; filter:none}
  16% {transform:translateX(-9px) scaleY(1.02); filter:brightness(1.7) saturate(1.4) hue-rotate(-8deg)}
  25% {transform:translateX(10px) skewX(-2deg);  filter:brightness(1.5) hue-rotate(12deg)}
  40% {transform:scaleY(.62) translateY(4px);   filter:brightness(2.5) opacity:.96}
  60% {transform:scaleY(.17) scaleX(1.03);  filter:brightness(3.6) blur(1.5px)}
  76% {transform:scaleY(.03) scaleX(1.08);  filter:brightness(5)   blur(1px)}
  100%{transform:scaleY(0)   scaleX(1.16);  filter:brightness(6.5) blur(3px); opacity:0}
}
```

| 时间        | 画面       | 技术手段                                                |
| --------- | -------- | --------------------------------------------------- |
| 0 – 16%   | RGB 撕裂抖动 | `translateX` 正负跳变 + `skewX` 斜切 + `hue-rotate` 色相偏移  |
| 16 – 40%  | 开始纵向压缩   | `scaleY` 1 → .62，同时 `brightness` 1.7 → 2.5          |
| 40 – 76%  | 压成极窄光带   | `scaleY` .17 → .03，`scaleX` 略增（压缩守恒的视觉暗示），`blur` 加晕 |
| 76 – 100% | 白光爆闪后消失  | `brightness` 飙到 6.5 + `blur(3px)` + `opacity 0`     |

> **三个关键手法**
>
> **① `transform-origin: bottom`**——塌缩的锚点在底部，画面才会像"被投影仪收回"一样从下往上收，而不是从中心缩小（那看起来像"缩略图动画"）。
>
> **② 亮度与压缩量成反比**——面积越小、亮度越高。物理上不通，但知觉上"能量被压进一条线"的暗示极强，这是所有科幻 HUD 断电特效的通用配方。
>
> **③ 缓动不是 ease**——`cubic-bezier(.5,0,.75,0)` 是"慢起、后段猛烈加速"，模拟机械惯性而不是匀速收缩。

同一时间轴上还并行了四条独立动画（都锁 1.5s，靠 `forwards` 定格）：光锥与地面光斑淡出（`bdBeamOut`）、HUD 上下栏延迟 30% 后淡出（`bdHudOut`）、底部白色光带横向拉伸（`bdCollapse`）、以及"信号丢失"文字（`bdEndFlash`，36% 时以 `letter-spacing: .3em` 淡入，做出"扫描确认"的节奏）。

### 4.4 用真实 ended 事件，而不是算时长

```js
vid.addEventListener('ended', end);   // ← 唯一可靠的"播完"信号

function end(){
  if(wiping) return;                  // 防重入：ended 与手动按钮可能同时触发
  wiping = true;
  const d = (vid && isFinite(vid.duration)) ? vid.duration : 0;
  if(vid){ try{ vid.pause(); }catch(err){} }

  player.classList.add('ending');       // 这一行触发全部 1.5s 动画
  setTimeout(() => {
    player.classList.remove('open', 'ending');
    mount.innerHTML = '';                 // 移除 video 元素 → 释放解码器
    vid = null;
    document.body.classList.remove('bd-open');  // 解锁滚动
    toast('// BD-CHIP 回放结束 · 全息投影已断开');
  }, 1560);                                // 比动画 1500ms 多 60ms，等最后一帧落定
}
```

| 设计选择                                                | 原因                                                   |
| --------------------------------------------------- | ---------------------------------------------------- |
| `ended` 而非 `timeupdate` 判 `currentTime >= duration` | `timeupdate` 触发频率约 4Hz，且末尾可能不触发；`ended` 是规范事件，一次且仅一次 |
| `wiping` 布尔锁                                        | `ended` 和用户点「结束投影」可能在同一帧发生，不加锁会播两遍                   |
| `1560ms` 而非 `1500ms`                                | 动画最后一帧是 `opacity:0`，但合成层可能还有一帧残留；多给 60ms 避免"闪一下又出现"  |
| 移除 `video` 元素而非 `pause()`                           | 隐藏的 video 仍占解码器与内存；`innerHTML=''` 让 GC 能真正回收         |

### 4.5 自动播放：必须在手势调用栈里调 play()

```js
vid = document.createElement('video');
vid.src = bd.src;
vid.preload = 'auto';
vid.controls = false;          // 用自家 HUD，浏览器控件全部关掉
vid.playsInline = true;         // 属性写法（iOS）
vid.setAttribute('playsinline', '');
vid.setAttribute('webkit-playsinline', '');   // 老版 iOS 专有

// 关键：这一行在 click 处理器内同步执行 → 命中 user activation → 允许带声音播放
const p = vid.play();
if(p && p.catch) p.catch(() => setPP(false));   // play() 返回 Promise，必须兜住 NotAllowedError
```

> **浏览器策略** — Chrome / Safari 只允许**在用户手势的调用栈内**启动带声音的媒体播放。若把 `play()` 放进 `setTimeout`、`await fetch` 之后、或 `load` 事件回调里，`user activation` 已失效，播放会被拒绝（`NotAllowedError`）。这正是为什么 `open()` 里创建元素后**立刻同步**调 `play()`，而不是等 `canplay`。

`playsinline` 同理是硬要求：iOS Safari 上不声明它，视频会劫持全屏，整个全息投影框直接消失。两套写法（属性和 `setAttribute`）都要给，因为老版本 WebKit 只认 `webkit-playsinline`，而新规范认 `playsinline`。

### 4.6 六视频注册表：加文件即生效

六个视频不能写死成一堆 `if`。方案是**注册表 + 声明式数据**：文章对象里只存 `videoKey`，播放器按 key 查表拿 `{src, label}`。HUD 顶部的编号也随之自动切换。

```js
const BD_SOURCES = {
  quickhack : { src:'assets/bd-quickhack.mp4', label:'QUICKHACK_ICE_BREAK'   },
  cyberware : { src:'assets/bd-cyberware.mp4', label:'CYBERWARE_DIAGNOSTIC'  },
  frontend  : { src:'assets/bd-frontend.mp4',  label:'HUD_SPEC_V2'           },
  badlands  : { src:'assets/bd-badlands.mp4',  label:'BADLANDS_ROADTRIP'     },
  tower     : { src:'assets/bd-tower.mp4',     label:'TOWER_EVENING_WIND'    },
  afterlife : { src:'assets/bd-afterlife.mp4', label:'AFTERLIFE_BAR_STORIES' }
};

// 打开时按 key 取，HUD 自动换编号
label.textContent = 'BD-CHIP 回放中 // ' + bd.label + '.BD';
```

配套的是**文件存在性探测**：页面加载后对每个源发 `HEAD` 请求，只有确认存在才点亮「接入回放」，否则保持不可点。这样"视频还没上传"的中间状态不会产生死链——用户点了黑屏，比按钮灰着糟糕得多。

```js
// 三级放行策略
for(const a of links){
  const bd = BD_SOURCES[a.dataset.key];
  if(!bd) continue;

  // ① 本地 file:// 直接放行（该协议下 fetch 必然失败，见第 9 节）
  if(isLocalFile){ a.classList.add('ready'); continue; }

  try{
    const r = await fetch(bd.src, { method: 'HEAD' });
    // ② 只有明确「不存在」才锁住；405 / 403 / 500 一律放行
    if(r.ok || (r.status !== 404 && r.status !== 410)) a.classList.add('ready');
  }catch(err){
    // ③ 探测本身失败（跨域 / 离线 / file:）也放行
    a.classList.add('ready');
  }
}
```

> **为什么不是 `if (r.ok)` 就完事**
>
> `HEAD` 不是所有静态服务器都实现。部分服务器对 `HEAD` 返回 **405 Method Not Allowed**，文件明明存在却被判定为"没有"。所以判定逻辑必须是**黑名单（404/410）而不是白名单（200）**——这是"渐进增强"在探测场景的具体形态：*默认可用，只有确定不可用时才禁用*。

### 4.7 生命周期：那个真实存在的空指针

播放器关闭时把 `vid = null`，但如果此时还有一帧 `timeupdate` 在队列里没执行，回调里访问 `vid.duration` 就会抛 `TypeError`。表现是控制台红色报错 + 下一帧动画轻微卡顿。

```js
vid.addEventListener('timeupdate', () => {
  if(!vid) return;        // ← 守卫：元素可能已被移除
  const d = vid.duration || 0;
  if(d > 0){
    progEl.style.right = (100 - Math.min(vid.currentTime / d, 1) * 100) + '%';
    timeEl.textContent = fmt(vid.currentTime) + ' / ' + fmt(d);
  }
});
```

> **通用规则** — 凡是**异步回调里引用了可被销毁的对象**，回调第一行必须是空值守卫。事件监听不会因为元素被移除就自动注销——在 `innerHTML=''` 之后，绑定在元素上的回调仍可能因为已排队的任务而执行一次。

---

## 05 性能压缩：92MB → 20.4MiB

> 视频占 95%，所以先动视频；代码只有 64KB，压它是收益结构问题不是体积问题

### 5.1 图片：PNG 换 JPEG + 限制最长边

```bash
# macOS 自带 sips
sips -s format jpeg -s formatOptions 85 -Z 800  portrait.png      --out portrait.jpg
sips -s format jpeg -s formatOptions 88 -Z 1920 hero-city.png     --out hero-city.jpg
sips -s format jpeg -s formatOptions 88 -Z 1100 cyberware-arm.png --out cyberware-arm.jpg
```

| 文件                | 之前     | 之后     | 降幅   | 关键动作         |
| ----------------- | ------ | ------ | ---- | ------------ |
| portrait（肖像）      | 5.3 MB | 209 KB | −96% | 最长边压到 800px  |
| hero-city（首图）     | 2.5 MB | 915 KB | −64% | 1920px + q88 |
| cyberware-arm（义体） | 1.5 MB | 419 KB | −73% | 1100px + q88 |

> **技术点**
>
> **① PNG 不适合照片。** PNG 是无损格式，一张 1024×1024 的人像 PNG 里每个像素占 3~4 字节原始数据，压缩后仍有几 MB；JPEG 走 DCT 有损编码，同样观感只要几百 KB。只有需要透明通道或纯色图形时才该用 PNG。
>
> **② 分辨率上限比压缩质量更省。** 肖像在页面上最宽只显示约 400px，撑到 2 倍屏也只需要 800px。把 2048px 的图压到 800px，比继续调 JPEG 质量参数省得多，且观感无损——因为多余的像素根本没被用到。
>
> **③ `-Z` 是"最长边"，不是宽或高。** 竖图横图都能正确约束，不会变形。

### 5.2 视频：ffmpeg 一组参数，逐个解释

```bash
FF=<ffmpeg 可执行路径>

# 1080p 的两支先降到 720p，其余保持原分辨率
$FF -y -i bd-frontend.mp4  -vf scale=1280:-2 \
    -c:v libx264 -preset medium -crf 22 -pix_fmt yuv420p \
    -movflags +faststart -c:a aac -b:a 128k \
    out/bd-frontend.mp4
```

| 参数                     | 作用               | 为什么是这个值                                       |
| ---------------------- | ---------------- | --------------------------------------------- |
| `-c:v libx264`         | H.264 编码器        | 浏览器/移动端/硬件解码全支持，兼容性天花板                        |
| `-crf 22`              | 恒定质量（0–51，越小越好）  | 18–28 是常用区间；22 偏保守，视觉上接近无损                    |
| `-preset medium`       | 编码速度 / 压缩率折中     | `slow` 只多省 5~8% 但耗时翻倍，不值得                     |
| `-pix_fmt yuv420p`     | 色彩采样 4:2:0       | **兼容性硬要求**：`yuv444p` / 10bit 很多浏览器不支持硬解甚至无法播放 |
| `-movflags +faststart` | 把 `moov` 原子移到文件头 | 否则必须先下完整个文件才能播；加了才能边下边播                       |
| `-c:a aac -b:a 128k`   | 音频重编码            | 128k 立体声是"透明"的经验值；视频里主要是人声与环境音                |
| `-vf scale=1280:-2`    | 缩放到宽 1280        | `-2` 不是 `-1`：H.264 要求宽高都是偶数，`-2` 会自动取最近的偶数    |

| 视频                 | 原始           | 压缩后          | 降幅         |
| ------------------ | ------------ | ------------ | ---------- |
| bd-frontend（前端工程）  | 40.1 MB      | 6.01 MB      | −85.0%     |
| bd-afterlife（来世酒吧） | 19.1 MB      | 1.78 MB      | −90.6%     |
| bd-quickhack（快速黑客） | 8.96 MB      | 4.13 MB      | −53.9%     |
| bd-cyberware（义体改造） | 8.57 MB      | 3.20 MB      | −62.7%     |
| bd-badlands（恶土见闻）  | 8.68 MB      | 2.37 MB      | −72.7%     |
| bd-tower（高塔晚风）     | 8.97 MB      | 2.14 MB      | −76.2%     |
| **合计**             | **90.0 MiB** | **18.7 MiB** | **−79.2%** |

> **降幅差异为什么这么大**
>
> `bd-afterlife` 掉了 90%，`bd-quickhack` 只掉 54%——不是参数不同，是**源文件码率不同**。原始文件如果是"高码率但画面简单"（静态机位、大面积纯色），CRF 22 能砍掉绝大部分冗余；如果源片本身就是压缩过的低码率，再编码只能省下重新量化的空间。**压缩率不是参数决定的，是素材复杂度决定的。**

### 5.3 弃用 macOS 自带 avconvert 的原因

| 预设                     | 实测结果         | 问题                           |
| ---------------------- | ------------ | ---------------------------- |
| `PresetAppleM4VWiFi`   | 38MB → 2.5MB | **实际输出 480×272**，画面糊成马赛克，不可用 |
| `PresetAppleM4V720pHD` | 38MB → 19MB  | 码率约 7.5Mbps，比源文件还高，压缩意义为零    |

`avconvert` 的预设面向"设备播放档位"（WiFi / 蜂窝 / HD），**不暴露 CRF、码率、分辨率这些可控参数**。想精确控制压缩率就必须上 ffmpeg。这里还有一个环境坑：`ffmpeg-static` 从 GitHub 拉二进制在国内网络下会长期卡住，改用 npm 源分发的 `@ffmpeg-installer/ffmpeg` 才能装下来（见第 9 节）。


### 5.4 HTML：−16.9%，并且刻意停在这里

```js
// 构建脚本核心配置
const after = await minify(before, {
  collapseWhitespace: true,
  removeComments: true,
  minifyCSS,                     // 走 clean-css level 1（保守）
  minifyJS: true,                // 走 terser
  removeAttributeQuotes: true,
  removeRedundantAttributes: true,
  collapseBooleanAttributes: true,
  useShortDoctype: true,
  keepClosingSlash: true,
  sortAttributes: false,        // 不重排属性，diff 更可读
  sortClassName: false           // 不重排 class，避免和调试工具对照困难
});
```

**结论**：77.6 KB → 64.5 KB，省 13.0 KB（−16.9%）。对一个已经开了 gzip 的静态站，这 13KB 传输后差距不到 4KB。

**为什么不用 clean-css level 2**：实测只多省 1.5 KB，但 level 2 会**合并重复规则、重构规则顺序**，层叠优先级可能被改写。用 1.5KB 换整站样式错乱的风险，是负收益。

> **判断标准** — 压缩优化的收益必须相对于**总传输体积**评估。这个站 20MB 里视频占 18.7MB、图片 1.5MB、代码 0.06MB——在代码上再抠 2KB，用户感知为零。**把力气花在体积最大的那一项上，而不是最容易动的那一项。**

---

## 06 工程化与构建链

> 40 行脚本，换来的是一条"改源码 → 出产物"的确定路径

### 6.1 最终目录结构

```
cyberpunk-homepage/
├── index.html                 ← 构建产物（线上跑的就是它，64.5 KB）
├── src/
│   └── index.source.html      ← 可读源码（改内容改这里，77.6 KB）
└── assets/
    ├── bd-quickhack.mp4       4.13 MB
    ├── bd-cyberware.mp4       3.20 MB
    ├── bd-frontend.mp4        6.01 MB
    ├── bd-badlands.mp4        2.37 MB
    ├── bd-tower.mp4           2.14 MB
    ├── bd-afterlife.mp4       1.78 MB
    ├── portrait.jpg           209 KB
    ├── hero-city.jpg          915 KB
    ├── cyberware-arm.jpg      419 KB
    └── favicon.svg            242 B
```

### 6.2 构建命令

```bash
node minify-html.mjs src/index.source.html index.html

# 输出
# source : 77.6 KB
# output : 64.5 KB
# saved  : 16.9%
```

### 6.3 这个结构制造的新风险

> **必须记住的约定**
>
> 有源码和产物两份文件，就存&#x5728;**「改错了那份」**&#x7684;问题。真实发生过：直接改了 `index.html`（产物），此时若再从 `src/` 重新构建，改动会被**无声覆盖**——没有报错、没有提示，只是内容退回去了。

| 场景        | 正确做法                           | 错误做法                     |
| --------- | ------------------------------ | ------------------------ |
| 改文案 / 换视频 | 改 `src/index.source.html`，再跑构建 | 直接改 `index.html`（下次构建丢失） |
| 临时线上热修    | 改产物**并回写源码**，两份同步              | 只改产物，之后忘记同步              |
| 发布        | 确保产物是最新的，且与源码内容一致              | 改完源码没构建就发布（线上还是旧版）       |

更彻底的做法是引入 `npm run build` + 发布前校验产物哈希。但对一个单人维护的单页站，约定清楚"改源码、产物只读"就够了——**工程化的成本必须匹配协作规模**，一个人不需要 CI。

### 6.4 顺手补的 favicon

之前每次打开页面，控制台都有一条 `/favicon.ico 404`。这不是"关闭标签"的小事——浏览器会在每次导航时自动请求它，404 会出现在网络面板和性能瀑布图里，干扰后续排查真实问题。解法是加一个 242 字节的手写 SVG：黄底 + 黑 V，和站点的 logo 同源。

```html
<link rel="icon" href="assets/favicon.svg">


<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E...">
```

---

## 07 调试方法论

> "看起来不对"和"知道哪里不对"之间，差一套可编程的验证手段

### 7.1 用 CDP 读状态，而不是靠截图猜

无头浏览器 + Chrome DevTools Protocol，可以直接把页面内部状态读成结构化数据。截图只能回答"好不好看"，CDP 能回答"视频是不是真的在播、播到第几秒、有没有异常"。

```js
// CDP 三段式
const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });   // ← 必须先等连接建立

await send('Runtime.enable');      // 异常 / console
await send('Network.enable');      // 请求 / 失败原因
await send('Page.navigate', { url });

// 核心：在页面里求值，拿回 JSON
const state = await evalJS(`(()=>{const v=document.querySelector('#bd-player-mount video');
  return JSON.stringify({t:+v.currentTime.toFixed(1), paused:v.paused, dur:v.duration,
    readyState:v.readyState, error:v.error?.code ?? null});})()`);
```

| 监听事件                       | 能抓到什么                  | 典型用途            |
| -------------------------- | ---------------------- | --------------- |
| `Runtime.exceptionThrown`  | 未捕获异常 + 堆栈             | 发现空指针、脚本报错      |
| `Runtime.consoleAPICalled` | console 输出（含 iframe 内） | 第三方播放器为什么加载失败   |
| `Network.loadingFailed`    | 失败原因 + 是否被取消           | 区分"404"和"被策略拦截" |
| `Network.responseReceived` | 状态码 + URL              | 确认资源真的下发了       |
| `Runtime.evaluate`         | 任意 JS 求值结果             | 读状态、注入探针、模拟点击   |

> **一个必须知道的坑** — `new WebSocket()` 之后**立刻 `send()` 会丢消息**。必须等 `onopen`。第一版脚本没等，收到的全是空响应，误判成"页面什么都没加载"。

### 7.2 注入探针：验证事件到底有没有触发

"结束特效没出现"有两种可能：**事件没触发**，或者**触发了但动画没生效**。不区分这两者，就会一直在错误的层里改代码。办法是挂一个探针：

```js
// 在页面里挂监听，把触发记录到全局变量
evalJS(`(()=>{const v=document.querySelector('#bd-player-mount video');
  window.__ended = false;
  v.addEventListener('ended', () => { window.__ended = true; });
  return 'probe installed';})()`);

// 之后逐秒轮询
evalJS(`JSON.stringify({ev: window.__ended, t: v.currentTime,
  endingCls: document.getElementById('bd-player').classList.contains('ending')})`);
```

探针一挂，结论立即清晰：`__ended` 一直是 `false`，说明事件根本没触发，于是问题被定位到"视频没有真的播到结尾"，而不是"CSS 动画写错了"。

### 7.3 抓视频帧：不用截图，用 canvas

想确认"压缩后画质有没有下降"，需要看具体某一帧。用 CDP 的 `captureScreenshot` 在无头模式下抓 `<video>` 画面时**会挂起不返回**（合成层还没就绪）。改用页面内 canvas 直接读帧：

```js
const c = document.createElement('canvas');
c.width = v.videoWidth; c.height = v.videoHeight;
c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
const dataUrl = c.toDataURL('image/jpeg', 0.8);   // 直接拿 base64，写入文件即可
```

> **前提** — `drawImage` 要求视频**同源**，否则画布被"污染"（tainted），`toDataURL` 会抛 `SecurityError`。本地视频天然满足；这也是当初放弃第三方播放器的又一个理由——跨域资源连"验证画质"都做不到。

### 7.4 四个把时间耗光的环境陷阱

| 现象                          | 真实原因                                      | 正确做法                                       |
| --------------------------- | ----------------------------------------- | ------------------------------------------ |
| 服务器/浏览器莫名"消失"，测试连不上         | 沙箱里后台子进程会随命令结束被回收                         | 把**起服务、起浏览器、跑脚本、杀进程**写在同一条命令里              |
| 视频 seek 到结尾后又从 0 开始播        | `python3 -m http.server` **不支持 Range 请求** | 不要用它测 seek；要测"播完"就改 `playbackRate` 加速跑完全程  |
| CDP 连不上 `/json/list`        | Chrome 冷启动要 3~5 秒                         | 轮询 `/json/version` 直到 200，而不是 `sleep 4` 硬等 |
| `npm install` 报 `ENOTEMPTY` | 上次 kill 掉的进程留下了半写状态                       | 换一个全新的空目录安装，不要和残留的 `node_modules` 搏斗       |

> **Range 那个坑值得展开**
>
> HTTP `Range` 是"分段下载"能力，视频跳转（seek）依赖它。Python 的简易服务器对 `Range` 头直接忽略，返回整个文件并给 200 而不是 206。浏览器拿到的数据从第 0 字节开始，于是 `currentTime` 被重置回 0。表现就是"我明明跳到 59 秒了，怎么又从头发开始播"——**看起来像代码 bug，其实是测试服务器能力缺失**。真实托管环境支持 Range，不受影响。

---

## 08 部署与验证

> 发布成功 ≠ 用户能看到新版本

### 8.1 静态托管的形态

纯静态站点，托管侧只需要一条命令：`python3 -m http.server "$PORT" --bind 0.0.0.0`。没有构建步骤、没有依赖安装、没有环境变量。这也是"单文件 HTML"决策在第 4 天兑现的红利。

```
浏览器 ──HTTPS──▶ 反向代理（单端口） ──▶ 静态文件服务
                                          ├── index.html      (64.5 KB)
                                          └── assets/*        (18.7 MB 视频 + 1.5 MB 图片)
```

### 8.2 发布后必须验证的三件事

| 检查项      | 命令 / 方法                                                   | 能发现什么             |
| -------- | --------------------------------------------------------- | ----------------- |
| 首页可达     | `curl -o live.html -w "%{http_code} %{size_download}"`    | 站点是否真的在用新内容（比字节数） |
| 关键字符串在不在 | 在下载的 HTML 里搜新功能的特征串                                       | 线上是不是旧快照          |
| 每个资源可达   | 逐个 `curl -o /dev/null -w "%{http_code} %{size_download}"` | 视频/图片是否被漏传        |

最终的验证输出（10 个资源全部 200，字节数与本地一致）：

```
首页: http=200 size=66062          ← 与本地产物字节完全一致
200  213732B  /assets/portrait.jpg
200  937012B  /assets/hero-city.jpg
200  428893B  /assets/cyberware-arm.jpg
200     242B  /assets/favicon.svg
200 4125716B  /assets/bd-quickhack.mp4
200 3198420B  /assets/bd-cyberware.mp4
200 6014623B  /assets/bd-frontend.mp4
200 2366679B  /assets/bd-badlands.mp4
200 2135540B  /assets/bd-tower.mp4
200 1784304B  /assets/bd-afterlife.mp4
```

### 8.3 一次真实的"发布成功但线上是旧版"

中间出现过一次典型误判：多次修改都只在本地验证，线上链接一直是**首次发布时的快照**。症状是用户反馈"点视频打不开"，而在本地怎么测都正常。逐项对比后才发现线上那一版：

- 「接入回放」是 `onclick="return false"` 的**装饰性死链**，根本没有播放器代码；
- `assets/bd-*.mp4` 全部 **404**，视频文件从未上传；
- 标题、图片都还是第一天的旧版本。

> **教训** — **"本地通过"只能证明代码是对的，不能证明线上是新的。** 部署之后必须*回读线上内容*做一次断言——对比字节数、搜索特征字符串、逐资源查状态码。这次就是因为没有做这一步，让一个不存在的功能被当成"已上线"了六天。

---

## 09 踩坑清单

> 十二条，每条都真实发生过，附根因与修复

| #  | 现象                              | 根因                                                     | 修复                                                 |
| -- | ------------------------------- | ------------------------------------------------------ | -------------------------------------------------- |
| 1  | **双击打开，六个「接入回放」全点不动**           | `file://` 协议下浏览器禁止 `fetch`，`HEAD` 探测全部抛异常，被当成"文件不存在"锁死 | 三重放行：本地协议直接放行、异常放行、只有 404/410 才锁                   |
| 2  | **第三方播放器嵌进页面一片黑**               | 跨域 iframe 在嵌入环境下的初始化失败，且外部完全看不到内部状态                    | 放弃 iframe，视频落本地改原生 `<video>`                       |
| 3  | **结束特效提前触发 / 不触发**              | 用硬编码时长推算"播完"，用户暂停或缓冲时时序全错                              | 改监听真实 `ended` 事件                                   |
| 4  | **关闭播放器后控制台报 `TypeError`**      | 已排队的 `timeupdate` 回调在 `vid = null` 之后执行                | 回调首行加 `if(!vid) return` 守卫                         |
| 5  | **带声音的自动播放被浏览器拒绝**              | `play()` 不在用户手势的调用栈内，`user activation` 已失效             | 在 click 处理器内同步调用，并 `.catch()` 兜住 `NotAllowedError` |
| 6  | **iOS 上视频劫持全屏**                 | 未声明 `playsinline`，WebKit 默认全屏播放                        | 同时写 `playsinline` 属性与 `webkit-playsinline`         |
| 7  | **服务端有文件却判定"没有"**               | 部分静态服务器对 `HEAD` 返回 405                                 | 判定改为黑名单（只认 404/410），而不是白名单（只认 200）                 |
| 8  | **跳到结尾后又从头播**                   | `python -m http.server` 不支持 `Range`，`currentTime` 被重置  | 测试改用 `playbackRate` 加速，不用 seek                     |
| 9  | **首图视差到边角露出白边**                 | 位移量超过了图片的冗余尺寸                                          | 容器加 `scale(1.06)` 做 overscan，覆盖率始终 > 位移量           |
| 10 | **数字滚动在上下滑动时反复重播**              | `IntersectionObserver` 未 `unobserve`，进出视口都触发           | 触发后 `io.unobserve(target)`，只跑一次                    |
| 11 | **`npm install` 报 `ENOTEMPTY`** | 中断的进程留下半写的 `node_modules`                              | 换全新空目录安装，不在残留目录里修                                  |
| 12 | **改了内容，线上还是旧的**                 | "发布成功"被当成"内容生效"，从未回读验证                                 | 部署后 curl 首页 + 特征串 + 逐资源状态码做断言                      |

### 一条贯穿始终的规律

十二条里有七条属于同一类：**「我以为的状态」和「真实的状态」不一致**。iframe 里在播什么、`ended` 有没有触发、线上跑的是哪一版、`file://` 下 fetch 能不能用——全部是"看不到内部"造成的误判。对应的解法也高度一致：*把不可观测的东西变成可观测的*（探针、CDP 求值、回读线上内容）。

---

## 10 可复用要点

> 下次做类似项目，直接抄这份清单

### 媒体播放器

- 能用原生 `<video>` 就别嵌第三方播放器：状态可读、UI 可控、体积更小
- 判断"播完"只用 `ended`，永远不要用时长推算
- `play()` 必须在用户手势的同步调用栈内，且返回 Promise 要 `.catch`
- 移动端必写 `playsinline` + `webkit-playsinline`
- 关闭时 `innerHTML=''` 移除元素，而不是 `pause()` 后留着
- 所有异步回调开头加空值守卫

### 渐进增强与探测

- 资源存在性探测用**黑名单**（只排 404/410），不要用白名单（只认 200）
- `file://` 下 `fetch` 不可用，本地调试路径要单独放行
- 任何"依赖网络探测才能启用"的功能，都要有探测失败时的兜底策略

### CSS 动效

- 数字故障用 `steps(1)`，加缓动就变成廉价抖动
- 故障要稀缺：大部分时间静止，只在 1~2 帧里爆发
- 两个不同周期叠加，节奏才不重复
- 全屏特效层必加 `pointer-events: none`
- 位移动画要出界（`-15%` → `110%`），否则边缘会"凭空出现"
- 塌缩类动画锚点在底：`transform-origin: bottom` + `scaleY → 0`
- 压缩时同步提亮（`brightness` 反向上升），暗示"能量被挤压"
- 视差图必须 overscan（`scale > 1`）覆盖位移量

### 性能

- 照片用 JPEG，PNG 只留给图标和需要透明的图
- 先限分辨率（`-Z` / `scale`），再谈压缩质量
- H.264 + `yuv420p` + `+faststart` 是浏览器兼容的稳妥组合
- CRF 22 是"视觉无损"的保守值；压缩率取决于素材复杂度，不取决于参数
- 力气花在体积最大的那一项上

### 工程与验证

- 源码与产物分离，并明确"改哪份"的约定
- 无头浏览器 + CDP 读取页面状态，比截图更有信息量
- 关键交互挂探针（`window.__ended`），区分"没触发"和"触发了但没生效"
- 部署后**回读线上内容**做断言：字节数、特征串、逐资源状态码
- 全屏遮罩必须有超时逃生路径，`finish()` 必须幂等

---

> **最后一句**
>
> 这个项目里最难的不是"做出赛博朋克的感觉"——那只是审美和 CSS 的堆叠，调参数就行。真正花时间的是**让不可见的系统变得可见**：视频到底播没播、事件到底触没触发、线上到底是哪一版。视觉是门面，可观测性才是能交付的底气。

---

*NIGHT CITY PERSONAL TERMINAL · TECH RETROSPECTIVE · 2026.10.09 — 10.18*  
*1359 行源码 · 6 段超梦 · 20.4 MiB*  
线上站点：<https://cyberpunk-terminal.app.workbuddy.host/>
