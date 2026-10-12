# Firecrawl 前瞻采集

目标：436网站持续纳入前沿研究、评测与条件预测。复用现有external摄取、发布读取层和bridge timer，前端保持冻结。

范围：Epoch AI、Forethought、METR、ARC Prize、Sakana AI；Firecrawl只抓公开列表及详情，每12小时运行，Firecrawl每源每轮最多2篇；原生来源首次最多3篇、连续24小时60次请求尝试。Credit消耗独立记录，次数不等于Credit。模型预算不变，X/Google账号搜索仍暂停。

验收：真实抓取、原始日期、摄取及公开索引、网站结果、定时挂接和失败持久化分别确认。

状态：完成，实采、公开读回及维护入口实际执行通过。
