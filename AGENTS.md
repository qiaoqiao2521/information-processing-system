# 项目入口

先读 `PROJECT.md`，再按任务阅读 `plans/aihot-core-migration` 和 `deploy/aihot/README.md`。

- 网站核心在 `vendor/aihot`，遵循该目录的上游 `AGENTS.md`；版本见UPSTREAM.md。优先行业包与官方external入口，减少核心改动。
- `skills/`为原项目技能源码； `.agents/skills/`为按项目启用入口，不扩大全局范围。
- 不提交.env、私密配置、会话、数据库、日志或运行快照。旧网站与knowledge_pack不可未经核实删除。
- 模型处理、迁移和复制任务文本分别核验；不要给存量伪造AI分数或新日期。当前授权预算见PROJECT.md，不因限量验证成功自行扩大预算。
- X采集保持暂停；定时维护不使用编码Agent，不发外部通知。
- 修订上游副本时更新UPSTREAM.md，迁移只做增量并保留回退。
