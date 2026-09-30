# 已核实发现

## 用户更正：OpenCode MiniMax

- 当前目标Provider为`minimax-cn-coding-plan`，模型`MiniMax-M3.1-Flash-Preview`；本地OpenCode1.18.30的官方auth list确认已有MiniMax Token Plan认证。普通文本与自定义news agent的真实JSON输出都成功。
- 436 OpenCode1.14.48：root只有Zhipu认证，agent436没有认证，两者配置默认GLM5.1；服务器没有可直接复用的MiniMax Token Plan认证。此状态不同于自家MiniMax CLI的1008余额失败，不能混为一谈。
- `--pure`、permission全deny、steps1、分享disabled、只启用该Provider，原生Prompt分别传入system与user，后者经stdin；CLI返回的JSON事件流需要text和stop finish均完整，error/tool_use/不完整流均拒绝发布。
- temperature按官方agent配置应用，max_tokens不保证等价。账号凭据留本地，继续经原SSH stdio回传；opencode独立预算与回执，mcode旧结果保留真实来源。

## 此前MiniMax自家CLI验证（历史）

- 本地CLI为`~/.minimax-code/bin/mcode`0.5.9，当前终端PATH未加载；无需重装。真实无工具请求成功，模型MiniMax-M3.1-Flash-Preview，账户使用minimax-managed。
- 官方CLI支持`exec --input - --model --permission off --max-steps 1 --output-format json`。JSON最终回答可能带代码围栏，AIHOT原有extractJson支持。
- CLI每次加载自身系统上下文，最小验证输入约13kToken；不能将CLI次数等同于短API请求成本，也未证明无限额度。
- 共用数据库通过原有远程后端提交，避免复制数据库或重写评分引擎。SSH stdio无需反向隧道/新增HTTP服务，CLI凭据留在本机。
- 普通worker在`MODEL_CALLS_ENABLED=false`时不消费内容/事件模型队列，已采集内容保留；本地入口只为自己的独立进程启用模型调用。
- 本地mcode提供独立服务回执与300/连续24小时保守上限，单次默认40，不修改原llm/Jina预算。
- CLI不暴露temperature/max_tokens，不应声称与原API采样设置等价；回执记录samplingParametersApplied=false。Prompt、门槛和双次独立评分保留，未声称评分已校准。
