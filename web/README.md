# 木乔信息阅读工作台

> 2026-10-01：公网站点已改用[AIHOT核心](../deploy/aihot/README.md)。本目录保留旧Python阅读器、本地媒体桥接、采集适配与回退能力；以下原快照部署说明属于旧运行方式，旧维护timer现已停止。当前服务器的自定义采集只通过新bridge推送，不再发布Python快照。

纯 Python 标准库服务 + 同源 CSS/JavaScript，无前端构建或 CDN 依赖。
公网站点：https://intel.muqiao.xyz/ 。

## 本地运行

在仓库根目录执行：

```bash
HUB_PUBLIC_READONLY=1 python3 web/server.py 8087
```

打开 `http://127.0.0.1:8087/`。默认读取同级 `../output_to_user` 和 `web/data`，可用 `HUB_OUTPUT_DIR` 指定采集目录。
修改后端后需重启服务；页面修改后刷新。
不设置 `HUB_PUBLIC_READONLY=1` 时可使用已有媒体任务桥接，`MEDIA_STUDIO_API_URL` 指向工作室 API（默认 `http://127.0.0.1:3000/api/media`）。

## 数据与界面

`catalog.py` 适配 10 类现有输出：HN、橘鸦、HF、乔木 RSS、AK RSS、GitHub、AI Builders、雷达、融合简报、媒体素材。
原始采集结果优先；旧 enrichment 只补充匹配内容，不覆盖新条目。
`/api/library` 提供统一阅读模型，`/api/status` 提供运行模式、来源状态和指纹。

发表时间来自原文元数据，采集时间来自 generated_at/generatedAt；没有时间的结果明确标为文件更新时间。
稍后读和主题选择只保存在当前浏览器，不会跨设备同步。页面刷新只重读已发布的文件，不执行采集。

## 发布到 436

采集并发布最新在线内容，在仓库根目录执行：

```bash
python3 web/refresh.py --destination /tmp/intelligence-hub-releases --deploy
```

本命令重新请求 HN、橘鸦、HF、乔木 RSS（沿用 3 个订阅、每个 2 条）、AK RSS（89 个订阅的近七天候选）、GitHub 趋势和 AI Builders；AI Builders 强制读取在线 feed，不使用旧本地镜像。
每个采集器先写临时目录，通过非空内容和来源链接检查后才替换已有输出；旧文件及原时间戳保存在 `output_to_user/.refresh-history/<run-id>/`。任一来源失败，本次不自动发布，成功采集结果保留供检查，失败来源的旧快照保持不变。
可用 `--sources juya` 只更新橘鸦，省略 `--deploy` 只采集。此命令是一次性执行；436 的周期维护见下节。

上游最新一期可能早于今天：`date` / `publishedAt` 是原文日期，`generated_at` / `generatedAt` 是本次成功采集时间。机会雷达、融合简报和媒体素材来自各自的报告或加工流程，不通过上述命令重写日期。

只发布已存在的快照（不会重新采集）：

```bash
python3 web/publish.py --destination /tmp/intelligence-hub-releases --deploy
```

省略 `--deploy` 可只打包检查。发布只接触 SSH 别名 `racknerd-436b0c0` 上的 `/opt/intelligence-hub` 和 `intelligence-hub.service` 的专用 drop-in。
Cloudflare Tunnel 和远端流水线 Git 仓库独立管理，本命令不修改它们。

发布包只纳入 `CODE_FILES`、`OUTPUT_FILES`、`DATA_FILES` 明确列出的文件；移除 local_path/git_head，拒绝检测到的本机路径、Cloudflare token、私钥模式。
包内 `release.json` 记录源提交、文件哈希、代码/数据指纹。源提交只是工作区基线，未提交代码仍会发布；真正的比较依据是指纹。
数据指纹包含无日期文件的原始更新时间，打包保留时间戳，不以发布时间冒充采集时间。

远端结构：

```text
/opt/intelligence-hub/
  releases/<release-id>/   # 每次独立版本
  current -> releases/<release-id>
  web/ snapshots/         # 首次旧部署，保留供回退
```

上传后校验文件哈希、原子切换 current、重启并校验运行指纹；失败自动恢复前一服务配置。
旧版本保留。手动回退时选定已验证的前一版本，原子切换 current 后重启 `intelligence-hub.service`；首次旧版回退需移除本次生成的 `20-release.conf` drop-in 后 daemon-reload/restart。

验收：比较本地与公网 `/api/status` 的 `codeDigest`、`datasetDigest`、`sources`；浏览器检查搜索/详情/收藏；公网 POST `/api/studio/dispatch` 必须返回 403。
静态资源 `no-cache`、API `no-store`；HTML 中脚本和样式的 URL 携带运行代码指纹，发布后自动切换资源版本，避免旧 HTML 与新脚本/数据混搭。

## 436 原生定时维护

用户于 2026-09-30 要求直接运行脚本、无需 Agent、不要通知。维护通过 `intelligence-hub-maintenance.timer` 调度：北京时间每个偶数小时的 15 分执行（00:15、02:15……22:15，允许最多一分钟调度误差）。`Persistent=true` 在机器错过计划后补跑一次。

首次安装或更新维护脚本：

```bash
python3 web/install_maintenance.py
```

安装器仅打包明确列出的采集脚本、RSS/账号配置和维护代码；X 采集另使用独立 venv 中的 Playwright，发送到 `/opt/intelligence-hub/maintenance/releases/`，不依赖 ControlMesh、Codex、模型 API 或本机在线。启用 timer 后立即运行一次。

`web/maintain.py` 在 436 直接采集七个在线来源（X 改为按需并默认暂停），以当前线上版本为基础生成新发布包，验证哈希后切换并检查网站。部分来源失败时保留该来源旧内容和原时间戳；全部失败则不发布；切换后健康检查失败则回退。手动发布和定时任务共享互斥锁。

日志仅写 systemd journal，最近一轮结果保存在 `/opt/intelligence-hub/maintenance-last-run.json`；没有通知、邮件、Webhook 或 Agent 汇报步骤。自动版本保留最近 14 份，当前版本、直接回退目标和手工发布版本受保护。

在 436 上检查或操作：

```bash
systemctl list-timers intelligence-hub-maintenance.timer
journalctl -u intelligence-hub-maintenance.service -n 30 --no-pager
systemctl start intelligence-hub-maintenance.service
systemctl disable --now intelligence-hub-maintenance.timer
```

服务端定时采集后，线上数据会比本地旧快照更新；本地代码依然是开发基准。要手动发布数据，先运行采集到发布命令，避免单独发布旧快照。

## 验证

```bash
python3 -m unittest tests.test_web_catalog tests.test_web_studio_bridge -q
python3 -m unittest tests.test_web_refresh tests.test_web_maintenance -q
node --check web/public/app.js
```

## 11 个项目阅读技能

- AK RSS：复用 `skills/ak-rss-digest` 的 89 个 RSS/Atom 订阅，抓取近七天，按 URL 去重后保留最近 150 篇。`fetch_ak_rss.py` 只转换字段，不生成 AI 评分。
- X 关注动态：64 个账号、近七天 Google 公开搜索候选，已退出默认 timer，按需新采集须通过账号风控门禁。Jina 正文接口保留，当前按用户选择显示搜索摘要；中文精选周报仍按需。
- X 文本归档、X 图片与视频：按链接、权限和依赖条件执行。
- 论文解读、论文解读与制卡、内容制卡、概念拆解、通俗解读、概念降秩分析、书籍结构拆解：用户选择内容后复制任务，交给项目内 Agent；论文制卡先消费实际 Org 解读。

入口在顶部“阅读工具”和详情页“用阅读工具处理”。任务带有材料、技能相对路径、产物要求，可先预览或修改材料；复制被浏览器拒绝时自动选中任务供手动复制。此版本不在公网执行 Agent，也不自动将产物回写网站。

`web/public/workflows.json` 是可公开的展示与任务描述；不发布 SKILL 原文、工具认证或账号配置。制品的 `codeDigest` 包含该文件。

AK 采集结果写入 `ak_rss_sources_latest.json`，包含 `coverage`、`window`、`selection=unscored` 和原文时间。订阅部分失败时展示覆盖数；全失败或无有效有日期文章时保留旧快照、记录失败，不伪造新鲜度。所有原定时任务继续不调用模型、不发送通知。

```bash
python3 web/refresh.py --sources ak-rss
python3 -m unittest tests.test_ak_rss tests.test_web_catalog tests.test_web_studio_bridge tests.test_web_refresh tests.test_web_maintenance -q
```

## X 关注动态与 Jina Reader

`fetch_x_google.py` 用 Playwright 附着 436 现有 `server-browser.service` 的回环 CDP，创建并清理本次专用匿名上下文。Google 结果可能是 `/goto` 跳转链接，使用任务页面正常导航取得真实 X URL；严格过滤账号、URL 和帖子 ID 日期，去重并合并最近七天候选。搜索索引不代表完整账号时间线，不调用 X API、opencli 或模型。

默认 8 组搜索、每组最多 8 个结果，整轮预算 230 秒、外层超时 270 秒。遇到 Google 验证挑战停止，记录日志并保留旧快照。无有效近期内容不伪造更新；来源状态显示搜索批次、未解析链接及摘要/正文数。原帖时间取 X Snowflake，保留独立采集时间。

436 的 Jina 匿名读取因机房 IP 信誉返回 401。2026-09-30 用户选择先显示搜索摘要；无 key 时不重复请求。以后在 **436** 的 `/etc/intelligence-hub/jina.env` 配置 `JINA_API_KEY`（root 所有、0600，不进入仓库或制品），下一轮维护会读取。Jina 最多读取 16 篇、间隔至少 3.1 秒，401/403/429 停止本轮读取；失败保留摘要或已取得正文及原读取时间。当前 Jina 成功正文分支仅有离线测试，未完成此主机带 key 实测。

安装器只安装 Playwright 库，不下载或启动第二份浏览器。浏览器服务不可用时仅 X 本轮失败，其他来源继续；本机浏览器不参与自动维护。项目技能脚本是同一采集器的兼容入口，仍输出 `candidates.json` / `candidates.md` 供按需编辑。

```bash
python3 web/refresh.py --sources x
python3 -m unittest tests.test_x_google -q
```

`collection_status.json` 保存可公开的本轮状态，不含错误原文或服务器路径。来源采集失败时，页面显示“本轮未更新”和上次成功采集时间。安装维护包可加 `--no-run`，只更新脚本并保留 timer，不立即重复请求上游。

## 账号风控暂停（2026-09-30 用户修正）

X 已从 `DEFAULT_SOURCES` 移除，普通 refresh 和 436 timer 均不会搜索 Google。显式 `--sources x` 也先调用 `/usr/local/bin/ops-account-risk check --scope google:racknerd-436b0c0`；状态缺失、损坏或暂停都拒绝连接浏览器。每批及后续跳转前重新检查，识别验证时写入共享暂停状态并停止。Ops-Vault `20-How-To/account-risk-cooldown.md` 为规则原文，门禁源码为该库 `scripts/account-risk-guard.py`；独立部署到 436，不发布进网站。可用 `HUB_ACCOUNT_RISK_GUARD` / `HUB_ACCOUNT_RISK_SCOPE` 显式选择已授权环境的门禁与范围。

当前最小冷却 24 小时，到期仍须人工检查并明确恢复；不会自动补跑，也不更换身份/出口/匿名上下文重试。仅 X 已接入执行门禁，不代表全 fleet 自动化已被统一拦截。已有内容保留，其他七个来源按原计划采集，无 Agent、无通知。
