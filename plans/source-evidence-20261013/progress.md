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

公众号仓库已推送qiaoqiao2521/xueyu-gongzhonghao的codex/wechat-make-redesign-20261012：efa5b92（功能）、291454c（离线隔离附件解析）。信息系统本轮成果提交推送至既有eval/fusion-clustering-quality，完成后核对远端ref，不修改仓库可见性或主分支。

## 运行边界与接续

未部署436；未生成真实模型报告或新草稿。旧冻结来源、回执、账本与批准不迁移、不重签。生产接续owner为根Codex：部署本轮匹配代码后，使用新的报告素材包analysis_request:true做独立运行身份的验收；真实模型分类质量与投递结果另核对，不能用本次离线通过代替。

## 知识收尾

already_covered：Wiki/自动化开发范式与智能体协作.md的“按当前任务选择验收依据”和“内容质量与交付保真分开判断”已覆盖此次采用的方法。本轮复用引用对应、模型判断和交付保真分别验收的原则，未修改共享知识页或Codex记忆。
