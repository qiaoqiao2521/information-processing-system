# Findings

- Horizon参考修订：0eda588fb0486a4b183bb3c613d6f20548514505。借鉴采集与上下文组织，不引入第二套调度或评分系统。
- 436经现有Tailscale SSH别名racknerd-436b0c0连接。maintenance/current实际为20261013-source-evidence；本批五个既有程序与本地逐字一致。
- HN旧采集只有RSS标题/链接；CLI发布仅覆盖Claude/Codex。external摄取原生支持bodyText与raw。
- OSS Insight真实响应data_quality.status=unavailable，说明GitHub事件采集量降至基线约0.3%，无法计算趋势排名。rows=[]不代表零热门项目。只接入诊断与后续恢复入口，不能宣称榜单实采通过。
- LifeGame电脑和手机共用/api/site/pool；手机信源矩阵使用静态目录，需补新source ID。个人数据与生活记录分离，保持无新增账号。
- 采用Wiki「按当前任务选择验收依据」：分别核对采集、入库、模型产出和读取端，不以配置/退出码代替完整验收。
- 真实入库发现两个正文hash与数据库不符，原因是ingest明确trim正文，而初版适配对未trim文本计算hash。已统一为trim表示并补回归；两条现场元数据经原快照逐字trim比较及CAS修正，原hash另存，修正前raw保存至回退目录。未更改正文或模型评分。
- 首轮436无子请求失败：HN8条/21评论，GitHub6条；13条新增，1条与历史身份重合。六条官方发布已建立原始待处理公开索引，旧资料仍按原日期归档。
- 模型验收区分了调用成功与完整回答：Ask HN的understand请求耗尽31999 reasoning token，finish=length、最终输出0；保留unknown，不因CLI进程退出0接受它。原生opencode db只读查该会话的finish/tokens/model元数据，未复制账号或重发该请求。
- MiniMax官方说明M3.1省略effort默认max，不能关闭thinking，应降低effort：https://platform.minimax.cn/docs/guides/text-generation 。OpenCode1.18.34模型元数据确认minimax-cn-coding-plan使用@ai-sdk/anthropic，agent附加effort选项经该SDK传给output_config。现将新闻专用agent设low，不修改用户全局CLI配置、模型、评分标准或预算。两个新样本正常完整回答通过，不声称模型今后绝不截断。
- LifeGame的pool列表source只含name；详情source才有稳定id。公网验收同时读取列表与详情，而非假设列表包含id，沿用既有客户端契约。
