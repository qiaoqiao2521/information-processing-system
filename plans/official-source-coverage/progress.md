# 当前进度

## Current

官方覆盖修复已在436生效，发布版本`aihot-cf8f8d0-0b8e629ed326`。后续用户要求本地mcode加工新闻、回传436，接续见`plans/local-mcode-processing`。

## Done

- 新增Google Gemini、Anthropic news、Claude blog，当前121来源。六个官方源采集成功；新增21篇（Google5、Anthropic8、Claude8），原有3个官方源无重复新增。
- 已入库未公开的OpenAI53、DeepMind61、Research60篇补索引；没有伪造AI分数/日期或加入精选。
- 公网pool搜索返回Gemini4Argon、ClaudeGovernment、Sonnet5.5和OpenAI模型蒸馏攻击文章，均保留真实来源/日期和待AI处理标记。
- 空库后端194/194通过；最初复用旧测试库192/194，两个失败由已有数据影响告警/报告窗口，换独立新空库后通过。构建类型/网页/16项网页测试通过。
- `PROCESS_HISTORY_ENABLED=false`已配置；官方补采没有模型或Jina调用，24小时实际尝试llm300、Jina2，未扩大旧预算。

## Delivery / Next

当前版本`aihot-cf8f8d0-c21af6422385`、415文件manifest已与运行镜像核对，公网同一版本。三家此前新闻由本地自家mcode加工；用户更正为OpenCode内MiniMax，当前入口已改且一篇新Claude博客真实加工成功，见本地加工计划；源码版本回源Git。原API模型日限额仍300但消费者暂停，Jina50/X-only，其他付费采集0。后续自然定时采集按原脚本继续，不创建Agent定时任务。
