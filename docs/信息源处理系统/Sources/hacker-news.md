---
doc_type: reference
entity: hacker-news 信息源
status: active
owner: Muqiao
last_verified: 2026-09-26
---

# hacker-news

## Identity

| 字段 | 值 |
| --- | --- |
| source_id | `hacker-news` |
| cron_id | `daily-hacker-news-watch` |
| layer | `collector + selector + synthesizer` |
| schedule | `08:00 Asia/Shanghai` |
| skill scope | `repo-local` |
| source_of_truth | Y Combinator Hacker News 实时热榜 (`news.ycombinator.com/rss`) |
| collector script | `tools/knowledge_pipeline/acquisition/fetch_hacker_news.py` |
| canonical outputs | `output_to_user/hacker_news_digest_latest.md`, `output_to_user/hacker_news_sources_latest.json` |

---

## Source Contract

- **采集逻辑**：抓取 HN 前端实时 Top 30 议题，提取外部原文链接与 HN 评论区讨论链接；
- **智能分类**：自动区分为 `AI & LLM Frontier`（前沿模型与应用）、`Show HN (New Launches)`（首发新品）、`Dev Tools & Infra`（开发工具与基建）、`Ask HN` 以及 `General Tech`；
- **免登与零依赖**：利用公共 RSS 协议直连，不依赖三方 API Token，零封锁风控。
