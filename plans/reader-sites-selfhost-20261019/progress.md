# Current
2026-10-19，两个开源应用在436部署完成，独立域名和信息站入口实际可用。根正在整合本地历史成果与远端新增CI，完成Git交付。

# Done
- 经既有Tailscale SSH alias racknerd-436b0c0操作436，未改变Tailscale配置。与应用原「信息源」对话协作：根负责源码与服务，对方只通过官方cf和既有Tunnel追加DNS/ingress。
- [NewsNow](https://news.muqiao.xyz/)固定v0.0.43源码构建，newsnow.service启动且开机启用，127.0.0.1:4444；匿名读取，独立持久SQLite缓存，重启前后内容与数据库行hash一致。
- [ArXivHub · 论桥](https://papers.muqiao.xyz/)固定9c626869静态产物，归档及逐文件SHA校验通过。既有Nginx镜像精确digest、只读挂载及SPA深链，127.0.0.1:4445；Compose配置及systemd unit在436实际验证通过。
- 两个Proxied CNAME经Cloudflare API回读及公共DoH确认。专用Tunnel经CAS追加两条host，原idp、intel和末尾404保留；最终配置SHA256：89ca4c210fff4032e85ad7bc6896d5e9c883a28a19558658f1b9f863e5491b63。只重启该隧道，原信息站health保持200/ok。
- [信息站阅读工具](https://intel.muqiao.xyz/reading-tools)只改3个前端文件及UPSTREAM。web镜像reader-sites-20261019运行，API仍lifegame-20261014、worker仍nobrand-e-20261012，未重建它们。生产源码与本地前端文件hash逐一相同。回退路径见[部署说明](../../deploy/reader-sites/README.md)。
- 根在真实公网独立浏览器读回7条目标链接：两个本地域、两组官方站/GitHub及1706.03762深链；论文标题Attention Is All You Need和官方PDF目标实际可见。没有复制每日浏览器账号或使用外部响应mock。
- 子Agent独立公网浏览器：NewsNow实际选择知乎20条、GitHub12条，B站热门视频20条；论桥目录116项、完整MIT与commit元数据一致、论文详情和390px无横向溢出；两个应用JS pageerror均0。原官方名称、作者和许可保留。
- 本地全仓typecheck、网页build、现有29项网页测试通过；436真实Docker构建同样执行上述检查。Python现有102项测试通过。当前源码smoke在实际web容器检查页面、API、RSS、MCP全部通过。未执行需要空库的完整后端数据库测试，本次未改API/DB业务。
- 原始浏览器报告留在本机repo-scan/ArXivHub/artifacts/{news-public-smoke,papers-public-smoke}.json；运行日志、账户回执、缓存、截图和.env不入Git。

# Remaining
完成Git正常合并、推送与远端SHA读回；服务与用户入口无待部署项。

# Issues
NewsNow部分来源有上游失败（百度500）；缓存updatedTime不保证回源时间。论桥TLDR暂不可读、官方userscript不适用于自建域。上述为已观察的上游能力边界，未冒称全部通过。信息站旧镜像内置smoke误判首页302的差异已由当前源码检查和Location独立核对排除，详见findings。

# Knowledge
already_covered：已采用Wiki/工具链与认证体系.md的明确运行时路径及真实入口核对原则。Node根目录隔离、上游cache时间和Compose特殊标签等现场细节写回本项目findings与部署说明；本次没有需要改写共享知识页的新通用规则。
