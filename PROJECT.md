# 项目上下文

## Why / User Intent

将分散的AI动态、订阅、论文与开源项目变成可追溯、可筛选、按事件归组的阅读工作台。2026-10-01用户明确改用AIHOT为核心，沿用自己的订阅，替换436公网站点；重点升级信息处理。

## Success

采集、双次评分、中文摘要、事件关系判断与热度共用AIHOT处理链路，网页/RSS/API/MCP读取一致；自己的来源进入同一数据库。保留出处、真实日期、历史快照和旧链接；无人值守维护由脚本/worker执行，无通知。

## Constraints

- 品牌沿用木乔 · 信息工作台，保留MIT与上游来源，不使用AIHOT商业品牌。
- 用户批准现有MiniMax常态自动加工，连续24小时最多300次请求，8次/分钟、60次/小时；优先新材料，不批量重算迁移存量。Jina仅用于已有X原帖正文，连续24小时最多50次尝试，1次/分钟、10次/小时；普通网页Jina回退关闭，其他付费采集保持0。
- X/Google搜索继续暂停，验证触发风险规则由Ops管理，不能绕过。
- 436端口只loopback，管理员鉴权与摄取token仅后端；本地会话/.env/运行日志不入库。
- 评分Prompt/门槛先保留上游，尚无个人标注集，不声称已校准。
- 使用和隐私说明由用户后续补充，公开页标明待补充。

## Current State / Priority

核心源码快照 `vendor/aihot`。108 RSS + 10个外部/存量源（3个暂停）。旧Python工作台与knowledge_pack链路仍可本地使用，436旧站和快照用于回退。当前替换进度和真实验收回源 `plans/aihot-core-migration`。

## Non-goals

本次不重写上游评分/聚簇引擎，不开全量付费采集，不自动恢复X搜索，不将编码Agent放进定时任务，不复制账号登录态。

## Knowledge Map

- [部署与回退](deploy/aihot/README.md)
- [当前计划](plans/aihot-core-migration/task_plan.md)
- [上游架构](vendor/aihot/docs/architecture.md)、[评分](vendor/aihot/docs/selection.md)、[事件关系](vendor/aihot/docs/grouping.md)
- [信源配置](vendor/aihot/docs/sources.md)、[行业定制](vendor/aihot/docs/customize.md)
- [旧站与媒体桥接](web/README.md)、[来源契约](docs/信息源处理系统/README.md)
