# 实测与扩展范围

- 上游公开使用规则：https://aihot.news/terms，版本1.1，2026-09-30。个人非商业阅读与必要私有缓存可直接使用；公网镜像、批量再分发、代理/机器接口转供须提前书面授权。接口无需key或代码MIT都不覆盖内容服务授权。授权邮箱wzglyay@virxact.com；没有发送任何邮件。
- https://aihot.news/feed.xml：最新50条精选中文摘要、GUID、原日期、原文与AIHOT阅读入口；feed ttl=30。
- https://aihot.news/feed/all.xml：近期全部已公开动态；私人缓存保留最多100条。
- 扩展RSS：/feed/daily.xml日报；/feed/category/{ai-models,ai-products,industry,paper,tip}.xml分类。脚本支持这些显式路径，但默认timer仅同步精选/全部。
- /api/v1/items含摘要、评分、精选状态、source、attribution；今后获准公开接入时应保留上游身份，不伪造本站模型回执。
- /api/v1/selected/snapshot + /selected/changes提供新增、修改和撤选游标，优于猜发布时间；不将初始完整历史导入作为当前新闻。
- 其他公开出口：hot-topics、stories/{publicId}事件时间线/综述、dailies/latest与日期日报、MCP。模型榜有公开页面，稳定对外同步接口仍需单独核验。
- 新发现：llms.txt要求重置日常轮询recent、完整历史仅按需。现有公开重置镜像需确认书面授权，并在允许继续后调整完整快照轮询策略；本次不擅自改变已有已授权部署或删除数据。接续Owner：当前Codex，入口plans/upstream-reset-sync。
- 本机Python TLS超时，436Python可正常获取；不能把本机网络失败当作上游不可用。
