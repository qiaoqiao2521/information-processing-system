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

436未安装Buildx，本次使用`DOCKER_BUILDKIT=0 docker build -t muqiao-intel-aihot:local .`完成构建。源文件manifest放在服务器部署根目录，核对镜像内409个文件哈希；`AIHOT_RELEASE`与`/api/health`对应实际部署版本。

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

当前新站已启用`MODEL_CALLS_ENABLED=true`、`COLLECT_ENABLED=true`。旧`intelligence-hub-maintenance.timer`已停止，新bridge/backup timers启用。回退配置保存在`/opt/intelligence-hub/aihot/rollback-current`；旧8080服务仍在。

## 订阅与回灌

- `python3 tools/aihot/subscriptions.py`把89 AK OPML订阅、乔木当前3个及上游18示范源合并为108 RSS，追加旧自定义源。
- 首次seed新增信源，复跑不覆盖后台修改。以后订阅在 `/admin/sources`管理。
- `scripts/import-hub.ts public-library.json`保存真实发表/采集日期、无模型分数的旧站摘要和旧ID映射；同网址跨来源只留一个身份，复跑不新增。
- `tools/aihot/bridge.py`推送HN/橘鸦/HF/GitHub/Builders最新材料；文章摘要、正文有界传输，旧抓取失败则保留快照。不会重跑已原生接入的RSS和暂停的X。
- 同一条文章被不同来源发现会留发现记录，重复发现不会制造新文章。
- 默认不展示或再分发原文全文；阅读工具只复制任务，不直接调用模型。

## 切换与回退

切换前保存旧origin配置、release指向及服务/timer状态，验证新站网页/API/RSS/后台鉴权。停止旧维护timer以免重复抓取，启用bridge timer，再把**既有专用隧道**origin切到8088并重启该隧道unit；公网检查失败恢复备份。数据库卷和旧站保留。

回退时恢复备份的 `/etc/cloudflared/intelligence-hub.yml`（origin8080），重启 `cloudflared-intelligence-hub.service`，停bridge timer，恢复 `intelligence-hub-maintenance.timer`。不要执行 `docker compose down -v`。

## 说明待确认

用户将自行补充使用/隐私说明，草稿在 [terms.draft.md](../../plans/aihot-core-migration/terms.draft.md) 和 [privacy.draft.md](../../plans/aihot-core-migration/privacy.draft.md)。公开页仅显示待补充，未发布未经确认的模板条款。
