# 实测与扩展范围

- 上游公开使用规则：https://aihot.news/terms，版本1.1，2026-09-30。个人非商业阅读与必要私有缓存可直接使用；公网镜像、批量再分发、代理/机器接口转供须提前书面授权。接口无需key或代码MIT都不覆盖内容服务授权。授权邮箱wzglyay@virxact.com；没有发送任何邮件。
- https://aihot.news/feed.xml：最新50条精选中文摘要、GUID、原日期、原文与AIHOT阅读入口；feed ttl=30。
- https://aihot.news/feed/all.xml：近期全部已公开动态；私人缓存保留最多100条。
- 扩展RSS：/feed/daily.xml日报；/feed/category/{ai-models,ai-products,industry,paper,tip}.xml分类。现已全部加入私人timer。
- /api/v1/items含摘要、评分、精选状态、source、attribution；今后获准公开接入时应保留上游身份，不伪造本站模型回执。
- /api/v1/selected/snapshot + /selected/changes提供新增、修改和撤选游标，优于猜发布时间；不将初始完整历史导入作为当前新闻。
- 其他公开出口：hot-topics、stories/{publicId}事件时间线/综述、dailies/latest与日期日报、MCP。模型榜有公开页面，稳定对外同步接口仍需单独核验。
- 新发现：llms.txt要求重置日常轮询recent、完整历史仅按需。现有公开重置镜像需确认书面授权，并在允许继续后调整完整快照轮询策略；本次不擅自改变已有已授权部署或删除数据。接续Owner：当前Codex，入口plans/upstream-reset-sync。
- 本机Python TLS超时，436Python可正常获取；不能把本机网络失败当作上游不可用。


## 三项扩展实测

官方发现入口：https://aihot.news/llms.txt。436匿名API实测 schemaVersion=1。

- /api/v1/dailies/latest：report包含date、lead、sections、flashes和归属；仅取最新日报JSON，历史通过30期RSS读取。
- /api/v1/hot-topics：items共10个；story链接使用aihot.virxact.com旧域名。只接受该域名和aihot.news提供的/story/ID，API统一请求aihot.news；不猜测ID、不全库遍历。
- /api/v1/stories/{publicId}：story.reports含文章标题、摘要、来源、publishedAt、原文链接；digest为上游综述。实跑10个事件的storyline均为空，报道日期全部存在，9个digest非空。不能把空storyline说成已有事件节点。
- /api/v1/selected/snapshot?limit=1用于游标水位，不按该历史快照第一条判断新旧；/items?mode=selected&window=7d&by=published&limit=100提供近期阅读种子。
- /api/v1/selected/changes：op=upsert带完整item，op=remove带id；cursor不解码。remove为退出精选语义，不据此删除全部动态。近期缓存和撤选记录均有数量上限，每轮最多500变更；不是全历史镜像。
- RSS GUID与API id实测一致；分类变化会从旧分类缓存移除，下轮新分类RSS提供新归属。
