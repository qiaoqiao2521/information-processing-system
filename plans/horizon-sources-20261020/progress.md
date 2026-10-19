# Progress

## Current

三类来源适配已部署436。HN和GitHub真实采集、入库、模型产出及LifeGame读取通过。OSS Insight上游明确不可用，当前没有可验收榜单；原两小时任务继续检查恢复。

## Done

- 已确认现有bridge timer正常，五个受影响维护程序与本地一致。
- 已实测OSS Insight不可用，按上游明确声明处理，不制造替代趋势。
- 首轮HN8条讨论/21评论、GitHub6条发布说明；新增13条，1条与历史身份重合。旧发布按原日期归档，未伪装为今天的新版本。
- 六条官方发布建立原始待处理索引。4条完成真实OpenCode MiniMax3.1加工并独立对照原材料：Cairn讨论、Transformers5.20.2、Timestral讨论、SGLang0.5.22。前三条未精选但可在全部动态阅读；SGLang74分，作为已有story54的新事实171保留。
- 首条Ask HN样本的understand回执2330为unknown；原生CLI记录确认finish=length、reasoning31999、最终输出0，保留该回执，未自动重发。其余预筛/评分回执仍在。
- 查官方MiniMax文档及OpenCode1.18.34实现，确认该provider为@ai-sdk/anthropic。新闻专用agent显式effort=low；严格拒绝length、工具和多步回答。低档位两条实采材料完整跑通，共13次CLI调用，包含每分钟限速等待。全轮三批共30次调用，共享原300/24h预算。
- 修正采集正文trim与hash表示不一致，两条元数据经原快照比对和CAS修复，原值另存；独立数据库回读13条hash全匹配。
- Python43项、全仓TypeScript检查、MJS语法通过。LifeGame相关Flutter16项和analyze通过；真实公网列表/详情经Dart客户端与Godot解析器通过。列表只含来源名称，稳定source ID从详情读取。
- LifeGame0.4.27/code4028 ARM64签名包已交付/home/muqiao/下载/LifeGame.apk；原签名、包名、版本、ABI和16KiB zipalign通过。SHA256 be783cc91f96e43d73edce510492fb7dc289d9ddafb3022949992042f2126441。旧包归档保留，未执行真实手机安装验收。
- 维护release为20261020-horizon-sources；采集timer沿用。API/worker常驻模型开关仍false。发布助手由宿主通过stdin执行，避免容器重建丢失docker-cp脚本。未重建网页镜像，回退入口见deploy/aihot/README.md。

## Remaining

- OSS Insight数据可用性取决于上游事件采集恢复；既有bridge每两小时检查，无额外Agent或通知。
- unknown样本留待显式处理，不自动重放。手机实际安装与个人使用由用户验收。

## Knowledge

already_covered：Wiki「自动化开发范式与智能体协作 / 按当前任务选择验收依据」覆盖分层验收，本批具体状态保留本计划。

pending：MiniMax3.1默认max思考导致length的具体经验已留findings。候选目标Wiki/工具链与认证体系.md；该页及开发知识入口已有未提交修改，归属尚未核实，本轮未并行改共享Wiki。接续owner根Codex，先核对已有改动，再将本批官方依据和适用范围整合原页。
