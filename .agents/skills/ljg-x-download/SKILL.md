---
name: ljg-x-download
description: "Download requested image/video files from X posts into the user's output directory (default ~/Downloads). Use only when X media acquisition is intended; saving tweet/article text as Markdown belongs to baoyu-danger-x-to-markdown."
version: "1.1.0"
user_invocable: true
---

# ljg-x-download

从 X (Twitter) 链接下载图片或视频到 ~/Downloads。

## 与文本归档的分工

本入口以图片/视频文件为产物；推文或长文章的正文归档交给 [baoyu-danger-x-to-markdown](../baoyu-danger-x-to-markdown/SKILL.md)。只有用户同时要文字和媒体时才串联，两个入口分别报告自己的产物。

## 依赖

- 宿主可调用的 `yt-dlp` 实际命令；这不是对已弃用 `yt-dlp-media` 技能的依赖。先确认工具可用，不把旧条目的“已安装”当作当前事实。

## 执行流程

### 1. 解析输入

从用户输入中提取 X/Twitter URL。支持的格式：
- `https://x.com/user/status/123456`
- `https://twitter.com/user/status/123456`
- `https://mobile.twitter.com/user/status/123456`
- 带查询参数的 URL（yt-dlp 自动处理 `?s=20` 等追踪参数）

缩短链接（t.co）先解析：`curl -Ls -o /dev/null -w '%{url_effective}' "SHORT_URL"`

如果用户没有提供 URL，用 AskUserQuestion 要求提供。

### 2. 尝试直接下载（视频优先）

直接用 yt-dlp 下载，无需先探测：

```bash
yt-dlp -o "~/Downloads/%(uploader)s_%(id)s.%(ext)s" "URL"
```

如果成功（视频推文），完成。跳到步骤 4 汇报结果。

### 3. 视频下载失败时，提取图片

yt-dlp 对纯图片推文可能报错。此时用 `--dump-json` 提取图片 URL：

```bash
yt-dlp --dump-json "URL" 2>&1
```

**判断结果：**
- JSON 中有 `thumbnails` 数组 → 提取图片 URL
- JSON 为空或报错 `no video` → 只能说明未取得视频/媒体数据，不能据此断言没有图片；用已可用的原帖读取工具核对媒体，或明确报告尚未确认。
- 报错含 `login` / `authentication` → 需要登录（见故障排除）
- 其他错误 → 报告具体错误信息

**图片下载：**

从 JSON 的 `thumbnails` 数组提取所有图片 URL，替换 `name=small` 或 `name=medium` 为 `name=orig` 获取原图，然后逐一下载：

```bash
curl -L -o ~/Downloads/tweet_ID_1.jpg "https://pbs.twimg.com/media/xxx?format=jpg&name=orig"
curl -L -o ~/Downloads/tweet_ID_2.jpg "https://pbs.twimg.com/media/yyy?format=jpg&name=orig"
```

文件扩展名跟随 URL 中的 `format` 参数（jpg/png/webp）。

### 4. 汇报结果

下载完成后，用 `ls -lh` 列出已下载的文件：文件名、大小、路径。

## 故障排除

### 需要登录

yt-dlp 报错含 `login` / `Sign in` / `age-restricted` 时，加 `--cookies-from-browser chrome`：

```bash
yt-dlp --cookies-from-browser chrome -o "~/Downloads/%(uploader)s_%(id)s.%(ext)s" "URL"
```

### 推文无媒体

纯文字推文没有可下载的媒体。告知用户即可。
