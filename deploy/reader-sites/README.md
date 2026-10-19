# 436 开源阅读站点

按用户2026-10-19要求，在436自托管既有开源项目。信息站的`/reading-tools`只提供入口、官方站与项目说明，不重写两个应用，不把其数据接入信息站publication或公众号定时器。

| 应用 | 固定上游 | Origin | 436运行方式 |
| --- | --- | --- | --- |
| [NewsNow](https://github.com/newsnext/newsnow) | v0.0.43，`0560c993b226cd2fd07d8a79875d50551f52c584` | `https://news.muqiao.xyz` → `127.0.0.1:4444` | `newsnow.service`，Node22.22.1，独立SQLite缓存 |
| [ArXivHub](https://github.com/Peaceful-World-X/ArXivHub) | `9c6268693b411ffc6d577dc95f192db44408a7b8` | `https://papers.muqiao.xyz` → `127.0.0.1:4445` | `reader-sites-arxivhub-1`，已有Nginx镜像，静态产物 |

官方站分别为[NewsNow](https://newsnow.busiyi.world/)和[ArXivHub](https://arxivhub.github.io/)。两者均保留完整MIT许可与官方来源；ArXivHub分发包另含第三方许可记录。NewsNow公开`/LICENSE.txt`和`/UPSTREAM.json`；ArXivHub公开`/LICENSE`和`/UPSTREAM.json`。公网接入及实际读回以[本次进度](../../plans/reader-sites-selfhost-20261019/progress.md)为准。

## 版本与运行目录

- NewsNow源码及构建：`/opt/reader-sites/newsnow/releases/<commit>`；`current`指向固定release。官方Compose的`latest`实测仍是v0.0.41，因此本次构建当前源码，不将旧镜像冒称v0.0.43。
- 复用436的Node22.22.1，以`corepack pnpm install --frozen-lockfile`和`pnpm run build`构建。原Dockerfile的Node20.12.2低于当前Vite7要求。运行直接使用生成的`dist/output/server/index.mjs`，不使用需.env的pnpm start。
- 运行二进制固定副本为`/opt/reader-sites/runtime/node-v22.22.1`；系统`/usr/local/bin/node`实际链接到root的NVM目录，不能在`ProtectHome=true`的服务中直接执行。没有修改全局Node或CLI登录。
- Node原发行包的完整许可随运行时保留为`/opt/reader-sites/runtime/node-v22.22.1.LICENSE`。
- NewsNow使用systemd DynamicUser；持久状态在`/var/lib/newsnow/.data/db.sqlite3`（host侧实际为`/var/lib/private/newsnow/.data/db.sqlite3`）。不设置OAuth或模型密钥，匿名阅读；缓存和账号状态不进Git。
- ArXivHub在固定源码`web/`内用现有Node22.23.2执行`npm ci --no-audit --no-fund --prefer-offline`、`VITE_BASE=/ npm run build`。正确产物是`web/dist`；仓库根Pages页面只是跳转页。
- 静态release位于`/opt/reader-sites/arxivhub/releases/<commit>`；`current`指向release。`compose.yaml`复用436已有的Nginx精确digest，仅绑定loopback；`arxivhub.nginx.conf`支持`/p/{id}`和`/about`的SPA深链。
- 静态包SHA256为`e814aaaa52ee19081421bb04eb5bea3dc69507c4345f38b511e92d15b571066f`，含逐文件`SHA256SUMS`，解包前后分别校验。

## 接入与更新

现有`muqiao-info-436`隧道追加两个host到对应loopback。DNS使用本机官方cf的既有OAuth创建Proxied CNAME；认证保持本机。服务器不复制OAuth，不另建Tunnel。原`/idp/*`、intel→8088和末尾404保留。

配置文件分别安装为`/etc/systemd/system/newsnow.service`、`/opt/reader-sites/compose.yaml`及同目录`arxivhub.nginx.conf`。运行`systemctl daemon-reload`、`systemctl enable --now newsnow.service`，再启动下列Compose服务。构建依赖留在release，动态用户只写独立StateDirectory。

维护命令：

```sh
systemctl status newsnow.service
systemctl restart newsnow.service
docker compose -p reader-sites -f /opt/reader-sites/compose.yaml ps
docker compose -p reader-sites -f /opt/reader-sites/compose.yaml up -d --force-recreate arxivhub
```

升级先在新release构建、校验，再切`current`。NewsNow重启后核对SQLite缓存保留；ArXivHub切指针后重建该静态容器，确保bind mount重新解析。不要清除持久缓存或批量重建信息站服务。

首次部署回退可停止对应新服务，保留release、许可、缓存和原始记录。信息站入口回退只恢复本次备份的3个前端文件／UPSTREAM和原web镜像；不恢复或覆盖API、worker、数据库及个人阅读状态。域名和ingress回退须比较当前配置，再只撤回本次新增两条，不能覆盖其他人的后续更新。

本次web镜像为`muqiao-intel-aihot:reader-sites-20261019`，回退目录为`/opt/intelligence-hub/aihot/rollback/reader-sites-20261019/`。Cloudflared原配置与本次暂存配置在`/var/backups/cloudflared-reader-sites-20261019T123542Z-e29ab0c1/`，现场manifest保存DNS创建回执与配置指纹，不将账户回执或运行日志提交Git。既有Compose override使用`!override`标签；更新镜像时保留该语义，不用普通YAML解析器重写整个文件。

## 已核实的能力边界

NewsNow是多平台热榜阅读应用，不是微信公众号热榜。缓存接口的一条成功分支将`updatedTime`设为请求时间；不能单凭该字段声称刚刚回源或推算上涨趋势。实际缓存写入时间与内容在独立SQLite中，重启持久性按数据库行与响应内容核对。

ArXivHub是论文工具目录和浏览器端论文阅读入口。元数据、指标及TLDR依赖DataCite、alphaXiv、Semantic Scholar、OpenAlex、Microlink和Reader等公开外部服务，其可用性/CORS/公开额度不由本机部署保证。本次真实1706.03762标题和PDF入口通过，TLDR显示暂未读取；不宣称摘要或全文全部成功。官方userscript桥只匹配原官方域及localhost，自建域默认不适用；本次不安装或注入脚本。
