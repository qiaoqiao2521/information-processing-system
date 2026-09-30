---
name: ljg-paper-flow
description: "Compose LJG paper interpretation and visual cards when both outputs are requested. For each paper, apply ljg-paper to produce Org analysis, then ljg-card to render that analysis. Use for 论文流, 读论文并做卡片 or paper-analysis-plus-card batches; reading alone uses ljg-paper."
user_invocable: true
version: "1.0.0"
---

# ljg-paper-flow: 论文流

读论文 → Org 解读 → PNG 卡片。此处只定义编排和产物交接；精读方法由 [ljg-paper](../ljg-paper/SKILL.md) 定义，视觉模具和品味由 [ljg-card](../ljg-card/SKILL.md) 定义，不复制它们的标准。

## 参数

| 流程参数 | 传给 ljg-card | 产物 |
| --- | --- | --- |
| 无 / `-l` | `-l` | 长阅读卡 |
| `-m` | `-m` | 多卡 |
| `-c`（本流程旧别名） | `-m` | 保留旧“多卡”含义，不直传 |
| `-i` | `-i` | 信息图 |
| 用户明确指定漫画 | `-c` | 漫画 |

`ljg-card -c` 的含义是漫画，而本流程旧 `-c` 表示多卡；必须按上表转换并在交付时说清采用的模具。

## 执行

1. 提取用户明确提供的论文链接、PDF 或论文名称。仅名称无法唯一定位时先确认论文身份。
2. 对每篇读取并应用 `ljg-paper`，获得实际生成的 Org 路径。宿主有技能调用工具时可调用；否则读取链接入口并执行，不要求特定的 “Skill tool”。
3. 读取已完成的 Org，把它作为 `ljg-card` 的输入；使用转换后的模具参数，获得实际 PNG 路径。不要在卡片阶段重新从原论文生成另一套解读。
4. 多篇之间可在宿主容量内并行；单篇内部必须先解读后成图。没有子代理时顺序完成同一流程即可。
5. 汇总每篇论文的标题、Org 路径和 PNG 路径。某一步失败就保留已有产物并报告该阶段，不把整批标成完成。

## 边界

- 只读论文的请求直接由 `ljg-paper` 完成。
- 已有解读只要 PNG 时直接使用 `ljg-card`，不重跑论文分析。
- 复用当前任务中已经确认的解读与卡片；版本或来源改变时才重新生成必要阶段。
- 原子的质量红线、个人方法和品味不变。流程不另定义 Org 结构或视觉规范。
