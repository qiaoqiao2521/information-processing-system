# Findings

本地 Firecrawl CLI 1.25.0 已认证；仅查询状态，未调用 scrape/crawl。额度返回异常比例，不能当作无限额度或免费承诺。

七个新增 URL 本地返回 HTTP200 并解析为 RSS/Atom。LangChain 旧 RSS 跳转 HTML、vLLM 旧 feed404，暂缓。BAIR 已接，不重复添加。

官方能力参考：https://blog.cloudflare.com/tag/ai/ 、https://www.nvidia.com/en-us/about-nvidia/rss/ 、https://pytorch.org/blog/ 。Firecrawl 自托管能力及限制：https://docs.firecrawl.dev/contributing/self-host 。

采用 Wiki/自动化开发范式与智能体协作.md 的「按当前任务选择验收依据」：配置、真实采集、数据库与公开读回分别证明。

NVIDIA 分类 feed 可解析但最新日期仅2026-04-14；改用 https://developer.nvidia.com/blog/feed/ ，最新2026-10-08。既有三条历史文章保留真实日期，仅为本批刚创建的源重置一次初次采集游标，增量导入三篇；不重置其他来源。该入口范围为全部开发者博客，名称据此修正。

本地配置131项，服务器源码种子128项：保留现场种子差异，仅合并本批七项，不用本地旧种子覆盖服务器。数据库现场新增七项，未覆写其他管理配置。
