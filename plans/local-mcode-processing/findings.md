# 已核实发现

- 本地CLI为`~/.minimax-code/bin/mcode`0.5.9，当前终端PATH未加载；无需重装。真实无工具请求成功，模型MiniMax-M3.1-Flash-Preview，账户使用minimax-managed。
- 官方CLI支持`exec --input - --model --permission off --max-steps 1 --output-format json`。JSON最终回答可能带代码围栏，AIHOT原有extractJson支持。
- CLI每次加载自身系统上下文，最小验证输入约13kToken；不能将CLI次数等同于短API请求成本，也未证明无限额度。
- 共用数据库通过原有远程后端提交，避免复制数据库或重写评分引擎。SSH stdio无需反向隧道/新增HTTP服务，CLI凭据留在本机。
- 普通worker在`MODEL_CALLS_ENABLED=false`时不消费内容/事件模型队列，已采集内容保留；本地入口只为自己的独立进程启用模型调用。
- 本地mcode提供独立服务回执与300/连续24小时保守上限，单次默认40，不修改原llm/Jina预算。
- CLI不暴露temperature/max_tokens，不应声称与原API采样设置等价；回执记录samplingParametersApplied=false。Prompt、门槛和双次独立评分保留，未声称评分已校准。
