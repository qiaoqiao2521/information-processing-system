# 上游来源

- Repository: https://github.com/KKKKhazix/AIHOT
- Commit: cf8f8d07d68dfa9079becc72b0717a45b33485f3
- Snapshot date: 2026-10-01
- License: MIT; see LICENSE. AIHOT name/logo are excluded from the brand license.
- This directory is a versioned source snapshot. The original checkout remains independent.
- Local customizations: industry identity/sources/features and reading workflows; import/ID mapping and bounded validation helpers; external ingest summary/body fields; paused model consumers; reading-tools route with desktop/mobile entries and legacy-link redirects; verified Docker build; X-only Jina target guard, provider-side token cap and on-demand known-post body helper with independent budget. Core scoring rubrics, thresholds, relation judging and heat formula remain upstream.
- Official coverage: explicit pending indexes for six first-party sources through publication; newest-first RSS limits; optional pause of automatic historical processing, including queued jobs; idempotent official-source reconciliation. Pending indexes have no model score or selection.

## 本地 mcode 按需加工

模型注册新增 `local-mcode`；只有显式 `MCODE_STDIO_ENABLED=true` 的独立SSH会话可以调用。`modelFor`在该会话统一选择本地模型，保留原有预筛、双次评分、摘要、结构与归组Prompt；不改变普通worker的模型设置。模型响应仍经过回执与独立 `mcode` 预算；断线/超时不自动重发，也不回退服务器API。`scripts/process-local-mcode.ts`限量选择最近官方材料或明确ID，经既有发布层提交结果。本地Python入口在外层仓库 `tools/aihot/local_mcode.py`，只调用工具权限关闭的官方CLI，不传递账号或数据库凭据。

## OpenCode入口更正

用户更正目标为OpenCode内的MiniMax Token Plan。新增`local-opencode`，完整模型ID为`minimax-cn-coding-plan/MiniMax-M3.1-Flash-Preview`，服务回执/预算独立于原mcode与API。`LOCAL_CLI_PROVIDER=opencode`在同一有界SSH会话中固定选择此模型；原MCODE_STDIO_ENABLED与stdio协议名保留兼容。默认推荐外层入口`tools/aihot/local_opencode.py`。OpenCode以`--pure`、独立临时目录、禁用分享、全部工具deny、单步news agent运行；系统/用户Prompt分别传递，temperature应用，max_tokens尚不保证CLI等价。原有已完成mcode分析保留真实记录，不重算或伪造。

## 公开重置结果同步

Codex模块开启展示，`CODEX_RESET_UPSTREAM_ENABLED=true`时由现有worker每15分钟同步AIHOT公开完整v1快照（ETag、4MiB、30秒、有界schema校验），保存在独立settings键，不伪装为本站X采集或账号核验。读取层共用快照，页面保留上游来源/状态/时间，超过45分钟提示缓存；失败不覆盖旧快照。直采SocialData计划在镜像模式禁用，不触发模型和通知。


## 引用加工与人工审批

后台/admin/reviews复用现有登录、CSRF和审计；有界材料从独立只读私有投影读取，不在页面请求中采集或调用模型。0039增量迁移仅新增upstream_reviews表。草稿与引用分开保存；保存版本和来源hash避免旧标签页/模型等待期间覆写。通过显式人工检查后，在同一事务中建立文章、人工override及publishArticleTx公开投影；网页/RSS/API仍读既有publication层。原日期、原文与AIHOT引用保留，上游分数不伪装为本站分析，人工精选单独记录。

本地OpenCode MiniMax 3.1通过--review显式ID生成待审稿，复用opencode的300/24h预算和回执，不新增定时模型任务；已发表稿须先退回待审才能重新加工。v2提示词限制工作日志/泛化清单，已知CLI处理状态前言从面向读者的稿件去除，原始返回留在回执。来源更正/明确撤选每30分钟使已发表稿退出公开层重新待审；仅退出近期窗口不视作撤选。缓存过期阻止新审批，网络失败不伪造撤选。该流程不声称已取得上游转载授权。
