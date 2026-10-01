# 选择与边界

- 复用上游公开API：`https://aihot.news/api/v1/codex-resets`；436访问200，本地Python TLS失败不代表服务器不可达。
- 全量快照目前39条，近期接口3条；15分钟ETag条件获取完整快照，旧记录撤回/修正无需自己猜测增量。
- 独立`settings.monitor.upstream`缓存；不写本站原生X帖子/识别/重置事件表，不把转载确认冒充本账户核验。
- 读取层复用现有页面、历史日历、v1/recent，保留原帖、上游URL、状态、checkedAt。额外upstream元数据提供最近成功同步时间与45分钟过期标记。
- guard固定HTTPS地址、30秒、4MiB、无重定向；schema/计数/ID校验后才覆盖缓存；304只刷新同步时间；失败保持旧快照。
- worker每15分钟执行`monitor.upstream`；镜像模式不登记SocialData的原生monitor.tick/lookback，不调用模型、不发送通知。模型榜未在本次启用。
