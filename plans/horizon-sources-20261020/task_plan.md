# Horizon 来源接入

## Goal

将 Hacker News 讨论、GitHub Releases、OSS Insight 趋势接入436既有采集、加工 workflow 和 LifeGame 读取链路。用户于2026-10-20接受这三类来源。

## Scope

- HN官方API补评论，保留讨论身份、作者、时间与出处。
- GitHub官方API订阅现有AI开发领域的发布说明；保留Claude/Codex既有采集。
- OSS Insight官方趋势接口，数据不可用时保留旧快照，不伪造榜单。
- 复用两小时bridge、external摄取、OpenCode预算和公开读取接口。补LifeGame来源目录。
- 不新建采集时钟、账号或通知，不启动X/Google，不调整评分门槛。

## Steps / Acceptance

1. 核对现场与本地基线、官方接口和已有适配。
2. 实现有界采集与元数据传递，检查故障保留旧快照、去重和日期。
3. 部署增量到436，核对运行文件指纹和真实入库。
4. 有界真实加工并读取LifeGame相同pool接口；来源故障独立报告。
5. 完成相关检查、回退说明、提交与推送。

## Status

实现、部署与读取验收完成。OSS Insight仅完成适配和不可用状态验收；上游恢复前没有真实榜单。未完成的模型样本保留，不自动重发。
