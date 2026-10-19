# 核实事实

- 受控仓库为 information-processing-system；436定制AIHOT是 /opt/intelligence-hub/aihot/app 源码快照，非独立Git仓库。
- 原信息站对话ID 01a0ddae-8240-7dd0-a5d1-e9daf23cb550，应用真实标题「信息源」。相似 ddb1 ID 属于物理课程，不用于协作。
- 2026-10-12只增加NewsNow官网/GitHub外链；ArXivHub是MIT论文工具目录，原官方入口 arxivhub.github.io/p/$id。
- NewsNow当前v0.0.43源码0560c993b226cd2fd07d8a79875d50551f52c584；官方Compose的latest镜像实际v0.0.41，不能当作当前版。源码使用Vite7，原Dockerfile Node20.12.2低于其版本要求。
- NewsNow前端硬编码/api及根路径路由，优先独立origin，避免为挂子路径大改上游。
- 论文项目固定为Peaceful-World-X/ArXivHub提交9c6268693b411ffc6d577dc95f192db44408a7b8。实际应用在web/，仓库根页面仅作跳转。VITE_BASE=/构建，Nginx保留history fallback。
- NewsNow匿名读取不需要复制账号；/api/enable-login返回506表示未开启可选登录，不能当作热榜读取失败。百度源曾500，36氪由等待转为200；不能宣称全部来源稳定。
- NewsNow已有一条cache分支以请求时刻填updatedTime，真实缓存写入时刻保存在SQLite。第一次按API时间与数据库时间相等的断言失败；修正验收方法后，确认重启前后缓存行及内容hash一致。应用源码未为此改写。
- 436的/usr/local/bin/node指向root的NVM目录，受ProtectHome隔离。初次服务出现203/EXEC；复用同一Node22.22.1二进制到/opt/reader-sites/runtime后恢复，保留原许可。历史重启记录未清零。
- ArXivHub真实论文标题、PDF目标及390px布局通过；TLDR上游Microlink400，Reader200但未解析出TLDR。独立部署不等于承诺全部第三方工具可用。官方userscript域匹配不含自建域，本次未注入或安装脚本。
- 现场Compose override带!override标签，普通PyYAML不能加载。初次解析失败发生在配置变更之前，后续通过CAS及仅替换web镜像行完成；不重写其他服务与特殊标签。
- web镜像继承的旧smoke脚本仍将首页302判失败；当前仓库脚本已允许唯一的/→/all规范跳转。根用当前脚本经stdin在新容器执行，所有检查通过；另独立核对302的Location=/all、/all与reading-tools均200。没有用旧脚本的非零退出声称验收通过。
- Git初态为本地31个历史提交、远端2个新提交分叉；远端仅CI与文档账户链接，无应用路径交叉。不清理历史118处空白问题，不将本次diff检查扩写成全部历史检查通过。
