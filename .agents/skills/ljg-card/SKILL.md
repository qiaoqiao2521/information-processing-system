---
name: ljg-card
description: "LJG 内容铸造原子：把已提供或已整理的内容转成 PNG 长图、信息图、多卡、视觉笔记或漫画。用于铸、阅读卡、信息图和视觉成稿请求；论文精读加卡片用 ljg-paper-flow，解词加卡片用 ljg-word-flow。"
user_invocable: true
version: "1.6.0"
---

# ljg-card: 铸

将内容铸成可见的形态。内容进去，PNG 出来。模具决定形状。

## 入口分工

本技能只定义视觉模具、品味和 PNG 交付。流程技能先完成解读/解词，再把已生成内容交给这里；不在成图阶段重跑研究或重新发明上游文本方法。

## 参数

| 参数 | 模具 | 尺寸 | 说明 |
|------|------|------|------|
| `-l`（默认） | 长图 | 1080 x auto | 单张阅读卡，内容自动撑高 |
| `-i` | 信息图 | 1080 x auto | 内容驱动的自适应视觉布局 |
| `-m` | 多卡 | 1080 x 1440 | 自动切分为多张阅读卡片 |
| `-v` | 视觉笔记 | 1080 x auto | 手绘风格 sketchnote，动态选择风格路线 |
| `-c` | 漫画 | 1080 x auto | 日式黑白漫画风格，动态选择漫画家视觉语言 |

## 约束

本 skill 输出为视觉文件（PNG），不适用 L0 中的 Org-mode、Denote 和 ASCII-only 规范。

## 共享基础

### 获取内容

- URL --> WebFetch 获取
- 粘贴文本 --> 直接使用
- 文件路径 --> Read 获取

### 文件命名

从内容提取标题或核心思想作为 `{name}`（中文直接用，去标点，≤ 20 字符）。

### 截图工具

```bash
node "$CARD_SKILL_DIR/assets/capture.js" <html> <png> <width> <height> [fullpage]
```

`CARD_SKILL_DIR` 指包含本文件的实际技能目录。依赖该目录运行时可用的 Playwright；先区分缺依赖和渲染错误，只有实际需要配置依赖时才使用下列命令：

```bash
cd "$CARD_SKILL_DIR" && npm install playwright && npx playwright install chromium
```

### arxiv 检测

内容来源为 arxiv 论文时（URL 含 `arxiv.org`、文件名含 `paper` 标签、或内容中出现 arxiv ID），提取 arxiv ID（格式 `XXXX.XXXXX`），在卡片 footer 右侧显示。适用于 `-l` 和 `-i` 模具（`-m` 多卡无 footer，不适用）。

### 交付

1. 报告文件路径

## 品味准则

**所有模具共享**。`references/taste.md` 是唯一的完整品味定义；选定模具后读取一次，并贯穿该次成图流程。

核心：反 AI 生成痕迹——禁 Inter 字体、禁纯黑、禁三等分卡片、禁居中 Hero、禁 AI 文案腔、禁假数据。

## 执行

根据参数只读取所选模具的 mode 文件，并结合本次已读的 `references/taste.md` 执行；不用加载其他四种模具：

### -l（默认）：长图

Read `references/mode-long.md`，按其步骤执行。

模板：`assets/long_template.html`

### -i：信息图

Read `references/mode-infograph.md`，按其步骤执行。

模板：`assets/infograph_template.html`

### -m：多卡

Read `references/mode-poster.md`，按其步骤执行。

模板：`assets/poster_template.html`

### -v：视觉笔记

Read `references/mode-sketchnote.md`，按其步骤执行。

模板：`assets/sketchnote_template.html`

### -c：漫画

Read `references/mode-comic.md`，按其步骤执行。

模板：`assets/comic_template.html`
