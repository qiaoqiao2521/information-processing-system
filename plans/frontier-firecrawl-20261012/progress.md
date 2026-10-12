# Progress

## Current

完成并部署436。五项前沿来源共11篇新增原始公开索引，前端保持冻结，未调用模型。

## Done

- Firecrawl常态接Epoch/Forethought/METR，固定公开HTML列表与详情；ARC/Sakana使用已有web_list，避免429/未知超时后的付费重试。
- 436实采及数据库回读：Epoch1、Forethought2、METR2、ARC3、Sakana3；十一篇均有公开索引，原始日期与类型保留，全文展示/分发关闭。
- 公网搜索“前沿”读回五来源、原始摘要、预测类型和待AI处理；截图 /tmp/muqiao-frontier-firecrawl-20261012.png。
- 类型检查通过；七项新适配测试+四项既有bridge测试共11项通过，覆盖预算/unknown冷却/未知日期/跳转/暂停前阻止付费/缓存摄取重放。配置全量校验、种子重复生成、mjs语法与diff检查通过。
- 故障路径保留：一次Sakana CLI超时、一次ARC详情429；来源改用原生入口。私有ledger记录生产11次及发现阶段5次，首次总计16次尝试；Credit字段未返回时unknown，不假设免费/固定单价。发现阶段请求时间按登记时刻保守占24h预算，不宣称精确消费时间。
- API及worker模型开关读回false，未扩大模型预算/启动X账号搜索/发通知。
- Tailscale SSH → racknerd-436b0c0，API key静默配置root600，不迁移浏览器账号。既有bridge.timer active；每12小时才实际Firecrawl抓取，最多60次/24h尝试。
- 原bridge.service的ExecStopPost已生效，并实际启动验证：2026-10-12北京时间16:59:40–42执行前瞻环节，三路not_due、没有新增付费请求，整个maintenance service Result=success。
- 只补五项source、external的_aihot配置键和独立薄适配；容器/前端镜像及网络未重建、更改。host备份及回退入口见deploy/aihot/README.md。

## Remaining

本批无必需剩余。新材料依原模型预算继续处理，本批实采公开不等于已完成AI评分或验证预测准确性。前沿搜索会同时命中其他文章中的同词，未声称独占来源标签。

## Knowledge closeout

already_covered：Wiki/自动化开发范式与智能体协作.md的按当前任务选择验收依据已覆盖该链路；具体provider失败、回执与部署边界保留本计划，无共享知识改动。
