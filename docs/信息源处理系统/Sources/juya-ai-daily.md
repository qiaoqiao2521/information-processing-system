---
doc_type: reference
entity: juya-ai-daily 信息源
status: active
owner: Muqiao
last_verified: 2026-09-26
---

# juya-ai-daily

## Identity

| 字段 | 值 |
| --- | --- |
| source_id | `juya-ai-daily` |
| cron_id | `daily-juya-ai-summary` |
| layer | `collector + selector + synthesizer` |
| schedule | `07:00 Asia/Shanghai` |
| skill scope | `repo-local` |
| source_of_truth | 橘鸦 AI 早报官方归档站 (`daily.juya.uk/markdown/YYYY-MM-DD.md`) 与开源镜像 (`ViggoZ/juya-daily`) |
| collector script | `tools/knowledge_pipeline/acquisition/fetch_juya_daily.py` |
| canonical outputs | `output_to_user/juya_daily_digest_latest.md`, `output_to_user/juya_daily_sources_latest.json` |

---

## Source Contract

- **采集逻辑**：自动探测并拉取最新一期早报原始 Markdown，结构化解析出五大栏目（要闻、开发生态、产品应用、技术与洞察、行业动态）；
- **要素提取**：保留每条早报的原始出处超链接（包括 Twitter、GitHub、官方博客等）、序号标签与正文深度解读；
- **落地支持**：直接提供全文字段供下游 Knowledge Pack、去重聚类（Fusion）以及自媒体工作站使用。
