# Progress

## Current

2026-10-09：来源补齐已部署436，实际入库通过；旧采集和Notebook定时消费已退役。代码、验收与Ops说明已完成，本批随当前提交交付。

## Done

- 只读确认原CLI稳定／preview语义、阮一峰Atom与BuilderPulse官方中文报告。
- BuilderPulse原生预览7项，最新8月14日；没有将提交RSS或旧本地文件冒充采集接管。
- CLI脚本14项离线测试通过；采集、bridge、catalog、refresh与maintenance共33项检查通过。
- AIHOT隔离副本使用Node 24.19.0与普通用户临时PG16测试库：类型检查、网页构建、网页16项、完整后端202项通过；来源相关32项在安全阀关闭时先通过。完整后端仅启用本地模型替身，未用生产库或真实凭据，临时库与工作区已清。
- 官方source管理新增三项；原生worker实采阮一峰3条、BuilderPulse7条。CLI在服务器窄范围刷新并摄取3条：Claude v2.1.295、Codex 0.162.0与0.163.0-alpha.4。根Agent独立数据库回读确认原URL、发表日期与摄取时间。
- 436新增来源为125个生产source中的3个；仓库种子124项，差额是已有现场来源。旧hub-radar／hub-topics暂停保留存量，不当作采集入口。
- 运行release为`20261009T152851-central-sources`，四个程序文件hash与本地一致；现有bridge timer仍active，旧maintenance timer仍inactive。RSS／web_list沿用原生worker，CLI进入原bridge，未增加时钟或Agent。
- API与worker的modelCallsEnabled独立回读均false。采集入库不等于AI加工或全部公开发布；未启动模型、X、Google、Notebook导入或消息发送。
- 阮一峰明确复用publishPending原始待处理展示；CLI／BuilderPulse未启用该配置，不声称全部材料已公开或已有评分。
- Cy／Moon消费及残余新闻、BuilderPulse入口退役：Cy16、Moon21个routine均archived、trigger为空。原运行历史、来源说明、Notebook和文件保留；BF14、Green12此前已退役，共原63项全部归档。

## Remaining / Next

本批无剩余实现；文档与代码沿用当前分支交付，Ops记录来源接管、消费停止与实际边界。本次不启用AI加工，不恢复Notebook定时任务。四个既有失败RSS仍由网站仓库后续处理，不重开分布采集。

## Runtime boundaries

CLI脚本只传不超过600字的摘要，bodyText为空。入库后，现有原生worker按原流程读取公开正文，数据库已存在部分正文；三项source的全文展示和全文分发开关均false。BuilderPulse七项只有标题、链接和文件名原日期，最新2026-08-14，没有把发现时间当成发表时间。

外部CLI摄取有成功ingest记录及last_ok_at，但原生external的health仍unknown，未直接改库冒充原生fetch健康；原生RSS／web_list有各自ok fetch run。两类入口分别验收。

## Knowledge closeout

`already_covered`：现有Wiki「按当前任务选择验收依据」已覆盖采集／日期／入库区别。具体来源状态留本计划，不新增平行知识页。
