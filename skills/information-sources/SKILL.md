---
name: information-sources
description: Use when the user asks about 信息来源, source routing, source priority, source of truth, latest/current verification, source attribution, cite sources, what is your source, official source, primary source, which source should I trust, 可靠来源, 用什么工具找资料, 先用哪个工具, fallback 顺序, 失败后换什么工具, 读网页正文, 读链接, 读推文, 读 PDF, 读图片, 读 RSS, 读 RSS 失败怎么办, 看 GitHub 仓库, 读 GitHub README, 提取视频信息, or when deciding between Jina Reader, gh, yt-dlp, mcporter, and feedparser.
---

# Information Sources

Use this skill to choose the right source and tool before gathering information.

Think in two layers:

1. Pick the source of truth
2. Pick the access path to that source

Do not collapse these into one decision.

## First Response Shape

When this skill is used, prefer answering in this order:

1. `Source of truth: ...`
2. `Preferred tool: ...`
3. `Fallback: ...`
4. `Freshness note: ...` only when the user asks for latest/current/recent information

Keep this first response short and operational.
Lead with the routing decision before extra explanation.

## First Response Examples

Use these as the default shape when the user mainly needs routing.

### GitHub repo metadata

- Source of truth: GitHub repository metadata
- Preferred tool: `gh`
- Fallback: Direct GitHub API or public repository page reading

### GitHub README body

- Source of truth: GitHub README
- Preferred tool: `gh` first
- Fallback: Direct GitHub API or raw README retrieval if `gh` is unavailable

### RSS feed parsing

- Source of truth: Feed URL
- Preferred tool: `feedparser`
- Fallback: Direct feed URL check or page fetch after `feedparser` fails

### Generic page-shaped reading

- Source of truth: Original page or document
- Preferred tool: Source-specific official tool or direct original retrieval
- Fallback: Approved Firecrawl sources within the existing budget; otherwise report unavailable content

### Latest or current status ask

- Source of truth: Live upstream source
- Preferred tool: source-specific official tool first
- Fallback: Direct page reading, then broad search only if the direct source path is blocked
- Freshness note: verify live; do not answer from memory alone

## Project scope

PROJECT.md owns collection budgets and paused sources. Tool availability does not override those limits.
The routes below apply to this repository; check installed tools before choosing them.

## Core reminders

- Source and tool are not the same thing. The platform or original document is the source of truth; the CLI or reader is only the access path.
- Prefer the most direct, structured, and official path first. Generic readers are fallback infrastructure, not the first answer to everything.
- If a platform already has a purpose-built tool in this environment, use that tool before scraping or broad search.
- For latest or current information, verify from the live upstream source instead of relying on summaries or memory.
- If the preferred tool is unavailable, fall through to the next-best access path without changing what counts as the source of truth.

## Default source priority

1. Direct primary source
2. Official tool for that source
3. Local configured MCP or parser
4. Approved Firecrawl source retrieval within its existing budget
5. Search results or summaries only as fallback

Do not use `agent-reach` as a source layer. Treat it only as an old wrapper that is no longer part of the workflow.

## Preferred tools in this environment

- `gh`: GitHub repos, releases, issues, PRs, stars, metadata
- `yt-dlp`: YouTube and other video-page metadata, subtitles, transcripts, media info
- `mcporter`: configured MCP servers and MCP-backed sources
- `feedparser`: RSS and Atom feeds
- `Jina Reader`: existing X post bodies only, through the budgeted reader; not generic web/PDF/image reading

## Failure Recovery Order

When the preferred tool fails, keep the same source of truth and fall back in a fixed order.

- `gh` failed:
  keep GitHub as source of truth, then use the official API or direct raw README; report missing content if unavailable.
- `mcporter` failed or MCP is not configured:
  only use `mcporter` when the MCP server is actually configured; if MCP is not configured, skip `mcporter` immediately and fall through to the next direct source path.
- `yt-dlp` failed:
  keep the video page as source of truth, then use available official subtitles or direct public page reading; preserve missing transcript/timestamp gaps.
- `feedparser` failed:
  keep the feed as source of truth, then fall back to direct feed URL checks or page fetch only after `feedparser` fails, and do not start from generic broad search.
- `Jina Reader` failed:
  keep the X original post as source of truth; preserve the existing summary and report the gap. Do not bypass account-risk cooldown or the 50 attempts/24h budget.

Do not change the authority layer just because the first access path broke.

## Fast route first

| User intent | Source of truth | Preferred tool | Notes |
| --- | --- | --- | --- |
| 看 GitHub 仓库信息 | GitHub repo metadata | `gh` | Metadata, releases, issues, stars all use `gh` first |
| 读 GitHub README 正文 | GitHub README | `gh` first, official API/raw fallback | Keep GitHub as source of truth |
| 提取视频字幕/元数据 | Video platform page | `yt-dlp` | Better than generic scraping |
| 读 RSS/Atom | Feed itself | `feedparser` | Do not scrape feed HTML first |
| 调 MCP 已配置源 | MCP-backed source | `mcporter` | Only when server is actually configured |
| 读普通网页/PDF/图片 | Original page/document | official/direct retrieval + document extractor | Preserve original body and verified positions |
| 读既有 X 正文 | Original post | budgeted `Jina Reader` | No new X/Google search; 50 attempts/24h |
| 问 latest/current/recent | Live upstream source | source-specific tool first | Never rely on memory or stale summaries |

## Source selection rules

### 1. GitHub content

Prefer `gh` first for:

- repository metadata
- releases and tags
- issues and pull requests
- stars and watchers
- authenticated access
- README body retrieval when possible

Use the official API or raw content for GitHub fallback. Jina Reader is outside this route.

Practical split:

- Repo metadata / release / issue / PR / stars -> `gh`
- README or page body when `gh` is unavailable -> official API or direct raw content
- Even on fallback, GitHub remains the source of truth

### 2. Video pages

Prefer `yt-dlp` first for:

- subtitles
- transcript-like text
- title, uploader, duration, upload date
- multi-site media extraction

Read surrounding public articles directly. Verify that `yt-dlp` is installed before selecting it; preserve unavailable metadata and subtitle gaps.

### 3. RSS and Atom

Prefer `feedparser` first.

Use it for:

- parsing feed entries
- timestamps
- titles and links
- structured feed consumption

Do not send RSS failures to Jina Reader. Preserve the feed URL and failure reason.

### 4. MCP-backed sources

Prefer `mcporter` when the target source has a configured MCP server.

Typical examples:

- Exa search through MCP
- platform-specific MCP integrations
- structured tool calls where the MCP exposes the canonical action

Before using `mcporter`, check whether the server is locally configured.
If it is not configured, do not stall there; fall through to the next direct source path.
Do not treat "MCP might exist" as enough reason to pause routing; configured and callable is the bar.

### 5. Web pages, tweets, PDFs, images

Use the official source tool or direct original retrieval for public pages.
Use PDF/image extractors for attachments. Preserve OCR uncertainty and selected pages.
Approved Firecrawl sources may use the existing 60 attempts/24h budget, two documents per source per round.
Unapproved sources need a routing decision; do not silently expand the allowlist.

Jina Reader is limited to existing X post bodies: 50 attempts/24h, 1/min, 10/h.
Use the existing budgeted X reader. Raw curl and the legacy preprocessor must not bypass this budget.
X/Google searches remain paused; honor account-risk cooldowns and stop on verification prompts.
Do not substitute a summary, abstract, raw PDF bytes or failed fetch for verified full text.

## Evidence and report handoff

Reuse the existing `claims/documents/provenance` packet, not a second source ledger.
Read [references/evidence-report-contract.md](references/evidence-report-contract.md) for source hashes,
article and original positions, verified page/time maps, structured report records and gap reporting.
Missing owner/date stays unknown; extraction does not create external tasks.

## Latest and current rule

If the request includes words like:

- latest
- current
- today
- recent
- 最新
- 现在
- 今天

then treat freshness as a hard requirement.

That means:

1. Verify against the live upstream source
2. Prefer structured official tooling over summaries
3. Mention when you are falling back
4. Do not answer from memory alone

## What to avoid

- Do not use a generic web reader first when a structured official tool already exists.
- Do not treat `Jina Reader` output as the source of truth for GitHub metadata, video metadata, or feed parsing.
- Do not scrape RSS with a generic web reader when `feedparser` can parse the feed directly.
- Do not use `agent-reach` as a source layer. It is not part of the current source-selection workflow.
- Do not mistake access convenience for authority. A readable page is not automatically the canonical source.

## Decision matrix

Read [references/source-matrix.md](references/source-matrix.md) when you need the task-to-tool mapping in compact form.
Read [references/fallback-matrix.md](references/fallback-matrix.md) when the preferred tool failed and you need the next access path in table form.

## Operating rules

- Prefer the most direct source over a derived summary.
- If the user asks for the latest or current status, verify with the live source, not memory.
- If a primary source is available, do not lead with secondary commentary.
- If the requested page is easy to read directly, use the direct reader instead of broad search.
- When multiple tools could work, choose the one that yields the most structured, authoritative output.
- If the user only wants fast page正文 and not structured metadata, prefer the shortest reliable path.

## Fast choices

- "看这个 GitHub 仓库" -> `gh`
- "读这个 GitHub README" -> `gh` first, official API/raw fallback
- "提取这个视频字幕" -> `yt-dlp`
- "读这个 RSS" -> `feedparser`
- "调用已配置的 MCP 源" -> `mcporter`
- "读这个网页/PDF/图片" -> official/direct retrieval; existing X body -> budgeted `Jina Reader`
- "看最新/最近/今天的情况" -> live upstream source first, not memory
