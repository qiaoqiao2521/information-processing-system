# 当前事实与边界

## 上游

AIHOT commit `cf8f8d07d68dfa9079becc72b0717a45b33485f3`，MIT。Node 24 / PostgreSQL / Fastify / React Router SSR / pg-boss。上游18个示范源不是生产信源全量。源码快照已保存在 vendor/aihot；保留 LICENSE 和 UPSTREAM.md。

处理：网址/内容身份判重 → 原文提取 → 预筛 → 两次独立评分（T1=60,T1_5=65,T2=76）→ 中文摘要/理由/分类事实 → SAME_OCCURRENCE / SAME_STORY / UNRELATED / ROUNDUP 归组 → 按独立来源计事件热度。48小时窗口、24小时半衰期。模糊归组需复核。全部公开出口同读 publication/；历史回灌不计今日热度。

## 本地与436

旧站为 Python+JSON 快照，89 AK OPML订阅，乔木只抓AI池前3个，其余自定义采集器。当前仓库已有此前技能/网页/维护代码遗留变动；保留并按比例审阅，不盲目覆盖。

436 Docker Compose可用，约5.2GB可用内存、60GB磁盘；旧站8080，Paperclip3100、其他业务端口保持。专用隧道 e91b6f25-0892-41f5-a1de-edb59870d5f6 / cloudflared-intelligence-hub.service。

108 RSS（示范源+89 AK+当前乔木3个，重复URL合并），8个外部源和2个RSS存量源，共118；hub-x/hub-rss/hub-ak-rss停止自动采集。默认不展示/分发全文。

## 模型

现有本地环境的中国区API，MiniMax-M3，OpenAI兼容接口单次真实请求成功：178 total tokens / 6 completion tokens。密钥经SSH stdin落在436私有.env，未写入代码/参数/聊天。用户先批准限量验证，随后明确批准连续24小时最多300次请求，8次/分钟、60次/小时；其他付费服务预算0、通知关闭。请求次数包含重试，完成回执可复用；到限额后队列等待，不追加付费额度。

两篇Latent Space完整正文材料经过真实双次评分、中文摘要、事实抽取、事件归组与综述，分别55、67分，均未达T2的76分门槛，只进入全部动态。12次真实模型尝试完成这次限定验证；分钟预算曾实际阻断继续调用，窗口恢复后复跑利用已有回执完成。没有为填充精选下调门槛。两个验证事件均为单一来源，不代表已用真实跨来源样本验证合并质量；embedding未配置。

一个OpenAI网页无法直接提取，且Jina无key，停止在正文提取阶段，未冒充全文分析成功。已有RSS全文可正常加工；此主机的带key Jina分支仍未实测。

启用后首轮108个RSS：104成功、4个degraded（johndcook.com、derekthompson.org、joanwestenberg.com、paulgraham.com）。失败订阅保留配置，旧站迁移资料仍在，不伪造成功时间。Worker的首小时模型请求到60次后暂停，实际预算门禁生效。

## 本次改动

行业品牌/信源/模块开关；external推送增加摘要与正文有界字段（原接口仅标题，模型无法利用旧采集正文）；存量经 editorial_overrides发布，无伪造 analyses/分数；复跑不改已存在数据。关闭模型时worker保留任务排队，不消费成无意义失败重试。旧query+hash链接映射到items页；自定义采集由2小时静默timer推送，原RSS不重复跑。

采用 CapMesh PIT-003/PIT-005/PIT-006 约束：不入库运行态，角色配置分离，只切专用隧道origin，实际公网验收。评分Prompt及门槛保持上游标准，暂无用户标注集，未宣称个性化校准完成。

手机验收发现`components/shell/nav.ts`的MORE_PATHS只是底部导航高亮列表，`routes/more.tsx`独立渲染入口；已补齐实际阅读工具行。仅修改前者不能提供手机导航入口。
