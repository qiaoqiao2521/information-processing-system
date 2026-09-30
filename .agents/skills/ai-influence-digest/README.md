# AI影响力信息汇总（ai-influence-digest）

把「刷一周 X」变成可复用的内容雷达流水线：
- 批量扫描指定 X 账号过去 7 天推文（工具/工作流/教程/Prompt）
- 过滤出对内容创作者“立刻可用”的高价值内容
- 产出结构化中文周报 Markdown
- 只保留 Markdown 工作流，后续排版/发布交给外部流程

## ✅ 前提与约束（强制）
- **绝对禁止使用 X API**（包括任何 X API 搜索/时间线拉取）。
- 只允许走“公开网页”路径：
  - Google 搜索：Playwright 复用已运行的 Chrome，只使用任务自己的匿名上下文
  - 推文正文抓取：`https://r.jina.ai/https://x.com/<handle>/status/<id>`

## 依赖
- Python 3.10+；安装仓库 `web/requirements-maintenance.txt`
- 已运行并通过回环 CDP 可连接的 Chrome，默认 127.0.0.1:9222
- 可选 `JINA_API_KEY`；436 匿名请求受限，当前按用户选择仅显示搜索摘要。

## 快速开始

### 1) 扫描候选推文（收集）
```bash
python3 scripts/scan_x_weekly.py \
  --accounts references/accounts_65.txt \
  --days 7 \
  --batch-size 8 \
  --per-search 8 \
  --outdir ./output/ai-influence-digest
```
输出：
- `candidates.json`（url/handle/text/content_status，无 AI 评分）
- `candidates.md`（便于人工快速扫读）

### 2) 人工筛选并整理成周报 Markdown（编辑）
筛选标准见：`references/filters.md`

建议将最终稿保存为：
- `./output/ai-influence-digest/weekly_report.md`

### 3) 分发或二次加工（可选）
本 skill 不绑定任何发布渠道。需要图文排版、社群分发或知识库归档时，把 `weekly_report.md` 交给外部独立流程处理即可。

## 作者
- X：https://x.com/koffuxu

项目适配：使用 `tools/knowledge_pipeline/acquisition/fetch_x_google.py`，不使用 opencli 或 X API。`x_google_sources_latest.json` 供网站自动采集；最终中文周报仍按需执行。
