---
doc_type: reference
entity: qiaomu-rss-ecosystem 信息源
status: active
owner: Muqiao
last_verified: 2026-09-26
---

# qiaomu-rss-ecosystem

## Identity

| 字段 | 值 |
| --- | --- |
| source_id | `qiaomu-rss-ecosystem` |
| cron_id | `daily-qiaomu-rss-harvester` |
| layer | `collector + selector + synthesizer` |
| schedule | `08:30 Asia/Shanghai` |
| skill scope | `repo-local` |
| source_of_truth | `joeseesun/qiaomu-ai-rss` 内置精选池（718 个 AI/Tech Tidings + 1342 个独立中文博客） |
| repo task contract | `information-processing-system/docs/信息源处理系统/Sources/qiaomu-rss-ecosystem.md` |
| collector script | `information-processing-system/tools/knowledge_pipeline/acquisition/fetch_qiaomu_rss.py` |
| local data snapshot | `information-processing-system/data/qiaomu-rss/tidings.json`, `independent-blogs.json` |

---

## Source Contract

| 字段 | 值 |
| --- | --- |
| source_of_truth | 乔木 RSS 生态聚合池，包含海外一线 AI Newsletter、中文独立博客、微信公众号转写与技术周刊 |
| access_path | 本地零依赖采集脚本 `fetch_qiaomu_rss.py` (基于标准库 `urllib` 与 `xml.etree`) |
| freshness_policy | 每次运行优先扫描 `ai`、`engineering`、`weeklies` 与 `top200` 精选包中最新 24-48h 条目 |
| selection_policy | 每个精选源最多提取 2-3 篇实质文章；清洗 HTML 噪音并提取首屏摘要 |
| output_contract | 中文 Markdown 精选简报 + 标准下游 `knowledge_pack` JSON manifest |

---

## 分类包设计 (Packs)

系统支持按专题包（Packs）精准收割与调度：
1. **`ai`**：99 个全球顶级 AI 实验室与独立 AI Newsletter（Google AI, Anthropic News, Apple ML, Lilian Weng, 等）；
2. **`engineering`**：419 个一线科技大厂与开源团队工程博客；
3. **`weeklies`**：高信噪比技术周刊（阮一峰科技爱好者周刊、tw93 潮流周刊等）；
4. **`blogs` / `chinese`**：1,342 个中文极客独立博客（基于 `timqian/chinese-independent-blogs`）；
5. **`top200`**：综合权重前 200 核心技术源。

---

## Canonical Outputs

- **Markdown 简报**：`output_to_user/qiaomu_rss_digest_latest.md`
- **JSON Manifest**：`output_to_user/qiaomu_rss_sources_latest.json`
- **通用 OPML 订阅表**：`output_to_user/qiaomu_rss_feeds.opml`（可一键导入任意通用阅读器）

---

## Downstream Consumers

- [[../Consumers/notebooklm-report]]：作为中文一手长文素材注入 NotebookLM 知识包
- `muqiao-media-studio`：作为自媒体选题库的高质量长文事实依据
- `knowledge_pack_latest.json`：自动进入多源协同与去重聚类（Fusion）流水线

---

## 容错与降级策略 (Failure Behavior)

- 单个 RSS/Atom 源超时（默认 6s）或解析失败时，静默跳过并记录调试日志，不阻断主采集流。
- 全网断网时，退回读取 `data/qiaomu-rss/` 本地快照，确保离线模式下元数据与源清单仍然可查。
