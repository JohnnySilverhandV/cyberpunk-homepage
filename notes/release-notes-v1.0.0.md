## 瑞哥 . 夜之城个人终端 — v1.0.0

首个正式版本。单文件 HTML，零框架、零运行时依赖，双远端（GitHub + Gitee）同步发布。

**线上终端**：https://cyberpunk-terminal.app.workbuddy.host/

### 本次内容

- **七个区块**：首屏 / 属性 / 义体 / 专长 / 超梦档案 / 语录 / 终端
- **开机自检序列**：`WAKE UP, 瑞哥_` 逐行点亮，三个出口（走完、点击跳过、3.4s 兜底），`finish()` 幂等
- **六段超梦回放**：原生 `<video>` + 自绘 HUD，点击「接入回放」弹出全息投影，播完触发 1.5 秒结束投影（幕布 `scaleY → 0` 纵向塌缩 + 亮度反向飙升 + `SIGNAL LOST`）
- **视觉系统**：RGB 色差故障字（双伪元素 + `clip-path` + `steps(1)`）、CRT 扫描带、跳动胶片噪点、鼠标视差首图（`scale(1.06)` overscan）
- **交互层**：打字机、IntersectionObserver 双阈值滚动驱动、无缝跑马灯、终端命令与 `burn` 烧城彩蛋
- **工程**：源码/产物分离（`src/index.source.html` → `index.html`），`release.py` 一键发版

### 媒体压缩

| 项目 | 之前 | 之后 | 降幅 |
|---|---|---|---|
| 六段视频 | 90.0 MiB | 18.7 MiB | −79.2% |
| 三张图片 | 9.3 MB | 1.5 MB | −84% |
| HTML | 77.6 KB | 64.5 KB | −16.9% |

### 下载后怎么用

```bash
unzip cyberpunk-terminal-v1.0.0.zip
cd cyberpunk-homepage
python3 -m http.server 8000   # 或直接双击 index.html
```

### 技术复盘

完整 10 章复盘：`notes/cyberpunk-homepage-tech-notes.md`（HTML 排版版同名 `.html`）。

---

个人主页项目，与 CD PROJEKT RED 无关。
