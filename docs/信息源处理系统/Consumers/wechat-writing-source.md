---
doc_type: reference
entity: 公众号写作素材交接
status: active
owner: Muqiao
last_verified: 2026-10-06
---

# 公众号写作素材交接

信息工作台负责发现与取得材料；公众号项目负责选题冻结、写作、内容审查、排版和收件入库。网站 PostgreSQL 与公众号发布器 SQLite 是两套数据库，不能用其中一套的条数判断另一套是否完成生产。

## 已有发现接口

公网 `https://intel.muqiao.xyz/api/v1/items`；436 本机同一接口为 `http://127.0.0.1:8088/api/v1/items`。使用已有公开 API，不另开服务，不传管理员或数据库凭据。

```text
GET /api/v1/items?mode=all&window=24h&by=timeline&limit=100
```

响应 `schemaVersion=1`，条目在 `items`。`page.hasMore=true` 时携带返回的 `page.nextCursor` 翻页；记录查询窗口、取得时间和是否读完。当天材料不足可明确回退 `window=7d`，不能把旧文改成当天发布。

| 字段 | 用途和边界 |
| --- | --- |
| `id` | 稳定站内标识，交接包保存为 `provenance.site_item_id` |
| `links.original` | 原作者页面入口；优先直接取得这里的正文及官方附件 |
| `links.aihot` | 工作台条目页，用于发现溯源；不是一手全文承诺 |
| `title` / `originalTitle` | 站内标题与原始标题，不能混同二次加工稿和原始报道 |
| `source.name` | 供给来源，原作者另从原文署名核实 |
| `publishedAt` / `discoveredAt` | 发表时间与本站发现时间；保留原值及原文的日期口径 |
| `score` / `selected` | 本站处理结果；`null` / `false` 不表示没有原文，不是材料深度判断 |
| `summary` | 发现线索。待处理条目可能只含来源短摘；不能据此声称读过原文 |

## 正文获取与身份核对

`/api/site/items/:id` 的 `body` 是否存在受 publication 和全文权限控制。官方源当前 `site_fulltext=false`，即使后台已采到全文，公开详情也可能没有 `body`。保持这个边界，从 `links.original` 和其明确链接的官方附件取得写作材料。

- 公开二次加工稿的正文包含本站分析及上游引用，不能冒充原作者全文。
- 后台 `articles.body_text`、`body_status` 是采集记录；`ok` 与正文长度不能证明读到了论文全部章节，也不能替代作者、版本与附件身份核实。
- PDF 要记录原链接、落地页、文件 hash、页数与提取方法；选读章节明确页码，摘要不能标为全文。
- 仓库 README、发行说明与实现代码分别记版本和位置；未运行的项目，不写成复现实测。
- 正文、附件、冻结 feed 和运行快照只保存在忽略的本地目录，不提交 Git，不整本复制到公网。

## 本地素材包

下列是交接 JSON 的字段约定，不是公开 API 新增字段，也不代表公众号已经自动导入。公众号任务显式接入自己的冻结计划并校验材料。

| 字段 | 内容 |
| --- | --- |
| `url`、`source_kind` | 主材料身份与类别，例如 `official_article` |
| `body`、`body_sha256` | 主材料实际正文及 UTF-8 SHA256；不放编辑建议或生成分析 |
| `evidence_scope`、`retrieved_at` | 取得了什么、人工读到哪里、尚未验证什么，以及取得时间 |
| `full_body_file`、`full_body_sha256` | 相对包根目录的原文归档路径和 hash，交接时验证路径与字节 |
| `documents[]` | 辅助一手材料的 `url`、`title`、实际 `body`、`body_sha256`、`evidence_scope`；选读 PDF 加 `pdf_pages` / `complete=false` |
| `provenance` | `site_item_id`、`site_item_url`、原始来源及冻结 feed hash |
| `editorial_brief` | 读者、核心问题、写作价值和可修改角度；与一手材料分开 |
| `claims`、`limits` | 可核对结论的位置与证据边界；写作审查仍需核对具体引用片段 |

验证正文 hash 只能证明冻结后未改字节，不能证明事实正确。内容审查应逐条核对引用是否来自对应 `document.url` 的归档 `body`，并区分作者结论、研究建议、作者示例、本文推演和实际测试。

## 每日三篇的选题顺序

1. 从新鲜、未写过的独立事件发现候选，保留原文日期。`mode=all` 包含尚未精选的原始官方条目。
2. 先验证一手正文、作者和实质材料，再按主题价值排序。摘要或 README 可以启动调查；仅几百字符不能独自支撑技术长文。
3. 方法、实现、实验条件、结果和局限应有可定位材料。产品营销与排行榜需要归属来源，不补编场景、指标或实测。
4. 同一模型或版本的重复报道合为一个选题。方法实现、研究证据、工具实践可用于搭配，但不是必须凑齐的三个槽位。
5. 材料不足就明确留空或延后，不重复旧稿，不靠拉长摘要凑字数；日期回退和不足原因进入公众号计划。

## 交付验收与责任

信息源验收看真实原文、附件、身份、日期和 hash；公众号验收看新文章文件、内容审查结论、436 收件回读，以及新的 SQLite 文章 ID 和正文 hash。timer 启动、模型返回或网站增加稿件，均不能替代公众号的新稿入库。

2026-10-06 已向公众号根任务交出 Google Research 10 月 5 日智能体隐私与安全主题的本地素材包：站内 ID `jhgedr5xxe277yswpisrhe36r`，官方博客全文、完整 116 页技术报告及明确选读的 7 页。它适合一篇技术解释稿；报告是开放研究议程，包本身没有批准文章发布，也没有实现或复现实验。

同日约13:42CST取得协作回执：该包产出公众号新草稿112《给Agent权限之后，为什么它仍可能越界？》，独立内容预审一次通过，实际微信回读一致，SQLite为`draft_created`、工作流为`draft_verified`。源侧独立核对取回文件的源稿、Markdown和回读HTML hash。该结果仅代表一篇已入草稿箱，未公开发布；后续定时槽需要各自真实回读，不能用单篇代替每日三篇验收。

后续素材取得仍沿用已有 API、官方原文和附件。X / Google 搜索保持暂停，普通网页不使用 Jina；不增加账号、服务或模型额度。

## 代码依据

- [公开 API 路由](../../../vendor/aihot/apps/api/src/routes/v1.ts)
- [公开详情与全文规则](../../../vendor/aihot/packages/backend/src/publication/detail.ts)
- [自动加工发布的任务边界](../../../plans/upstream-editorial-review/task_plan.md)

采用知识：`Wiki/自动化开发范式与智能体协作.md#按当前任务选择验收依据`，在这条交接中分别核对来源材料、生成行为和目标入库。
