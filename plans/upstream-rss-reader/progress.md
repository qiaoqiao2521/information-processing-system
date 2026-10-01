# 已完成：私人缓存

2026-10-01 436首次真实执行：selected50条、all50条，HTTP200；保留原始GUID、发布时间、中文摘要、原文与AIHOT归属。第二次紧接运行命中TTL缓存，未重发请求。

- intelligence-hub-upstream-reader.service Result=success、ExecMainStatus=0；timer已启用，实查下一次2026-10-01 06:05:09 UTC（北京时间14:05:09），每30分钟继续维护。
- 服务目录/缓存：/opt/intelligence-hub/aihot-private-reader/cache，目录700、文件600，privateOnly=true。该目录不挂载网站容器、不进内容数据库或公开API。无Agent、模型调用、账号操作或通知。
- 本机Python实际TLS超时；采用436实际连通的官方RSS，不改网络/代理配置。
- 3项测试通过：出处/日期、XML/链接拒绝、TTL/ETag/304/失败保留与权限。git diff --check通过，792仓库文件敏感扫描无命中。仅改Python工具/测试、systemd单元和项目说明，无核心/前端改动，无需重跑既有后端套件。

## 待确认的公网范围

新核实AIHOT/terms公开使用规则1.1要求公开镜像、批量公开再分发先书面授权；已异步询问用户有无覆盖intel.muqiao.xyz的授权。尚未得到答复，不开启RSS公网转载，也未发送申请邮件。此前重置镜像也需确认授权，未擅自删除或停用。

Owner：当前Codex。获得授权范围后，可用selected快照/changes游标接入已有发表层，并同步更正与撤选；不能将上游评分伪装为本站模型产出。重置轮询须按上游llms说明改recent日常轮询/完整仅按需，先确认公开授权再调整。新增日报/分类/热点/事件综述按必要范围推进，不做整站复制或全文扩权。
