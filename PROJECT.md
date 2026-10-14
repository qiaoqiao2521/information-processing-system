# 项目上下文

## Why / User Intent

将分散的AI动态、订阅、论文与开源项目变成可追溯、可筛选、按事件归组的阅读工作台。2026-10-01用户明确改用AIHOT为核心，沿用自己的订阅，替换436公网站点；重点升级信息处理。

2026-10-09用户确认信息收集集中在436网站，未覆盖的来源也迁入该站；其他服务器不再保留采集时钟。Notebook下游定时消费停止，历史Notebook与成果保留，不继续等待恢复。来源迁移按实际采集和入库验收，不凭同名栏目或已有配置判断接管完成。

## Success

采集、双次评分、中文摘要、事件关系判断与热度共用AIHOT处理链路，网页/RSS/API/MCP读取一致；自己的来源进入同一数据库。保留出处、真实日期、历史快照和旧链接；无人值守维护由脚本/worker执行，无通知。

## Constraints

- 品牌沿用木乔 · 信息工作台，保留MIT与上游来源，不使用AIHOT商业品牌。
- 用户批准现有MiniMax常态自动加工，连续24小时最多300次请求，8次/分钟、60次/小时；优先新材料，不批量重算迁移存量。Jina仅用于已有X原帖正文，连续24小时最多50次尝试，1次/分钟、10次/小时；普通网页Jina回退关闭，其他付费采集保持0。2026-10-12用户授权Firecrawl用于公开前瞻来源；初始每12小时检查、每源每轮最多2篇，连续24小时最多60次抓取尝试，Credit消耗独立记录，不扩大模型预算。
- X/Google搜索继续暂停，验证触发风险规则由Ops管理，不能绕过。
- 六个明确配置的官方来源及本批阮一峰个人订阅先公开原始标题/摘要/出处并标记待AI处理，模型完成后才发布评分/精选。CLI发布与BuilderPulse未启用原始待处理发布。订阅历史资料暂停自动加工，不抢占新内容预算。
- 用户更正目标为本地OpenCode内的MiniMax Token Plan：`minimax-cn-coding-plan/MiniMax-M3.1-Flash-Preview`。复用本机已有CLI认证，SSH传递有界模型请求与回答，账号不迁移；推荐`tools/aihot/local_opencode.py`；2026-10-03用户确认AI独立复核通过后自动发布。本地独立会话，opencode独立连续24小时300次保守上限、单次默认40次；未验证无限额度。此前误用自家mcode的真实分析保留，不伪装为OpenCode结果。
- 436原API模型消费者暂停，采集继续；本地处理会话单独启用模型，避免两端重复加工。
- 436端口只loopback，管理员鉴权与摄取token仅后端；本地会话/.env/运行日志不入库。
- 评分Prompt/门槛先保留上游，尚无个人标注集，不声称已校准。
- 使用和隐私说明由用户后续补充，公开页标明待补充。

- 用户授权同步AIHOT公开Codex重置结果：`CODEX_RESET_UPSTREAM_ENABLED=true`，现有worker每15分钟条件获取完整快照，45分钟过期提示；不启用X直采、模型识别或通知。见[同步计划](plans/upstream-reset-sync/task_plan.md)。

- AIHOT 已部署8路RSS、最新日报、热点10个事件详情及近期精选评分/变更游标的私人缓存与30分钟脚本timer，复用上游摘要、综述和评分，不进模型队列或公网站点数据库。新核实上游公开使用规则：公网镜像/批量再分发须书面授权；当前无上游书面授权记录；用户在2026-10-01明确选择引用保留、AI二次加工和审批后发布网站，2026-10-03确认由AI独立复核通过后自动发布，存疑稿留给人工。二次加工不作为授权依据。436定时采集只生成私人缓存，本机timer执行有界加工/复核并发布通过稿；审批入口见[加工审批](plans/upstream-editorial-review/task_plan.md)。

## Current State / Priority

2026-10-14用户选择LifeGame速读结果同步到私有草稿。436增加管理员入口 `/admin/lifegame`，只接收LifeGame服务的令牌授权写入；同请求幂等，不进入公开publication。API/web已部署 `lifegame-20261014-985f491701ac`，真实MiniMax结果的单行入库和管理员网页读回通过。未新增读者账号。见[个人阅读进度](plans/mature-product-user-structure-20261013/progress.md)。

2026-10-13用户明确暂不增加账号系统，先实现其他个人功能。436已部署“我的阅读” `/me`：本机收藏入口、最近阅读与正文SHA-256绑定的位置恢复、关注来源及公共来源筛选、复制任务记录、手工结果保存和文件导入导出。沿用Make视觉，修正深色颜色绑定和手机正文段落限高。旧收藏及已读标记保留；个人记录仅当前浏览器保存，手工结果保持未复核，自动跨端同步未启用。此前书籍笔记采集方向为Agent误解，已撤销。见[实现与验收](plans/mature-product-user-structure-20261013/progress.md)。

2026-10-12信息加工任务统一称为workflow，与遗留cron区分。`intelligence-hub-workflow.timer`替换原local-processing timer，串行处理自己的近期订阅与上游候选；本地OpenCode固定MiniMax3.1，沿用共享预算与无通知规则，运行结果写本机私密last-run.json。进度见[信息加工workflow](plans/news-workflow-20261012/progress.md)。

2026-10-12新增前瞻采集：Epoch AI、Forethought、METR、ARC Prize、Sakana AI，经Firecrawl进入原external链路。前沿研究、评测与条件预测保留类型、出处及原日期；入口沿用网站搜索“前沿”。2026-10-12用户取消独立分类导航：只保留全部动态，分类作为列表内下拉选项。沿用Make视觉，全部公开材料不受精选门槛过滤；未分类材料保留在全部列表。验收增加本地mcode直接操作公网站点QA。436安装官方Firecrawl CLI，复用现有云端认证及既有定时脚本。进度见[Firecrawl前瞻采集](plans/frontier-firecrawl-20261012/progress.md)。

核心源码快照 `vendor/aihot`。来源种子新增阮一峰RSS、BuilderPulse中文日报网页与CLI官方发布bridge；旧机会雷达／融合简报仅存量保留。旧Python工作台与knowledge_pack仍可手动使用，Notebook定时消费退役。436旧站和快照用于回退。来源补齐进度见 [集中采集收口](plans/centralized-source-completion-20261009/progress.md)，核心迁移进度回源 `plans/aihot-core-migration`，官方覆盖修复见 `plans/official-source-coverage`。

## Non-goals

本次不重写上游评分/聚簇引擎，不开全量付费采集，不自动恢复X搜索，不将编码Agent放进定时任务，不复制账号登录态。本地OpenCode无工具地回答信息加工Prompt；本机用户级workflow每30分钟加工近期自订阅与上游材料，上游稿独立复核，通过后自动上站，存疑稿留待审。

不在各服务器恢复RSS、GitHub趋势、AI Builders或旧日报采集cron，不恢复Notebook定时消费。公众号写作与网站采集分别验收；下游资料保留，不扩大模型预算或新增采集时钟。

## Knowledge Map

- [部署与回退](deploy/aihot/README.md)
- [当前计划](plans/aihot-core-migration/task_plan.md)
- [本地CLI加工与OpenCode更正](plans/local-mcode-processing/task_plan.md)
- [上游架构](vendor/aihot/docs/architecture.md)、[评分](vendor/aihot/docs/selection.md)、[事件关系](vendor/aihot/docs/grouping.md)
- [信源配置](vendor/aihot/docs/sources.md)、[行业定制](vendor/aihot/docs/customize.md)
- [旧站与媒体桥接](web/README.md)、[来源契约](docs/信息源处理系统/README.md)
- [公众号写作素材交接](docs/信息源处理系统/Consumers/wechat-writing-source.md)：沿用公开发现 API，原文和附件独立归档；网站与公众号入库分别验收。
