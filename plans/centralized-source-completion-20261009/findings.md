# Findings

- Moon原新闻读取Claude latest、Codex latest与recent10，并挑首个preview；原生json_list只接数组，直接改RSS或recent列表会丢失独立latest语义。复用既有bridge，新增一个有界标准库脚本；响应8MiB、25秒、无身份和模型。
- 阮一峰沿用 `https://www.ruanyifeng.com/blog/atom.xml`，原生rss处理发表时间，保留作者原文与更新日期区别。
- BuilderPulse官方所谓RSS是提交动态。436原生web_list预览README中文报告链接成功7项，文件名日期解析正确；最新为2026-08-14，不冒充今日，也无需新解析脚本或clone。
- BuilderPulse原文标CC BY-NC 4.0；此次只存日期／标题／原文链接，全文展示与全文分发关闭。不在采集时派生机会判断。
- 新来源通过既有官方source管理、原生worker或唯一bridge接入。旧 `hub-radar`／`hub-topics` 无有效collector，改暂停保留历史；不删除文章或旧Notebook。

## 436实际回读

2026-10-09 15:26 UTC：阮一峰原生fetch成功，found／new均3；BuilderPulse均7。CLI在15:29 UTC摄取created3，source的last_fetch_at／last_ok_at更新。生产source为110 RSS、3 web_list、12 external，总125；种子为124，不反向覆盖现场独有来源。

最新CLI的实际原发表日期分别为：Claude v2.1.295，2026-10-08 19:48:38 UTC；Codex 0.162.0，2026-10-08 18:55:59 UTC；preview 0.163.0-alpha.4，2026-10-09 13:21:04 UTC。阮一峰414期发表于10月8日，BuilderPulse最新为8月14日。所有日期与发现时间分别入库。

CLI桥接仅传元数据和短摘要；原生worker后续公开页面正文提取仍按既有流程运行，不是新增脚本或付费采集。source全文展示／分发为false，不把数据库正文读取等同于对外全文发布。external成功依据是ingest事件与source成功时间，不能要求它伪造RSS fetch run或将unknown直接写成ok。
