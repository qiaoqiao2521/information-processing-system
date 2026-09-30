# 当前进度

## 当前优先状态：OpenCode入口更正

用户指出目标是OpenCode里的MiniMax；前次工具理解错误已更正。当前版本`aihot-cf8f8d0-c21af6422385`已部署，运行镜像415文件hash与本地全部相符；源码回源当前分支Git记录。

- 本地OpenCode1.18.30，固定`minimax-cn-coding-plan/MiniMax-M3.1-Flash-Preview`；真实文本与JSON验证成功。入口`python3 tools/aihot/local_opencode.py --next 3`，或明确文章ID。
- 6项Python适配器测试通过，空库完整后端198/198通过（独立opencode/mcode服务预算与回执均验证），构建类型/网页/16项网页测试与30项公网smoke通过。
- 真实Claude博客材料`vei23wpv6idx97uss3p3ti5g5`完成analysis70，local-opencode，两次59/54、显示56分、非精选进入全部动态；6次CLI调用、6个completed回执，中文摘要79字，建立fact11/story11与综述。公网API/详情HTML200，发表日期仍2026-09-30T00:00:00Z，无待AI处理标记。
- 回执完整模型名为minimax-cn-coding-plan/MiniMax-M3.1-Flash-Preview，transport=stdio-opencode、temperatureApplied=true。末次真实格式验证覆盖辅助模型固定3.1与自定义会话标题，工具全部deny、步骤1、分享disabled、外部插件关闭。
- 旧API尝试仍300、Jina2、自家mcode17；新opencode6独立计数。原17次mcode有效结果保留来源，不重算、不改成OpenCode记录。
- 436原API模型消费者继续暂停，采集继续；root OpenCode只有智谱认证、agent436无认证，均未配置MiniMax Token Plan。不复制本机密钥，不变更服务器其他工具默认配置，不加Agent定时任务或通知。

当前Codex完成审阅并串行提交推送；后续使用OpenCode入口，原入口只作兼容/回退。预算保持保守opencode300/24小时、8/分钟、60/小时、单次默认40；不声称已核实无限额度或精确原API采样等价。

## 前一版已完成状态（MiniMax自家CLI）

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
