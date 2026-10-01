# 已核实

2026-10-01再通过436读取https://aihot.news/terms：公开镜像、换皮站、批量公开再分发或持续数据供给替代服务要求书面授权；只摘要、免费、测试不替代授权。用户明确要求审批后放公网站点，不声称已取得上游授权。

现有adminHandler提供登录与CSRF；publication/publish.ts的publishArticleTx可在业务事务中原子发布；manual override支持relevance=pass而不造analysis/模型评分。服务镜像以UID1000运行，不能直接读取root700缓存，故仅导出有界审批材料到独立700/600目录并只读挂载API，原私人缓存不公开挂载。


- 仅退出近7天/200条材料窗口不证明撤选；投影单独保留明确remove记录，reconcile只处理明确remove或hash变化。
- 本地OpenCode steps=1可能把“处理状态：代理最大步骤”等前言混入结构化analysis。只过滤该已知前言，不动引用/其他分析，原始回答留回执；提示词v2要求面向读者并把待核实缩至3点。
- 初次全套测试把模型总阀设false，导致本应请求本地stub的既有测试失败；按测试实际契约在全新隔离库启用测试模型调用，无生产密钥，200项通过。隔离环境仍关闭采集与通知。
- smoke以http://web:3000调用MCP被既有canonical-host保护拒绝；改用正式https://intel.muqiao.xyz，全部检查通过，未弱化Host保护。

- v2真实回答把uncertainties写成3项数组；增加仅模型输入的列表→逐行文字规范化，编辑/API存储仍是字符串。回执327的userHash与当前材料一致，按新schema恢复已收到回答并保存draft，审计保留原格式失败，不重新付费请求。实际总2次请求。
