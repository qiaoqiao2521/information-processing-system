# 集中采集收口

## Goal / Scope

2026-10-09用户要求：未被436覆盖的来源迁入网站，Notebook下游消费停止。迁移CLI官方稳定／预览更新、阮一峰Atom、BuilderPulse中文报告；HN／橘鸦复用已有来源。不新增cron、Agent、模型预算或核心引擎。

## Plan / Acceptance

1. 对比原脚本及官方输入，保留真实日期与原文链接。（completed）
2. 阮一峰／BuilderPulse复用原生rss／web_list；CLI小脚本补单对象latest与首个preview。（completed）
3. 离线验证后部署436，采集入库与现有时钟分别回读。（completed）
4. 停止Notebook及旧信息流水线触发器，保护历史成果。（completed；Ops回读）
5. 根Agent独立核验、更新项目与Ops、提交推送。（completed；本批实现与文档随当前提交交付）

完成依据为实际source记录、成功采集、原日期、入库URL、唯一时钟和旧trigger删除。进程退出、配置存在和页面栏目不是替代证据。

## Adopted Knowledge

沿用Obsidian `Wiki/自动化开发范式与智能体协作.md`「按当前任务选择验收依据」：配置、采集、原始日期与公开加工分别判断。此次只补来源，不调用模型，不伪造旧刊的新鲜度。
