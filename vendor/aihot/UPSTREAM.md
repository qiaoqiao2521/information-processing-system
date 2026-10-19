# 上游来源

- Repository: https://github.com/KKKKhazix/AIHOT
- Commit: cf8f8d07d68dfa9079becc72b0717a45b33485f3
- Snapshot date: 2026-10-01
- License: MIT; see LICENSE. AIHOT name/logo are excluded from the brand license.
- This directory is a versioned source snapshot. The original checkout remains independent.
- Local customizations: industry identity/sources/features and reading workflows; import/ID mapping and bounded validation helpers; external ingest summary/body fields; paused model consumers; reading-tools route with desktop/mobile entries and legacy-link redirects; verified Docker build; X-only Jina target guard, provider-side token cap and on-demand known-post body helper with independent budget. Core scoring rubrics, thresholds, relation judging and heat formula remain upstream.
- Official coverage: explicit pending indexes for six first-party sources through publication; newest-first RSS limits; optional pause of automatic historical processing, including queued jobs; idempotent official-source reconciliation. Pending indexes have no model score or selection.
- Centralized source completion: industry seed adds Ruanyifeng Atom, native BuilderPulse report links with filename dates, and the CLI release bridge. Legacy radar/topics seeds are paused; no upstream engine or model budget change.
- 2026-10-20 public radar: HN discussion context via official API, GitHub stable-release watchlist, and OSS Insight quality-aware adapter reuse the existing external bridge and local processing workflow. Two new external source seeds and a narrow reconciliation/publication script; source dates, evidence hashes and upstream unavailability remain explicit. No core scoring, schema, model budget, or frontend change.

## 本地 mcode 按需加工

模型注册新增 `local-mcode`；只有显式 `MCODE_STDIO_ENABLED=true` 的独立SSH会话可以调用。`modelFor`在该会话统一选择本地模型，保留原有预筛、双次评分、摘要、结构与归组Prompt；不改变普通worker的模型设置。模型响应仍经过回执与独立 `mcode` 预算；断线/超时不自动重发，也不回退服务器API。`scripts/process-local-mcode.ts`限量选择最近官方材料或明确ID，经既有发布层提交结果。本地Python入口在外层仓库 `tools/aihot/local_mcode.py`，只调用工具权限关闭的官方CLI，不传递账号或数据库凭据。

## OpenCode入口更正

用户更正目标为OpenCode内的MiniMax Token Plan。新增`local-opencode`，完整模型ID为`minimax-cn-coding-plan/MiniMax-M3.1-Flash-Preview`，服务回执/预算独立于原mcode与API。`LOCAL_CLI_PROVIDER=opencode`在同一有界SSH会话中固定选择此模型；原MCODE_STDIO_ENABLED与stdio协议名保留兼容。默认推荐外层入口`tools/aihot/local_opencode.py`。OpenCode以`--pure`、独立临时目录、禁用分享、全部工具deny、单步news agent运行；系统/用户Prompt分别传递，temperature应用，max_tokens尚不保证CLI等价。原有已完成mcode分析保留真实记录，不重算或伪造。

## 公开重置结果同步

Codex模块开启展示，`CODEX_RESET_UPSTREAM_ENABLED=true`时由现有worker每15分钟同步AIHOT公开完整v1快照（ETag、4MiB、30秒、有界schema校验），保存在独立settings键，不伪装为本站X采集或账号核验。读取层共用快照，页面保留上游来源/状态/时间，超过45分钟提示缓存；失败不覆盖旧快照。直采SocialData计划在镜像模式禁用，不触发模型和通知。


## 引用加工与人工审批

后台/admin/reviews复用现有登录、CSRF和审计；有界材料从独立只读私有投影读取，不在页面请求中采集或调用模型。0039增量迁移仅新增upstream_reviews表。草稿与引用分开保存；保存版本和来源hash避免旧标签页/模型等待期间覆写。通过显式人工检查后，在同一事务中建立文章、人工override及publishArticleTx公开投影；网页/RSS/API仍读既有publication层。原日期、原文与AIHOT引用保留，上游分数不伪装为本站分析，人工精选单独记录。

本地OpenCode MiniMax 3.1通过--review显式ID生成待审稿，复用opencode的300/24h预算和回执，不新增定时模型任务；已发表稿须先退回待审才能重新加工。v2提示词限制工作日志/泛化清单，已知CLI处理状态前言从面向读者的稿件去除，原始返回留在回执。来源更正/明确撤选每30分钟使已发表稿退出公开层重新待审；仅退出近期窗口不视作撤选。缓存过期阻止新审批，网络失败不伪造撤选。该流程不声称已取得上游转载授权。

## 2026-10-03 自动加工与独立复核

用户确认AI复核通过后自动上站。新增process-upstream-batch.ts及质量复核：仅最近7天有摘要的上游精选材料，先按原文URL去重，再分别进行加工和独立复核，共享原opencode预算/回执。源码仍不自动访问用户浏览器、复制账号或调用付费API。AI通过稿走同一decideReview/publishArticleTx事务并标记AI复核；存疑稿保留draft及理由，不冒充人工审阅、独立原文核验或本站模型评分。原版本/source hash和更正撤选规则继续有效。

外层本机用户级timer每30分钟运行普通Python脚本（3篇/轮、最多6调用）；本机离线时436采集继续，公开加工更新等待本机恢复。/all提供二次加工筛选入口，后台显示最新复核理由。预算暂停允许续跑；已hold、人工编辑或失败/unknown不自动重试。

## 2026-10-11 Make Version 8 前端接回

使用用户 Make 地图版视觉，保留 React Router SSR 和原公开读取层。新增 workbench 展示组件、真实数据映射及组合筛选，沿用 timeline 游标、取消请求和历史恢复；文章详情、原文、收藏、报表、事件及公开接口仍走原实现。真实统计失败仅显示本页数量，不把随机指标或模拟新闻发布。地图属于装饰，不宣称地点/传输核验。按时间完成解码、减少动效支持和手机横滑修复。新增的 d3-geo/topojson-client/world-atlas 采用 Make 版本的固定依赖；上游 MIT 许可保留。只更新 web 镜像。

## 2026-10-12 RSS 来源扩展

行业种子追加七个免费官方/作者 RSS，复用现有 RSS、pending 发布与 worker。首次最多三篇，按原日期归档，全文展示和分发继续关闭。生成器去重并保留既有种子配置；不修改核心引擎、前端或付费预算。

## 2026-10-12 Firecrawl 前瞻公开来源

行业配置新增五项external官方研究来源，复用原摄取及publishArticle。external仅允许已有_aihot元数据以声明pending展示，仍禁止任意未知配置。Python薄适配走官方Firecrawl v2公开scrape，不使用账号浏览器、LLM提取或X搜索；回执与预算在服务器私有持久状态中保存。前端及核心评分不改。

## 2026-10-12 分类阅读与论文工具

首页复用公开pool，类别与分页保留URL状态；精选门槛不再控制首页可见性。缓存继承上游绝对截止时间。六类沿用既有taxonomy，不改分类键或评分引擎。ArXivHub链接按官方`/p/$id`路由生成，仅接受arXiv ID/官方URL。保留436既有原标题优先和加工结果折叠展示；FeedItemSummary增加可选originalTitle，兼容旧API。上游MIT许可保留。

### 同日交互修正

用户指出分类与全部入口重复。删除独立分类导航，根路由保留参数跳转/all，分类改为流内下拉选项。保留既有筛选、分页和缓存边界。公网QA由本地mcode实际浏览器操作，报告分别标记通过、失败、未验收。

## 2026-10-12 NewsNow 外链

按用户要求在阅读工具添加NewsNow官网和GitHub项目入口，复用现有外链卡片，不增加采集或模型调用。

## 2026-10-12 信息加工 workflow

复用现有评分、摘要、分类、事件归组与publication，新增薄workflow编排以消费自己的近期订阅和上游候选。常态处理保持本地OpenCode模型、回执及原预算，避免失败/未知请求自动重发。上游事件候选召回同时比较原标题、加工标题和摘要；复核区分同一次事件与有新增事实的进展。同步保留436已有原文优先、basis、执行日志拦截和直接来源覆盖排除改动，未改前端。

## 2026-10-13 本机个人阅读

用户明确暂不增加账号系统。沿用 Make 视觉、既有 local-state 与 version-1 文件格式，新增“我的”、最近阅读、正文 SHA-256 与语言路径绑定的位置恢复、关注来源、已复制任务及手工结果记录。旧收藏和已读标记保留；新数组为可选字段，旧文件继续可导入。复制不等于模型执行，手工结果保持未复核状态。来源筛选复用公共 pool，包含查询、总数缓存及相关性搜索。未新增账号、自动跨端同步、模型调用或采集时钟；保留上游许可。

语义颜色改为就地解析，修复Make深色容器继承浅色别名；手机卡片限高不再影响阅读正文。保留服务器现有内容来源标记，旧原始标题字段兼容。不接受失效正文指纹的旧位置，结果保留原始空格和换行。独立验证工具对预期根路径跳转、实际正文与桌面/手机操作分别验收。

## 2026-10-14 LifeGame 私有速读草稿

复用现有管理员会话和数据库迁移，新增服务间鉴权的 LifeGame 整理结果入口。结果只进入独立草稿表，不进入文章、公开读取层或模型队列。只接收核心结论、三条看点、实体、公开来源与内容指纹，不接收网页全文。请求编号与结果内容绑定；丢失响应和并发重放返回同一草稿。新增管理员草稿页，保持上游 MIT 许可与个人区默认不公开的选择。

## 2026-10-19 开源阅读站点自托管

阅读工具的NewsNow和ArXivHub主入口指向436独立部署，保留各自官方站点及GitHub链接。单篇论文继续使用同一arXiv身份校验和`/p/{id}`路由，只切换origin到`papers.muqiao.xyz`。沿用Make卡片、复制任务和本机阅读记录；不将两个站点的数据导入publication，不改变模型、采集时钟或数据库。独立上游版本、MIT许可和部署回退见外层`deploy/reader-sites/README.md`。
