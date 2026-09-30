# 进度

## 当前交付（2026-10-01，北京时间）

- `https://intel.muqiao.xyz/`已切到AIHOT核心；全部动态入口为`/all`。固定上游`cf8f8d07d68dfa9079becc72b0717a45b33485f3`，MIT和来源保留。
- 最新运行版本`aihot-cf8f8d0-c21af6422385`，镜像内415个源文件与本地manifest全部相符；公网`/api/health`返回同一版本。官方覆盖与本地加工详情分别回源`plans/official-source-coverage`、`plans/local-mcode-processing`。用户更正目标为OpenCode内MiniMax Token Plan，现推荐本地OpenCode3.1入口；新一篇真实Claude博客材料6次调用、56分进入全部动态，原17次自家mcode结果保留真实来源。
- 当前109 RSS / 2官方网页 / 10外部及存量源已seed，X和两类RSS存量源不调度。初始108个RSS首轮104成功、4失败，自定义HN/橘鸦/HF/GitHub/Builders五类全部更新、新建13条；后续新增Google Gemini、Anthropic新闻和Claude博客，官方待处理内容也能公开阅读。
- 原MiniMax API预算仍300/连续24小时、8/分钟、60/小时，消费者现暂停；用户改用本地mcode按需加工、SSH回传436，共17次真实调用完成Google75/Claude87/OpenAI46分三篇。独立mcode预算保守300/连续24小时，不迁移账号。Jina仍50/连续24小时，仅X，普通网页回退关闭；其余付费服务0、通知关闭。采集Worker继续运行，历史自动加工暂停，不批量重算存量。
- 桥接`intelligence-hub-aihot-bridge.timer`北京时间每两小时15分运行，原Python维护timer已停止；采集/处理无编码Agent。备份timer每天04:10生成私有本地dump，保留7份。

## 数据与真实加工

- 278条旧站输入，创建241条去重材料；18条无可用原文入口/媒体素材留在旧库，19条跨来源重复。复跑新增0条；旧ID映射保存在数据库，原发表/采集日期不变。
- 两篇RSS正文经真实双次评分、中文摘要、事实、事件归组与综述，分别55、67分，未达媒体源76分，只进入全部动态。限定验证12次模型尝试，重跑复用已有回执；没有伪造精选。
- 原生OpenAI和Latent Space采集先验证新增9条，再启用108个RSS；网页刷新不发模型请求。

## 验收

- 原迁移58项Python回归（含2项AIHOT适配器）、19项相关适配/回灌测试通过。Jina接入后191项完整后端测试通过（含6项新增的范围、正文、回执和预算检查）；测试只用本地替身，不带生产密钥。
- Docker构建执行类型检查、网页构建和16项网页测试；手机入口修复后再次通过。
- 公网smoke：30项页面/API/RSS/站点资产/MCP initialize全部通过。匿名`/api/admin/sources`、`/api/ingest/items`返回401；原`/api/studio/dispatch`为404，未暴露媒体写入。
- 旧`/?source=juya#16986443444576746d74`实际跳至规范`/items/759e0911a1621bb595ec`；搜索Claude返回13条并包含两篇真实加工稿。原文链接、真实中文摘要/55分、按需工具带入原文、切换技能与任务预览均在浏览器验证，未见控制台error。
- 390×844手机阅读、更多菜单、阅读工具可达，scrollWidth=clientWidth=390；验收后恢复默认视口。Chrome共享代理原本已blocked，保留原状，改用无须登录的Codex内置浏览器验收公开站点。
- 模型、摄取和数据库配置仅服务器600私有文件；源码扫描未发现账号凭据。X技能的固定客户端Bearer常量与公开上游相符，不是用户会话。

## 回退与边界

- 旧8080服务、旧release和快照保持；专用隧道origin切到8088，其他隧道未改。回退配置`/opt/intelligence-hub/aihot/rollback/20260930T173949Z`，`rollback-current`指向该目录。首份918642字节数据库dump已生成并通过gzip校验；未做公网回切或数据库恢复演练。
- 评分标准未做个人样本校准，未配置embedding；两个限定验证事件来自同一出版者，不声称真实跨来源合并质量已验证。普通网页无法直接提取时不再走Jina，保持正文未确认。
- 用户选择稍后补充条款与隐私说明；草稿留在本计划，公开页只显示待补充。
- X保持暂停，无Google浏览器访问、无账号复制、无通知。

## Jina接入验收（2026-10-01）

- 密钥在436私有文件中生效，root 600；后端实测普通网址被scope拒绝，无新增回执尝试。
- X条目`8964d495c613d19c2091`取得1210字符原帖正文，回执63为completed，返回1734 tokens；旧摘要/日期/加工状态保留。复跑skipped，不重复请求、不触发模型。
- 搜索源hub-x仍disabled，全文权限仍false；只提供`scripts/read-x-body.ts`按需入口，没有新增X采集timer。
- Jina单次输出上限10000 tokens；日50次与模型日300次独立，其余付费服务0。新worker已恢复；旧镜像保留`muqiao-intel-aihot:pre-jina`标签，修改前源码与manifest保存在`rollback-jina/`，不涉及数据库删除或恢复。
- 436经公网域名的30项smoke全部通过，匿名后台为401；API/web/worker与数据库运行，bridge/backup timers active。本机CLI经过现有网络/代理路径访问超时或403，未用此结果冒充本机浏览器验收，也未修改本机网络设置。

## 仓库收尾

本机`workbench_vault`指向仓外生成目录，原状保留并忽略。其他既有有效未提交网页/11技能/采集/维护变动一并审阅、验证、整合，不覆盖历史成果。既有目标为public的`qiaoqiao2521/information-processing-system`，当前分支`eval/fusion-clustering-quality`，收尾推送保持该分支。提交和远端SHA以Git实际记录为准。

新增项目代码的staged whitespace检查通过；上游原样快照`DayList.tsx`、`HeatChart.tsx`及项目技能原样`cookie-file.ts`存在既有空白告警，已逐字节核对前两者对应固定上游commit、后者对应中央源码，保留原貌。34个本次文档相对链接全部存在；640个待提交文件未包含.env、数据库、日志或凭据存储。

核心与既有有效成果已提交`33df849fb68695f63b882e315fc035f52fd41fbf`并非强制推送到上述分支；GitHub ref读取的SHA与本地完全一致。此后仅补充完成状态和本条收尾记录，不改变已验证部署源码。
