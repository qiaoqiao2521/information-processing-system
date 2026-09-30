---
name: ai-influence-digest
description: 生成「AI影响力信息汇总」周报：在不使用 X API 的前提下，用 Google 搜索批量扫描指定 X 账号过去7天推文（偏工具/工作流/教程/Prompt），过滤出对内容创作者立刻可用的高价值内容，产出结构化中文周报 Markdown。当你需要做每周 AI Builder 账号扫描、实用推文精选、工作流/方法论周报时使用。
---

# AI影响力信息汇总（AI Influence Digest）

目标：把“刷一周 X”变成可复用的内容雷达流水线，自动采集公开候选，再按需产出可编辑、可分发的 Markdown 周报。

约束（强制）：
- **绝对禁止使用 X API**（包括任何 X API 搜索/时间线拉取）。
- 允许：Google 浏览器自动化（Playwright，复用已确认的 Chrome）+ Jina Reader + 本地整理；不使用 opencli。

## 来源与产物边界

- 本入口扫描 `references/accounts_65.txt` 或用户指定的 X 账号，产物是实用方法周报；搜索索引可见结果不等于账号完整时间线。
- [follow-builders](../follow-builders/SKILL.md) 使用中央 builder feeds；[ak-rss-digest](../ak-rss-digest/SKILL.md) 筛选 OPML 文章。不要因为主题相同就叠加执行它们。
- 同一条推文只保留一个原始 URL；候选分数服务于初筛，最终价值判断仍使用本技能的创作者标准。

## 快速流程（推荐）

### 0) 准备账号清单
- 默认账号列表：`references/accounts_65.txt`
- 可以按需删减/追加（每行一个 handle，不带 @）。

### 1) 扫描候选推文（收集阶段）
使用脚本抓“过去 N 天”候选推文（只拿 URL + 公开网页文本，不走 X API）。

```bash
python3 scripts/scan_x_weekly.py \
  --accounts references/accounts_65.txt \
  --days 7 \
  --batch-size 8 \
  --per-search 8 \
  --outdir ./output/ai-influence-digest
```

输出：
- `candidates.json`：候选列表（url/handle/text/content_status），未经过 AI 评分
- `candidates.md`：便于快速人工扫读
- `x_google_sources_latest.json`：网站原始候选，附搜索覆盖、原帖时间、采集时间和正文状态

2026-09-30 用户修正：X 退出默认定时采集。显式按需采集也须通过 Ops 账号风控门禁；验证提示后至少冷却 24 小时且人工确认恢复，到期不自动重试。已有候选可继续阅读、按需整理周报。

> 如果遇到搜索源封锁/挑战，先记录缺口；可在原授权范围内降低批量，或用宿主已可用的浏览器工具分批搜索。不要为此恢复已弃用的 agent-reach 技能。

### 2) 按标准筛选 5-10 条高价值内容（编辑阶段）
筛选规则见：`references/filters.md`

产出要求（每条 150-200 字，必须含 Why it’s useful + 推文链接）：

- 标题用中文强调“实用价值”
- 结构固定：
  - Title
  - Account
  - Type（🛠️ 可复用方法｜💡 工作流优化｜📝 小技巧｜🚀 新工具）
  - Core Methods/Techniques：3 条可执行项
  - Why it’s useful：1-2 句解释“为什么内容创作者立刻能用”
  - Tweet Link：必须是原始推文 URL

### 3) 输出最终周报 Markdown（发布物阶段）
把最终周报整理为单个 Markdown 文件，供后续分发、改写、排版或接入你自己的发布流程。

```bash
cat ./output/ai-influence-digest/weekly_report.md
```

建议最终稿保存为：
- `./output/ai-influence-digest/weekly_report.md`

明确非目标：
- 本 skill 只负责候选收集、筛选和 Markdown 周报整理
- 本 skill 不内置 Telegram / 知识星球 / Notion 发布适配
- 若需要发布物渲染，交给外部独立流程处理，不耦合在此 skill 内

## 常见坑
- Google 搜索结果可能混入非目标账号/聚合帖：只保留 `https://x.com/<handle>/status/<id>`。
- r.jina.ai 抓取会带 UI 噪音：脚本已做基础提取；如文本异常，回退到手动读原帖。
- 自动采集按真实发帖时间排序；工具/教程偏好留给按需编辑阶段，不将搜索摘要当作 AI 筛选结果。
- 依赖 `web/requirements-maintenance.txt` 中的 Playwright，浏览器 CDP 默认为 `http://127.0.0.1:9222`，可通过 `HUB_BROWSER_CDP_URL` 指向 SSH 本地转发。只创建并关闭自己的匿名上下文，不读取 Cookie、不关闭共享浏览器。
- 436 匿名 Jina 请求返回 401；用户选择先显示搜索摘要。配置 `JINA_API_KEY` 后才补读正文；未取得正文不得称为正文。
- 无有效近七天候选、全失败或 Google 验证挑战时退出，保留旧快照和日期；不绕过挑战。

## 资源
- `scripts/scan_x_weekly.py`：批量收集候选推文（Google 搜索 + 公开抓取）
- `references/accounts_65.txt`：默认账号清单（当前 64 个唯一账号）
- `references/filters.md`：筛选标准（内容创作者视角）
