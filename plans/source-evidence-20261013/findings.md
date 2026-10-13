# 已核实缺口

- 项目约定 Jina 仅用于既有 X 正文，路由技能与遗留预处理器仍将其用于网页、GitHub、PDF。
- 遗留预处理器含伪装浏览器、Google Referer 和 X-Forwarded-For；没有接入当前 X 预算。移除该绕路入口。
- 旧 acquisition 注册表仍可直接选择 Jina 和 Firecrawl stub，缺现行预算/白名单。保留账本名称但禁用这两个适配器；默认 recipe 移除它们并优先原文直取。现行有预算的 X Reader 和批准 Firecrawl 采集器保持原状。
- 现有公众号校验已将每个 claim 的 evidence 对照对应 document，并校验已声明的正文 hash；尚未输出位置及缺口清单。
- 来源包支持附件、证据范围与选读页码，但选读页码不能推出具体引文页码。位置必须来自绑定正文的 evidence_segments。
- 借鉴 Hermes grounded-citations 1.2.0 与 document-to-action-items 0.1.0 的编号、引用清单、缺口报告和类型区分。快照来自 NousResearch/hermes-agent 的 eefdfe0692207a7520b3a8c764fe510024f552a1；不安装其运行时，不复制英文分词门槛或建立新账本。

## 436真实入口检查

- 原生模型输出校验器只接受单一type；新owner/due_date使用string/null联合类型，实际会抛出`TypeError: unhashable type: 'list'`。已补窄范围nullable支持和真实接收端回归，保留错误类型拒绝。
- 436公众号工作区原HEAD为bdd155f，只有fix_claims.py、validate_claims.py两个未跟踪文件。在既有运行锁内用Git bundle快进到17206a3，保留两文件；模型使用agent436普通用户。
- 信息源维护目录只含既有采集器，新增acquisition模块必须包含包初始化所导入的orchestrator及其依赖。暂存检查先发现缺失，旧current未切换；补齐、导入及文件hash核对通过后才切换。
- 真实首版5条引文均能定位原文；claims采用概述，5条正文定位全部缺失。缺口报告如实记录，独立复核通过不代表正文定位已完整。追加同账本内的引用元数据对齐，保留首版，不改正文或结构化记录。
