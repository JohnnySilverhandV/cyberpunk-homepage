<div align="center">

<img src="assets/hero-city.jpg" alt="NIGHT CITY / 夜之城" width="100%">

<br>

# 瑞哥 . 夜之城个人终端

**NIGHT CITY PERSONAL TERMINAL**

单文件 HTML · 零框架 · 零运行时依赖 · 6 段超梦回放 · 20 MiB

<sub>WAKE UP, SAMURAI. 我们有一座城市要烧。</sub>

<br>

[线上终端](https://cyberpunk-terminal.app.workbuddy.host/) ｜ [GitHub](https://github.com/JohnnySilverhandV/cyberpunk-homepage) ｜ [Gitee](https://gitee.com/johnny-silver-hand123/cyberpunk-homepage)

</div>

---

## 这是什么

一个赛博朋克 2077 风格的个人主页：进门先过一遍神经链路自检，然后是义体清单、专长树、超梦档案、语录墙，最后落在一个能用键盘敲命令的终端上。

页面不是"套模板加霓虹"，而是把 CP2077 的界面语言拆成可复用的部件：RGB 色差故障字、CRT 扫描带、会跳动的胶片噪点、鼠标视差首图、全息投影播放器。全部手写，没有一张 UI 贴图。

| 入口 | 地址 |
|---|---|
| 线上终端 | https://cyberpunk-terminal.app.workbuddy.host/ |
| GitHub | https://github.com/JohnnySilverhandV/cyberpunk-homepage |
| Gitee（国内镜像） | https://gitee.com/johnny-silver-hand123/cyberpunk-homepage |

## 七个区块

| 区块 | 锚点 | 内容 |
|---|---|---|
| 首屏 | `#hero` | 视差城市首图、打字机自述、代号与状态条 |
| 属性 | `#attributes` | 六维能力条，进入视口才填充、数字才滚动 |
| 义体 | `#cyberware` | 义体清单 + 改造等级 |
| 专长 | `#perks` | 专长树，悬停触发色差抖动 |
| 超梦档案 | `#braindance` | 六篇档案，每篇带一段「接入回放」全息视频 |
| 语录 | `#quotes` | 城市语录墙 |
| 终端 | `#terminal` | 可输入命令的假终端：`help` / `whoami` / `contact` / `clear`，以及彩蛋 `burn` |

## 交互细节

- **开机自检**：`WAKE UP, 瑞哥_` 逐行点亮，三种出口（走完 / 点击跳过 / 3.4s 兜底），`finish()` 幂等
- **超梦回放**：点击「接入回放」弹出全息投影，原生 `<video>` 自动播放，播完触发 1.5 秒「结束投影」——幕布纵向塌缩成一条光带、亮度反向飙升、`SIGNAL LOST`，随后自动断开
- **打字机**：打字随机 55~115ms、删除固定 22ms、打完停 2.4s，节奏不均匀才像人
- **滚动驱动**：IntersectionObserver 双阈值（显现 .15 / 计数 .5），触发后 `unobserve`，不重播
- **跑马灯**：内容复制一份，位移恰好 `-50%`，无缝且与字体加载无关
- **终端彩蛋**：`burn` 让全站进入 4 秒烧城状态（切一个 body class，不改布局）

## 目录结构

```
cyberpunk-homepage/            ← 仓库根 = 站点根
├── README.md
├── LICENSE
├── index.html                 # 构建产物（线上跑的就是它，约 66 KB）
├── src/
│   └── index.source.html      # 可读源码（1359 行，改这里）
└── assets/
    ├── bd-quickhack.mp4   # 4.1 MB  快速黑客
    ├── bd-cyberware.mp4   # 3.1 MB  义体改造
    ├── bd-frontend.mp4    # 6.0 MB  前端工程
    ├── bd-badlands.mp4    # 3.1 MB  恶土见闻
    ├── bd-tower.mp4       # 2.1 MB  高塔晚风
    ├── bd-afterlife.mp4   # 2.1 MB  来世酒吧
    ├── hero-city.jpg      # 915 KB  视差首图
    ├── portrait.jpg       # 209 KB  肖像
    ├── cyberware-arm.jpg  # 419 KB  义体
    └── favicon.svg        # 242 B
```

> **改哪一份**：改文案、换视频请改 `src/index.source.html`，再跑构建生成 `index.html`。
> 直接改 `index.html` 也能立刻见效，但下次从源码构建时会被无声覆盖。

## 快速开始

零依赖，不需要 `npm install`：

```bash
# 方式一：直接双击 index.html（file:// 下视频探测会自动放行）
open index.html

# 方式二：起个静态服务（推荐，更接近线上）
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000
```

> 本地用 `python3 -m http.server` 时**不要用它测视频 seek**：该服务器不支持 Range 请求，跳转会从头开始播。要验证「播完特效」，把 `playbackRate` 调到 8 倍跑完全程。

## 构建

源码 1359 行、产物压缩后体积约 −17%。构建依赖 `html-minifier-terser` 与 `clean-css`（CSS 只走 level 1，level 2 会重排规则顺序、有层叠错乱风险）：

```bash
npx html-minifier-terser \
  --collapse-whitespace --remove-comments \
  --minify-css true --minify-js true \
  --remove-attribute-quotes --remove-redundant-attributes \
  src/index.source.html -o index.html
```

## 性能账本

| 项目 | 之前 | 之后 | 降幅 |
|---|---|---|---|
| 六段超梦视频 | 90.0 MiB | 18.7 MiB | **−79.2%** |
| 三张图片 | 9.3 MB | 1.5 MB | −84% |
| HTML | 77.6 KB | 64.5 KB | −16.9% |
| 全站 | ~99 MiB | **20 MiB** | −80% |

视频占总体积 95%，所以优化火力全押在这里：H.264 `-crf 22 -preset medium -pix_fmt yuv420p -movflags +faststart`，1080p 先降到 720p；图片一律 PNG→JPEG 并先限最长边（`sips -Z`），比继续降质量省得多。**压缩率取决于素材复杂度，不取决于参数。**

## 技术要点速览

| 问题 | 做法 |
|---|---|
| 数字故障字 | 两个伪元素青/红双通道 + `clip-path: inset()` 切片，`steps(1)` 跳变，0%~88% 完全静止 |
| 结束投影 | `transform-origin: bottom` + `scaleY → 0`，同时 `brightness` 反向飙升到 6.5，`cubic-bezier(.5,0,.75,0)` |
| 自动播放被拒 | `play()` 必须在 click 的同步调用栈内，返回的 Promise 要 `.catch()` |
| 判断播完 | 只信 `ended` 事件，绝不用时长推算；关闭时 `innerHTML=''` 释放解码器，回调首行 `if(!vid) return` |
| 视频探测 | 黑名单而非白名单：只有 404/410 才锁住「接入回放」，405/异常/`file:` 一律放行 |
| 视差首图 | `scale(1.06)` 做 overscan，覆盖率必须大于最大位移，否则边角露白 |

## 版本记录

### v1.0.0 — 2026-11-04

首个版本，双远端（GitHub + Gitee）同步发布。

- 单文件赛博朋克主页：七个区块、开机自检、打字机、滚动驱动、无缝跑马灯、终端命令彩蛋
- 六段超梦回放：原生 `<video>` + 自绘 HUD，真实 `ended` 驱动结束投影特效
- 媒体压缩：全站 99 MiB → 20 MiB（视频 −79.2%）
- 源码/产物分离 + 构建脚本，线上产物与仓库字节一致

## 声明

个人主页项目，与 CD PROJEKT RED 无关；《赛博朋克 2077》相关名词仅作致敬。页面无第三方运行时依赖，不含统计脚本。
