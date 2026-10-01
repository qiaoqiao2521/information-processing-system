# 已完成

2026-10-01已部署436，版本`aihot-cf8f8d0-02754911973f`，候选镜像`7a467c4467a7`。运行容器531文件hash与本地一致。

- 真实首次同步39条完整事件，近期3条；上游核验时间保留，HTML展示来源、每15分钟同步、缓存提示和个人账号边界。
- worker已登记`cron.monitor.upstream`、`*/15 * * * *`、Asia/Shanghai。通过同一队列实际执行：job_runs1404，status=ok，HTTP304，39条，成功更新时间2026-10-01T05:19:50.356Z。非Agent任务，无通知。
- 模型MODEL_CALLS_ENABLED=false，采集COLLECT_ENABLED=true；FEISHU_CONTENT_PUSH_ENABLED=false、FEISHU_INTERNAL_ENABLED=false；无原生SocialData监测计划。
- 全量后端199/199、typecheck、web构建和16项web测试通过；公网31项smoke全通过。完整/近期/site/day API可读，真实HTML来源与边界文本存在。此为HTTP验收，未新增浏览器视觉验收。
- 新测试覆盖合法/非法快照、200/304、失败保留、45分钟过期、关闭采集零请求。检查784仓库文件未发现敏感模式，git diff --check通过。
- 无新数据库迁移；只增独立settings键。回退镜像`muqiao-intel-aihot:pre-upstream-sync`；私密配置及旧source-manifest保存`/opt/intelligence-hub/aihot/rollback-upstream-sync`。源码回源当前分支Git。

后续Owner：既有worker每15分钟维护；失败由下次定时运行恢复，保留缓存并标记过期。上游结果不保证个人账号到账，不新增站内AI推断。模型榜保持关闭。
