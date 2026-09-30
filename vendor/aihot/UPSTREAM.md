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
