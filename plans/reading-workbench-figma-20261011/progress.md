# 进度

- 2026-10-11：本地干净，基线 d5bd539。436 Tailscale SSH 可达；web/API/worker 镜像 26f8e7e4e8c3。本地与 436 home.tsx、app.css 哈希相同。
- 现场一手精选仅三条，最新内容发表于 2026-10-01；不能标为今日更新。API generatedAt 只是响应生成时间。
- Figma 文件：https://www.figma.com/design/1EzmBZIxCukmAiCNg0Bp5N 。无既有屏幕、无 Code Connect。已检索 Simple Design System，复用 Button、Navigation Button、Search 和 Space/400；行业新闻条目不在该套组件中，需要局部组件。
- 本机 Node 22 不满足上游 Node >=24.11；优先复用 436 已验证的 auto-build 镜像，不更换系统 Node。
- Figma 可编辑桌面 3:253、手机 3:488 已建立，均使用 Noto Sans SC，正文无整页图片；本地预览已保存。部分中文按钮仍折行，设计接回时需调整单行宽度。前端实现、真实交互验收和 436 部署尚未开始。
- 用户随后要求把前端整理到下载目录。已交付 `~/下载/木乔信息工作台-前端-20261011/`：当前源码、共享 contracts、前端使用的 industry 配置、Figma PNG/链接与改版说明。根 workspace 清单仅包含三个前端包；原根配置和锁文件保存在 reference 供溯源。
- 文件夹包含 172 个文件、1,386,941 字节；167 个复制文件逐一核对 SHA-256 一致。独立安装、构建和 API 交互未执行。运行要求和状态见文件夹 README.md；source-manifest.json 记录来源。
- 接续 owner：根 Codex。最短入口是文件夹 README.md 的改版文件映射与 Figma 桌面/手机节点；用户继续接回改版时，先修复按钮折行，再实现筛选、视觉与公网验收。
- 知识回写：already_covered。Wiki/自动化开发范式与智能体协作「按当前任务选择验收依据」已覆盖复制校验、构建和真实交互的边界，未新增通用结论。
- 2026-10-11：用户要求直接把当前运行前端导入 Figma。使用官方 `generate_figma_design`，在 Tailscale SSH 到 436 的临时 Node 24.21.0 容器中运行当前本地源码，通过 `API_BASE_URL=http://api:3001` 读取现有公开数据；loopback 8092 经专用 SSH 转发到本机 26082。捕获脚本仅加入临时副本。
- 一手精选 `16:208`（1440 × 1032）：59 个文本、205 个框架、37 个矢量图层；全部动态 `14:208`（1440 × 8053）：302 个文本、1064 个框架、72 个矢量图层。自动布局分别为 156、762 个；无整页图片填充。保留既有桌面、手机和条目组件草案作为对照。
- 已把 48 个不可用的 Liberation Mono 引用换为可用的 Roboto Mono；两个导入页面缺失字体均为 0。已检查修复后的首页和全部动态预览，页面文字和布局保持当前站点样式。下载目录 `design/` 新增 `figma-current-first-party.png`、`figma-current-all.png`，并更新 Figma链接.md、README.md。
- 两个捕获 ID 均完成且已消费；未调用采集、模型或修改生产数据。三个专用后台浏览器已关闭，临时容器和传输包已删除，本机专用 SSH 转发已停止。436 root.tsx 哈希仍为 `4bba6ee2e2b9eab694563a9f2c90ce2d64f7aeb63fd30e25983025c5d693ac27`；生产首页 HTTP 200，web/API/worker 未重启。
- 当前页面导入已交付；原计划的改版实现和部署仍未开始。知识回写：already_covered，采用的验收依据已覆盖本次结构和截图校验。接续 owner：根 Codex；从 Figma `16:208`、`14:208` 与设计草案对照继续。


## 当前：Make Version 8 已接回并部署

- 冻结2026-10-11 Version 8地图版；保留点阵地图、配色、光晕、卡片比例和解码效果。原始包、源文件及集成hash记录于 make-v8-manifest.json。
- 接回 timeline/pool/stats 和真实日期、六类分类、来源频道、组合搜索/排序、分页、AI加工、收藏/已读、文章/原文、事件及原有辅助入口。模拟新闻/随机延迟/固定在线和虚构指标移除。标题解码按750毫秒实际时间完成；减少动效时静态更新正文。
- 本地 Node24.21.0 临时工具完成全仓typecheck、web build、18/18网页测试；436最终镜像重新执行相同构建门槛。新增测试覆盖组合条件保留/分页重置和日期/待处理/事件定位映射。
- 真实436 API + 浏览器：一手搜索OpenAI保留来源；收藏写入并在收藏页读回；详情来源链接和返回条件正常；公网第二页实际取得40条；首页3张卡片均有定位key，打开后返回恢复，已读状态可见。手机390宽，无整体横向溢出，分类独立横滑；未把程序验证宣称为用户主观审美验收。
- 436最终web镜像 `516129543c0ef1db2baeb08e2202aeaadf065d760ccd98dea0a87f0cd079dbc3`，仅绑定127.0.0.1:8088。API/worker/db镜像和启动时间不变，无数据库迁移、模型消费、采集开关或通知变更。
- 首次冒烟紧接容器启动、监听尚未就绪，31项连接失败；随后确认origin HTTP200，再运行既有smoke脚本，31项页面、公开API、RSS和MCP初始化全部通过。公网浏览器已读回最终定位标记及真实数据，没有捕获到运行错误。
- 回退：`/opt/intelligence-hub/aihot/web-make-v8-20261011/compose.previous.yaml`和`app-web-before.tgz`；旧镜像保留为`muqiao-intel-aihot:pre-make-v8`。只恢复web镜像和前端源码，不操作数据库卷。
- 下载目录新增 make-v8-source、integrated-web 及 review/make-v8-live-*.jpg。integrated-web仅变更文件交接，完整工程是仓库，未声称下载目录可独立安装。
- Knowledge closeout: already_covered。采用的 Wiki/自动化开发范式与智能体协作「按当前任务选择验收依据」已覆盖源码/构建/真实交互/外部读回以及启动不等于就绪，无共享知识改写。
- Remaining：无必要工程工作待用户操作；自动加工质量、模型额度及最新精选条数属于既有后台流程，本次未改造。后端数据库测试未运行，因为本次仅前端展示和依赖；全仓类型与既有网页缓存/取消/本机状态测试已执行。

- 收尾仅移除两个新文件的尾随空格／EOF空行；不改代码语义。manifest分别保留构建源码hash与提交源码hash，避免混淆字节校验与行为验收。临时本机预览和专用API SSH转发已停止。
