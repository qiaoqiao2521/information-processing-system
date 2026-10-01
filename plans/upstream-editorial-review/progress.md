# Current

工程已完成并部署436，真实本地OpenCode稿件version3待审，引用/加工/审批流程可用。Owner：当前Codex。

# Done

- 0039增量表、后台/admin/reviews列表和引用对照编辑页、版本/来源hash校验、管理员登录/CSRF、审计、审批/退回；原文去重，不覆盖已有独立来源文章。
- 审批通过在事务中写入文章/override/publishArticleTx，公开层共享；来源更正/明确撤选撤回，退出近期窗口不撤回。模型分数保持null，人工精选另记。
- 私人投影700/600、UID1000，只读挂载API；原始缓存仍不挂载。30分钟reader/reconcile Result=success，下一次实查北京时间15:48:09（当时快照）。
- 型检、构建、前端16项、后端200项（全新隔离数据库）、Python12项通过。隔离Playwright实测登录、编辑保存、审批发布200、退回404；未审批404/匿名后台401，移动390px无横向溢出，无pageerror。截图仅临时验收产物。
- 436正式health、匿名后台API401、页面302跳登录、公网站点完整smoke（含MCP）通过。旧镜像/override/源码备份保留。
- 一篇真实素材ed0fkjtzo2sbnpzqlara60ghs（ChatGPT Sites/MCP相关X转述），本地OpenCode MiniMax 3.1单次真实请求返回成功，回执326 completed，生成draft/version2，未建公开文章。未声称该X说法已由官方核验。

# Remaining

最终镜像9b853e13ed42、release=aihot-review-9b853e13ed42已上线，health正常；匿名后台401，未审批公开文章404，timer active。v2提示词/前言过滤以及模型列表规范化通过追加行为测试和型检/构建/16前端项。第二次真实模型回答因uncertainties数组被旧schema拒收，已修复为最多3项列表→逐行文字；在输入hash匹配下恢复回执327的已收到回答，没有第三次模型请求。回执327 completed并保留原格式错误/恢复审计，最终draft/version3，analysis3段、待核实3行，共2次真实调用。10个变动运行时代码/迁移文件与本地SHA256全部一致。代码提交推送收尾。实际发稿由用户在后台审阅点击通过；上游书面授权仍无记录，已向用户说明并如实保留其选择，未代其申请授权。
