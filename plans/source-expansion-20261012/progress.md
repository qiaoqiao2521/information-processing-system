# Progress

## Current

完成七项来源扩展并部署436。前端、容器镜像、模型预算、既有时钟保持当前状态。

## Done

- 本机RSS端点实测200，原生配置校验通过；生成器复跑完全一致，既有bridge四项测试通过。
- Tailscale SSH → racknerd-436b0c0；只增补行业配置和数据库七项source，原生collect.ts实采全部ok。
- 首次每源最多3篇；首次新增16篇，NVIDIA改用新鲜总订阅再增3篇，共19篇；URL判重继续生效。
- 数据库公开索引读回：七源各有public条目、last_ok_at非空、fail_count=0，全文展示/分发均false。
- NVIDIA最新三篇读回2026-10-07/08真实日期；旧分类三篇保持4月日期，不删除历史。
- API的modelCallsEnabled读回false，本次不调用模型、Jina或Firecrawl scrape，不新增Agent/通知/时钟。
- 公网直接HTTP API探测403；改用已有浏览器正常搜索，真实PyTorch文章、原日期、来源及待AI处理状态可见。截图 /tmp/muqiao-source-expansion-20261012.png。
- 服务器源码种子先备份为industry/sources-before-expansion-20261012.json。只增补本批source；回退可暂停这七项source，保留文章历史。

## Remaining

无本批实现剩余。LangChain/vLLM feed待另选可验证入口；不把失效URL启用。Firecrawl云返回的余额比例不作为免费预算依据；Firecrawl仍未加入生产付费链路。

## Knowledge closeout

already_covered：Wiki/自动化开发范式与智能体协作.md「按当前任务选择验收依据」已涵盖真实采集与公开读回的区别。无新增共享知识页。
