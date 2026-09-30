# 当前进度

## Current

部署与真实加工已完成。版本`aihot-cf8f8d0-474813e47fab`，415个源码文件在运行镜像内与本地hash全部相符。当前分支的Git记录为源码交付版本；没有长期后台mcode任务。

## Done

- 本机mcode0.5.9实际最小调用、固定MiniMax-M3.1-Flash-Preview结构化输出成功。
- 4项Python适配器测试、3项stdio异常/并发测试通过。
- 新空库完整后端198/198通过，包含本地模型停用预算零发送、独立mcode回执、已保存回答复用；无真实模型API调用。构建类型、网页与16项网页测试通过。
- 独立传输无需HTTP端口/DB凭据；无工具模式固定模型，每次有界，未验证无限额度。
- 三篇真实官方新闻完成，17次本地CLI调用、17个completed回执：Google Gemini4Argon两次79/72、显示75分并精选；Claude Sonnet5.5两次88/86、87分并精选；OpenAI模型蒸馏攻击两次54/39、46分进入全部动态。
- analysis IDs67/68/69，均local-mcode；Google/OpenAI建立事件与综述，Claude按真实旧日期归为historical，不制造新事件热度。没有改发表时间或强制提高分数。
- 三篇公网API及详情HTML均HTTP200，有真实中文摘要、无待AI处理标记。30项页面/API/RSS/MCP smoke通过；此为HTTP验收，未进行新增浏览器视觉验收。
- 436 MODEL_CALLS_ENABLED=false、PROCESS_HISTORY_ENABLED=false、COLLECT_ENABLED=true。原API尝试仍300、Jina2；没有新增API调用、搜索、通知或充值。
- 新CLI回执标记transport=stdio-mcode、samplingParametersApplied=false，未把CLI采样当原API等价。CLI分钟限额前置拒绝后等待60秒，已保存阶段复用，模型失败/unknown不自动重发。
- Python urllib对公网返回403；同一服务器curl与应用smoke、三篇API/HTML均成功，未扩大为Cloudflare配置调整。来源页面采集不受此验证客户端差异影响。

## Remaining

后续按需运行`python3 tools/aihot/local_mcode.py --next 3`（最近官方内容）或明确文章ID（任意已有源）。本机离线时原始官方索引仍公开，其他未加工材料保留队列。常态自动运行未启用；如需改变保守限额或加入本地调度，需新的明确需求。
