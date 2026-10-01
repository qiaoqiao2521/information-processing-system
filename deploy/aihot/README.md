# AIHOT 核心部署

上游来源和版本见 [UPSTREAM.md](../../vendor/aihot/UPSTREAM.md)。[项目计划](../../plans/aihot-core-migration/task_plan.md)记录当前验收；核心源码在 `vendor/aihot`，行业配置在 `industry`。

## 436 运行布局

- 源码与私密 `.env`：`/opt/intelligence-hub/aihot/app`（配置600 root；不复制认证数据库）。
- Compose：`docker-compose.yml` + `compose.override.yaml`，项目名 `muqiao-intel`。
- 新站 origin：`127.0.0.1:8088`；API/数据库仅内部 Docker 网络。
- 原 Python 站8080、快照与 maintenance runtime保留用于回退。
- 专用 Cloudflare Tunnel继续 `muqiao-info-436`；只切 `/etc/cloudflared/intelligence-hub.yml` 的origin。
- 原生RSS、评分、归组、报表由pg-boss worker调度；自定义来源经 `intelligence-hub-aihot-bridge.timer`（北京时间每两小时15分）进入同一库。无需编码Agent，通知关闭，X不进入timer。

## 构建与检查

```bash
cd vendor/aihot
# 独立设置私密.env，使用 .env.example 作字段参考；不要把密钥放在CLI参数。
docker build -t muqiao-intel-aihot:local .
docker compose -f docker-compose.yml -f ../../deploy/aihot/compose.override.yaml up -d
```

Dockerfile构建时执行类型检查、网页构建及网页测试。后端测试只允许独立 `_test` / `_ci` 数据库，模型使用本地替身。不要把真实模型密钥传给测试环境。

436未安装Buildx，使用`DOCKER_BUILDKIT=0 docker build -t muqiao-intel-aihot:local .`完成构建。源文件manifest放在服务器部署根目录；`AIHOT_RELEASE`与`/api/health`对应实际部署版本。

新部署付费预算默认0；`scripts/muqiao-budget.ts --validate`临时开放最多40次模型尝试。用户已批准436常态使用 `--daily-cap 300 --jina-x-cap 50`：连续24小时最多300次模型请求，8次/分钟、60次/小时；Jina单独最多50次尝试，1次/分钟、10次/小时；其他付费服务保持0。无参数关闭所有付费服务；省略Jina参数也会关闭Jina。`scripts/validate-hub.ts`只接受1–3个材料ID，经真实原文提取、双次评分、公开发布、归组及事件综述，不能冒充批量处理完成。

## Jina：只补已有X正文

密钥保存在436的私密`.env`和`/etc/intelligence-hub/jina.env`（root 600），不得入库或放在CLI参数。部署设置`JINA_SCOPE=x`、`JINA_BODY_FALLBACK=false`、`JINA_MAX_TOKENS_PER_REQUEST=10000`。后端在创建回执之前拒绝普通网页、搜索页、账号时间线和伪装域名，只允许HTTPS X/Twitter原帖链接。

```bash
cd /opt/intelligence-hub/aihot/app
docker compose -p muqiao-intel -f docker-compose.yml -f compose.override.yaml exec -T api \
  node scripts/muqiao-budget.ts --daily-cap 300 --jina-x-cap 50
# 一次只接受一个库中已有的X条目ID；不搜索，不调用模型。
docker compose -p muqiao-intel -f docker-compose.yml -f compose.override.yaml exec -T api \
  node scripts/read-x-body.ts <article-id>
```

Reader返回的是整页；辅助入口只识别与已有摘要匹配的原帖标题正文，丢弃登录提示、评论和推荐。登录/验证页或不认识的格式保持`unconfirmed`和搜索摘要，不自动重试；当天再次调用复用回执。成功补正文仅增加内容版本，保留日期、公开摘要、加工状态和全文权限，不自动重算旧帖。Google/X搜索继续暂停，此入口不加入定时采集。

[Jina官方说明](https://jina.ai/reader/)按输出Token计费，请求次数上限与MiniMax预算独立；`X-Token-Budget`限制单次输出，不能把50次等同于免费。内部预算保守统计实际尝试，失败尝试也占次数。未启用充值或修改账单设置。

## 静默维护

数据库每日北京时间04:10本地备份，文件仅服务器可读，保留最近7份自动备份；不上传云存储，不发通知。先验证的首份备份保留于 `backups/`。

当前新站继续`COLLECT_ENABLED=true`；本地mcode验收后436设置`MODEL_CALLS_ENABLED=false`，暂停服务器模型消费者，保留队列。按需本地会话单独启用模型调用。旧`intelligence-hub-maintenance.timer`已停止，新bridge/backup timers启用。回退配置保存在`/opt/intelligence-hub/aihot/rollback-current`；旧8080服务仍在。

## 订阅与回灌

- `python3 tools/aihot/subscriptions.py`合并89 AK OPML订阅、乔木当前3个及上游示范源；当前109 RSS、2官方网页源及10外部/存量源，总121。
- 首次seed新增信源，复跑不覆盖后台修改。以后订阅在 `/admin/sources`管理。
- `scripts/import-hub.ts public-library.json`保存真实发表/采集日期、无模型分数的旧站摘要和旧ID映射；同网址跨来源只留一个身份，复跑不新增。
- `tools/aihot/bridge.py`推送HN/橘鸦/HF/GitHub/Builders最新材料；文章摘要、正文有界传输，旧抓取失败则保留快照。不会重跑已原生接入的RSS和暂停的X。
- 同一条文章被不同来源发现会留发现记录，重复发现不会制造新文章。
- 默认不展示或再分发原文全文；阅读工具只复制任务，不直接调用模型。

## 官方覆盖与模型等待

OpenAI News、Google DeepMind/Research/Gemini、Anthropic newsroom、Claude博客六个明确官方来源启用`config._aihot.publishPending=true`。采集成功就通过同一公共发布层展示原始标题/摘要和“待AI处理”标记，不写假分数、不入精选、不改变原日期；真实模型判断可替换原始索引，判定block后仍退出公开池。其他来源不自动获得此待遇。

RSS默认按发表时间降序再截断，显式`sortByPublishedAt=false`可保留发布者顺序。436设置`PROCESS_HISTORY_ENABLED=false`，暂停历史自动加工及已入队历史模型任务；资料、原日期、人工按需处理入口保留，模型日额度仍300。

增补部署先运行`node scripts/seed.ts`，再运行`node scripts/reconcile-official-sources.ts`：只为行业包明确启用的官方源补pending标记/最新排序、最长60分钟间隔，并为已入库但未公开的文章建立索引；保留已有URL、选择器等管理员修改。随后强制采集这六个来源检查增量。此流程不需要浏览器登录或Jina，适配器为官方RSS和HTML列表。不要为补齐新闻扩大模型预算。

## 本地 OpenCode MiniMax加工，结果回传436

**当前入口更正为OpenCode**：`minimax-cn-coding-plan/MiniMax-M3.1-Flash-Preview`，本地已有MiniMax Token Plan认证。此前MiniMax自家CLI的登录与余额不是此Provider的证据。436的agent436 OpenCode没有凭据，保留本地调用与SSH回传，不复制密钥。

```bash
cd /home/muqiao/projects/information-processing-system
python3 tools/aihot/local_opencode.py --next 3
# 任意已有来源可按文章ID加工，最多10篇。
python3 tools/aihot/local_opencode.py <article-id>
```

OpenCode关闭外部插件（`--pure`），临时news agent单步、全部工具deny、分享disabled，只启用minimax-cn-coding-plan。系统Prompt进入agent.prompt、用户材料经stdin；temperature应用，max_tokens未保证等价，回执如实标记。独立`opencode`预算8/分钟、60/小时、300/24小时，默认单次40调用；原API与Jina不变。原mcode通道和已完成记录留作兼容/回退，下述旧入口不再作为推荐。

### 原MiniMax Code兼容入口

仓库已有本地完整源码，无需复制数据库。436保持采集、数据库与公网发布；本地启动一次SSH处理会话，远端原生流程把模型Prompt通过stdio传来，本机官方mcode返回回答。评分/摘要/归组和回执仍由同一后端提交。两个阶段并发时以请求ID匹配，不按响应先后顺序关联。

```bash
cd /home/muqiao/projects/information-processing-system
# 只处理最近7天尚未加工的官方内容，最多3篇。
python3 tools/aihot/local_mcode.py --next 3
# 或明确指定已有文章，最多10篇；默认每次最多40个CLI调用。
python3 tools/aihot/local_mcode.py <article-id>
```

本机CLI默认 `~/.minimax-code/bin/mcode`，模型固定 `minimax/MiniMax-M3.1-Flash-Preview`，每次独立临时工作目录，`--permission off --max-steps 1`。只支持文本，不复制浏览器登录态、不导出CLI密钥、不开放HTTP端口。CLI自身的系统上下文仍消耗Token；真实额度以账号为准，未验证“无限”。断线/失败保留上游回执的失败或unknown语义，不自动重发/切付费API。

此CLI版本未提供temperature/max_tokens控制参数：保留上游Prompt、双次独立评分和门槛，采样参数不与原API等价；回执明确记录`samplingParametersApplied=false`。没有宣称改用CLI后评分已校准。

`mcode`预算独立，首次入口创建8/分钟、60/小时、300/连续24小时的保守上限；已有预算不会被重置，`llm`与Jina预算不变。普通worker不启用stdio，仅这一按需SSH会话使用本地模型；本机离线时采集/原始官方索引继续运行。此入口没有定时Agent或通知。若运行 `muqiao-budget.ts` 重置全部服务，会将mcode也暂停，须显式审查恢复其预算。

## 切换与回退步骤

切换前保存旧origin配置、release指向及服务/timer状态，验证新站网页/API/RSS/后台鉴权。停止旧维护timer以免重复抓取，启用bridge timer，再把**既有专用隧道**origin切到8088并重启该隧道unit；公网检查失败恢复备份。数据库卷和旧站保留。

回退时恢复备份的 `/etc/cloudflared/intelligence-hub.yml`（origin8080），重启 `cloudflared-intelligence-hub.service`，停bridge timer，恢复 `intelligence-hub-maintenance.timer`。不要执行 `docker compose down -v`。

## 说明待确认

用户将自行补充使用/隐私说明，草稿在 [terms.draft.md](../../plans/aihot-core-migration/terms.draft.md) 和 [privacy.draft.md](../../plans/aihot-core-migration/privacy.draft.md)。公开页仅显示待补充，未发布未经确认的模板条款。

## AIHOT公开Codex重置结果

设置`CODEX_RESET_UPSTREAM_ENABLED=true`，现有worker每15分钟执行`monitor.upstream`，同步`https://aihot.news/api/v1/codex-resets`完整快照，使用ETag。首次可在api容器运行`node scripts/sync-upstream-reset.ts`。无数据库迁移，不导入本站原始X监测表，不触发模型或通知。页面`/codex-reset`、历史日历和公开v1读取同一缓存；来源、原文、状态不改写，45分钟过期提示，失败保留最后有效结果。撤回/修正随完整快照更新。关闭该环境变量回到原生监测读取（当前没有SocialData计划），模块开关false则隐藏入口。

## 上游RSS私人缓存（不进入公网内容库）

`python3 tools/aihot/upstream_feed.py --feed selected`保存个人缓存到`~/.local/share/information-hub/aihot-reader/`；`--feed all`读取全部动态，另支持daily及五个分类。目录700、文件600、TTL30分钟、ETag/304、最多100条，失败保留旧快照，禁止DOCTYPE及不合法上游链接；遇no-store不保存。无模型调用、摄取、通知或公网导出。

436的`intelligence-hub-upstream-reader.timer`每30分钟运行`upstream_reader.py`普通Python脚本，同步精选/全部、日报、五类RSS、最新日报API、热点10个事件及近期精选评分/更正/撤选到`/opt/intelligence-hub/aihot-private-reader/cache/`；目录不挂载到网站容器，不公开访问。本机TLS失败可通过既有SSH读取服务器私人缓存。

AIHOT公开使用规则1.1：https://aihot.news/terms。个人阅读与合理私有缓存允许直接使用；公网站点持续镜像/批量再分发需书面授权。定时RSS仍仅私有缓存；用户后续明确选择二次加工、人工审批后发布，见下节。当前没有上游书面授权记录，润色和审批不作为授权依据。接续见`plans/upstream-rss-reader`。


私人批量入口：`python3 tools/aihot/upstream_reader.py --cache-dir <私人目录>`。436服务目录为`/opt/intelligence-hub/aihot-private-reader`；工具依赖同目录的`upstream_feed.py`和`upstream_api.py`。缓存根为`cache/`，API结果在`cache/api/`，检查`cache/reader-status.json`获取各资源成功/失败摘要。服务超时12分钟、互斥锁避免重入、匿名请求间隔1秒，429停止当前轮次，不在本轮重试；常规TTL30分钟，支持ETag/304与no-store，坏响应保留有效缓存，404/410删除失效API资源。没有公开导出或模型调用。

精选初始快照只取游标，再取最近7天100条作为阅读种子；后续每轮最多5页、500个变更，状态最多200条近期文章，不覆盖全部历史。每页变更与游标原子保存；409过期时重建近期基线。API来源评分直接保存，摘要/评分更正及撤选同步至精选和分类RSS缓存，撤选不删除全部动态。热点之外的旧事件缓存清理；事件原始报道日期、来源链接、综述及storyline保留，缺少综述不补造。最新日报JSON与最近30期日报RSS分别保存。此目录不挂载网站容器。


## 加工审批（人工通过后上站）

后台入口`/admin/reviews`：建立待审稿 → 对照引用 → 本地AI生成/手工修改 → 填写审批依据、确认事实/新增价值/重复检查 → 通过并发布。默认进入全部动态，人工精选可进入首页。退回、重新保存或来源更正/撤选会撤回已有公开版本。素材与稿件均需管理员登录；公开接口看不到未审批稿。

```bash
python3 tools/aihot/local_opencode.py --review <上游ID> --max-calls 1
```

只支持1–10个显式ID，固定本地OpenCode的minimax-cn-coding-plan/MiniMax-M3.1-Flash-Preview；新闻加工和审批加工共用原opencode预算8/分钟、60/小时、300/24小时，既有预算不重置。真实回答先保存待审而非自动发布，人工编辑保留最近模型回执。

API从`UPSTREAM_REVIEW_CACHE=/upstream-reader/snapshot.json`读取有界私人投影：宿主`/opt/intelligence-hub/aihot/private-reader-api`以UID1000拥有，目录700、JSON600，只读挂载给API，未挂载原始私人缓存。reader通过`--admin-export-dir`更新投影，现有30分钟timer的ExecStartPost运行reconcile-upstream-reviews.ts，无模型/通知。近期材料最多200条，明确撤选记录保留最近1000个，覆盖单轮最多500变更；不把材料离开近期窗口当作撤选。维护失败需检查reader日志和投影新鲜度，超过1小时禁止新的审批，不拿旧来源审批；没有承诺完整历史覆盖。

0039迁移仅新增表，旧镜像可忽略它。此次旧镜像tag为muqiao-intel-aihot:pre-review，源码/override备份在review-staging/app-before-review.tgz、compose.previous.yaml；回退须恢复旧镜像及override，并恢复reader的RSS-only单元以免调用旧镜像没有的reconcile脚本。不要删除数据库/卷。根目录.env不进入源码备份，服务器仍保留原密钥，仅release标记更新。
