# Findings

官方来源：https://epoch.ai/publications 、https://www.forethought.org/research 、https://metr.org/blog/ 、https://arcprize.org/blog 、https://sakana.ai/blog/ 。

本地Firecrawl CLI1.25.0已认证，Epoch列表真实html/links抓取成功。官方API：https://docs.firecrawl.dev/api-reference/endpoint/scrape 。既有后端无Firecrawl provider；复用external摄取，薄Python适配只承担固定公开来源、付费尝试回执和水位。静态API key由CLI配置安全传输至436后端，浏览器凭据不参与。

网站pending公开投影由既有publishArticle/republishSource生成，不在网页请求中抓取或调用模型。

Firecrawl对Sakana列表的一次CLI调用超时，ARC一次服务器详情调用返回429；未立即重试。两个站的原生HTML可解析，改用已有web_list worker并保留失败记录。实际常态Firecrawl为Epoch、Forethought、METR三路。原生来源首次三篇，Firecrawl每轮每源最多两篇。

Forethought只选ListCard直接子链接，排除featured及正文内交叉引用；日期依次取原站meta/time/JSON-LD/卡片原日期，无法确认留空。原生Sakana的时区为+09，网站显示北京时间，日期跨日是正确换算。

网页入口沿用搜索“前沿”，会同时命中其他文章正文中的同词，不称独占标签筛选；新来源名称均带前沿前缀。新材料没有伪造模型分数或预言概率。
