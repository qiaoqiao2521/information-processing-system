# 引用定位与报告结构化交付

## 已完成

- 修正information-sources的示例、优先级、矩阵与项目路由；普通网页/GitHub/PDF不再走Jina。旧适配器评估明确标为历史。
- 遗留预处理器移除Jina/Defuddle兜底与伪装请求头；PDF保留提取缺口，arXiv摘要明确不等于全文，X旧路径不发请求。
- 旧acquisition的Jina/Firecrawl stub禁用，即使有key也不发请求；默认recipe优先直取原文。现行有预算的采集器未改。
- 公众号复用claims/documents/provenance，输出包内引用编号、原文与正文字符范围/行号、hash绑定、位置歧义及缺口报告。页码/时间戳要求绑定正文的完整片段映射，未知保持null。
- analysis_request:true的来源包在同一次作者响应中返回五类source_analysis；现有独立复核检查分类、证据支持和责任人/期限。没有依据的字段为null，不创建任务；不新增固定模型轮次或调用上限。
- 两份报告进入批准候选hash绑定和归档；机械拒绝也保留缺口报告。附件只复制到.source-archives，离线CLI可读同一目录，不能覆写输入或附件。

## 验收

- 公众号184项通过：source_evidence、runner、pinned_runner、quality_workflow、daily_maintenance、source_documents、topic_sources。
- 信息系统27项通过：6项information-sources技能测试，21项acquisition_orchestrator/pipeline_fixes/quality_reliability_evaluation。
- CLI真实执行以冻结测试素材验证成功/非零失败和运行包附件解析；流程模型与微信为测试替身，无真实模型调用、任务创建或草稿写入。
- 文档相对链接检查通过；保留原技能CRLF，用git core.whitespace=cr-at-eol检查diff，公众号普通diff检查通过。

## Git交付

公众号仓库已推送qiaoqiao2521/xueyu-gongzhonghao的codex/wechat-make-redesign-20261012：efa5b92（功能）、291454c（离线隔离附件解析）、17206a3（原生nullable类型修复）。信息系统代码ef04066已推送既有eval/fusion-clustering-quality，并核对远端ref；部署与真实验收记录沿用原分支交付，不修改仓库可见性或主分支。

## 运行边界与接续

首轮交付时未部署436、未生成真实模型报告或新草稿。随后用户授权补齐部署与真实模型验收，记录见下节。旧冻结来源、回执、账本与批准不迁移、不重签；本次报告验收没有微信草稿写入或外部任务创建。

## 2026-10-13生产部署与真实模型验收

- 连接：Tailscale 100.74.111.55的SSH管理入口，root部署，agent436运行模型；网络、账户及已有预算配置未改。
- 公众号生产工作区：`/srv/self-media-exchange/inbox/xueyu-gongzhonghao-receive`，代码17206a3；新增nullable输出校验修复已推送。原有两个未跟踪脚本保留。
- 信息源维护目录：`/opt/intelligence-hub/maintenance/releases/20261013-source-evidence`，source-evidence-package.json绑定ef04066及20份文件hash。current原子切换；data继续引用原20261009版本数据目录，既有采集器未替换。previous_release记录可回退入口。
- 本机202项公众号相关测试通过，包含18项原生模型接收端测试；436的78项相关测试和6项路由测试通过。远端模块导入及20份文件hash核对通过。公网`/api/health`返回ok/db ok，前端release保持既有版本。
- 新运行：`/srv/self-media-exchange/outbox/wechat-daily/editorial-source-evidence-20261013`。使用既有Google官方博客归档和116页技术报告的物理页17、29、32、33。原PDF SHA256为1205f537b2bd644db7fb04dbe015356e48739cd8bde624a45a021d07101845a6；重新提取选读页，建立完整字符范围与页码映射。
- 真实首版：AGY回执确认gemini-3.8-flash-medium/实际wire gemini-3.8-flash-n、一次原生生成、正常end_turn；独立MiniMax-M3.1-Flash-Preview由实际HTTP请求/响应确认，单次请求、正常end_turn。提取5条fact、2条author_recommendation、1条analysis；未强造义务或例外，8条owner/due_date均null，建议标为needs_review，creates_tasks:false。
- 首版程序报告有效，5条原文定位成功，但5条正文定位缺失。原稿、两份报告、验收结果和状态留在`acceptance-candidates/first-real`。同一账本内追加引用claim对齐，正文、标题、摘要、结构化记录与检查要求完全不变。
- 对齐完成，第二次独立复核通过，状态report_pre_review_passed；两次作者、两次复核各有独立原生会话，四次调用均completed。最终5条claims同时定位正文与原文，4条PDF引用的实际页码为32、17、32–33、32，另一条来自博客。正文hash仍为2fa32b3326794da940f4d33e11b41f5206b649e693a9402391e3b7bfbde76f2e。
- 原生回执、回答hash、prompt hash、source/criteria hash、附件hash及最终产物hash均独立重算读回一致。两次AGY均正常结束且无工具步骤；两次MiniMax均严格单次实际HTTP请求、正常结束且无工具步骤。离线CLI在这份真实包上执行返回0，结果与运行报告一致。
- 仍有16处paragraph_without_located_claim，独立复核保留2条非阻断建议（行业共识措辞、情境规范与法律合规的区分）。按现行规则通过，不宣称全篇引用完备、全116页覆盖或生产日常三篇均交付。没有视频输入，真实时间戳正例未覆盖。
- 验收产物整理到本机下载目录`source-evidence-acceptance-20261013`，只含正文、文章JSON、引用/结构化报告和结果说明，不复制认证、原生会话或运行日志。本次未写微信草稿、未发通知、未创建外部任务。

## 知识收尾

already_covered：Wiki/自动化开发范式与智能体协作.md的“按当前任务选择验收依据”和“内容质量与交付保真分开判断”已覆盖此次采用的方法。本轮复用引用对应、模型判断和交付保真分别验收的原则，未修改共享知识页或Codex记忆。
