# Current

2026-10-03已完成自动加工发布纠偏，部署436。实际3篇：2篇通过并公开、1篇因效果推断写成确定能力而留待审；旧ChatGPT Sites样稿仍保留待审。Owner：当前根Codex。

# Done

- 原0039草稿/引用/人工审批、登录/CSRF、版本和source hash、更正/撤选、原文URL去重、统一publication边界保留。初版仅1篇草稿且无常态本地处理，是用户在/all看不到加工的原因。
- 新增最近7天新材料批次与独立质量复核。只有材料支撑、具体新增价值、无重复全部通过才发布；AI复核如实标记，评分null、不自动精选，不声称独立查阅原文。
- 预算暂停可续跑；hold、人工改稿、失败/unknown不定时重复付费。source hash或稿件版本在模型等待期间变化，阻止旧答复发布。
- /all新增“AI加工”筛选，正文展示分析、待核实、原样引用和原文链接；后台显示最新复核理由。
- 实际本地OpenCode MiniMax-M3.1-Flash-Preview共6次调用，回执328–333均completed、transport=stdio-opencode：Project Suncatcher（review-ljyywltag6vvryw193ryz7lgd）与DGX Spark（review-epb245so8hb7m1r74gumw2dze）通过公开；Finances（ouqidz9vopsnd1srzkmfz4zmn）hold，公开404。
- 436运行镜像26f8e7e4e8c3，release=aihot-auto-26f8e7e4e8c3；health正常，匿名后台401，已发布详情200，原日期和空评分保持。436原API模型消费者false，reader timer active。
- 本机~/.config/systemd/user/intelligence-hub-local-processing.{service,timer}已启用，每30分钟3篇、最多6次无工具请求，共享opencode预算8/分钟、60/小时、300/连续24小时；首次下一轮当时检查为04:24:29 CST。普通Python/SSH脚本，不发通知，账号留本机；本机离线时436采集继续。
- 类型/构建、前端16项、全新隔离数据库后端202项、Python适配器4项与上游12项通过。公网31条smoke通过。隔离Playwright1440/390实测/all点击AI加工→已发布详情，分析/待核实/引用可见，无pageerror或横向溢出；截图仅/tmp验收产物。
- 旧镜像tag muqiao-intel-aihot:pre-auto-processing及auto-processing-staging/app-before-auto.tgz、compose.previous.yaml保留，可停本机timer后回退；生产数据库/卷保留。

# Remaining

Finances及旧Sites稿保持待审，可在/admin/reviews查看原因并修改后再审；不能宣称已完成原文独立事实核验。自动任务仅覆盖近期上游材料，不重算旧存量或恢复X/Google搜索。本机服务依赖机器在线且用户服务运行。

# Next

后续从timer日志和后台稿件查看新结果；模型额度/认证失效则保持草稿，不回退付费API。
