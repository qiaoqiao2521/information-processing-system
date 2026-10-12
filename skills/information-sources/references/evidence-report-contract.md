# 引用定位与报告提取

## 复用对象

沿用 `claims/documents/provenance`，正文留在 `body`，写作角度留在 `editorial_brief`。不建第二份来源数据库。不把摘要、作者建议或本文推演混入原文。

校验实现在 `xueyu-gongzhonghao/automation/daily-wechat/source_evidence.py`，由既有 writer → 独立内容复核流程调用。离线 CLI 只读取已有 JSON，不调用模型、发布器或任务系统。旧 acquisition 的 Jina/Firecrawl stub 因缺预算接口已禁用，即使提供key也不执行；现行有预算的采集器保持原状。

## 正文与定位

- `body_sha256`：原文 UTF-8 字节的 SHA-256。提供后必须相符；结构化新包要求所有 document 声明它。历史缺 hash 包只输出缺口，不重签旧运行。
- `full_body_file/full_body_sha256`：包目录内相对路径及原始归档字节 hash。校验拒绝目录穿越、外部符号链接、缺失或篡改；导入运行时复制到隔离目录 `.source-archives`，不覆盖已有文件；离线检查也读取该目录。已有内嵌 `full_body` 继续校验 `full_body_sha256`。
- `body_span: [start, end]`：零起点 Unicode 字符范围，左闭右开。不是 PDF 字节偏移。
- 引用报告为每份文档、每条引用分配包内编号 `s1/c1`，输出原文位置及 Markdown 正文位置、行号与绑定 hash。
- 原文只匹配窄范围的空白、引号、PDF 英文断词和原有强调格式；数值、型号、负号与 TeX 不做近似匹配。
- 多处相同引文输出全部候选并标 `ambiguous`。人工消歧可提供 `location: {body_sha256, body_span}`，两者必须匹配冻结原文。

选读 `pdf_pages` 只说明证据范围，不能推出某句在第几页。生产者若知道位置，添加与实际正文一致的映射：

```json
{
  "evidence_segments": [
    {"start": 0, "end": 160, "page": 7, "body_sha256": "<body_sha256>"},
    {"start": 160, "end": 320, "page": 8, "body_sha256": "<body_sha256>"}
  ]
}
```

转写片段可用 `start_seconds/end_seconds` 替代 `page`。映射覆盖整条引文才显示页码或时间段；未覆盖、未提供时保留 `null`。OCR 可信度、来源语言、选读范围及不完整性保留在原 packet/provenance，不从已有摘要推断。

## 结构化提取

来源包显式设置 `analysis_request: true`，既有作者在同一次响应中增加 `source_analysis`，最多20条。独立复核检查分类和依据，无新增模型轮次。

每条沿用 `claim/url/evidence`，另有：

| 字段 | 规则 |
| --- | --- |
| `kind` | `fact` 来源报告的事实；`author_recommendation` 作者建议；`obligation` 明确义务；`exception` 条件或例外；`analysis` 本文推演 |
| `modality` | `reported/may/should/must/unknown`；保留可能性与限定条件，不把 should 升为 must |
| `owner` | 对应 evidence 中明确出现的原文责任人；否则 `null` |
| `due_date` | 对应 evidence 中明确出现的原文期限；否则 `null`，不自行换算 |

未提及的类别不凑数。本文推演引用的是推演依据，不能标成作者结论。建议/义务缺责任人或期限会标 `needs_review`；报告固定 `creates_tasks: false`。任何外部任务创建属于另一个明确授权动作。

## 输出与缺口

- `citation-report.json`：引用清单、正文及原文位置、缺证据、未匹配正文、歧义、PDF页码/视频时间戳未定位与无已定位 claim 的段落。
- `structured-report.json`：五类记录、引用编号与未知字段，绑定同一冻结 packet。
- 错文档、缺引用、原文不存在、hash不符、伪造位置或责任人/期限阻断当前候选；缺页码、歧义、正文概述未逐字匹配只报告缺口。
- `valid` 只证明声明的文本引用对应，不证明语义蕴含、事实真伪或全篇引用完备。语义分类与引用支持关系仍由既有独立复核判断。
- 报告与候选一起 hash 绑定、归档；拒绝稿保留错误报告。不得把报告写回冻结原文，不得修改历史模型回执。

## 借鉴来源

编号、引用清单、缺口报告与分类提取参考 NousResearch/hermes-agent 的 `grounded-citations` 1.2.0、`document-to-action-items` 0.1.0，固定快照 `eefdfe0692207a7520b3a8c764fe510024f552a1`（技能许可证 MIT）。实现扩展现有公众号校验，不复制英文分词门槛、Hermes运行时或任务创建步骤。
