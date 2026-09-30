# Findings

- 本地 HEAD ad3fe8d，起始仅 workbench_vault 未跟踪。web/server.py 和 index.html 与 /opt/intelligence-hub 相同 SHA256。
- 436 的流水线仓库 HEAD feb9462；实际服务来自 /opt/intelligence-hub，与该 Git checkout 无关。
- 公网只打包了 3 个 web/data 文件和简报/雷达两个输出。新采集器 HN、橘鸦、HF、乔木已有本地结果，却未被网页消费和发布。
- 雷达 selected_sections 的标题是 section，条目为 question/signal/key_judgment/contrarian_view，旧 UI 读 heading/title/summary，导致空白。
- digest 原始结果使用 selectedSources，旧 fallback 只认 sources；trending/digest 总是优先旧 enriched 文件。
- 公网只隐藏了抽屉投产按钮，素材卡片仍有投产入口；后端 403 保持有效。
- Chrome shared proxy 已 blocked，桌面 fallback 无可见 Chrome 窗口。使用现有无需登录的 Codex IAB 页作界面验收。
- 对齐后共 9 个来源、129 条：HN 30、橘鸦 16、HF 15、乔木 RSS 6、GitHub 16、AI Builders 12、雷达 16、简报 3、素材 15。
- 雷达报告的发表日期为 2026-08-14，采集日期为 2026-09-26；必须分开显示。日期字段只有日精度时不补造时刻。
- 首次部署后曾观察到浏览器仍使用旧的选中逻辑；为脚本/样式 URL 增加运行代码指纹，最终公网验证列表首项、选中项和阅读内容一致。
- 436 流水线 checkout 并非网站服务入口，且输出目录没有可合入的更新快照；本次发布以本地现有采集文件为准。
- 2026-09-30 01:15 北京时间：橘鸦官方 `/archive/` 最新期为 2026-09-29，正文包含 30 条；旧公网仍是 26 日的 16 条，属于没有重新采集。
- 新增采集器直接执行时可能把请求失败返回的空数组写成今天的输出；`web/refresh.py` 先隔离采集，再验证后原子替换，保留失败来源原文件和时间。
- AI Builders 默认 prefer-local 会反复读取旧 feed 镜像；新刷新入口强制 remote。六个来源本轮全部成功，129 条更新为 141 条。
- BuilderPulse 官方 GitHub contents API 的 zh/2026 最新文件仍为 2026-08-14.md；不能把它包装成 30 日的新报告。融合简报和素材也保留原加工时间。
- 436 的原 crontab 只有 ControlMesh watchdog；ControlMesh 官方 CLI 返回 19 个任务，全部 enabled=false。没有信息站采集 timer，也没有匹配本项目的 Codex automation；无需停用或改动其他任务。
- 安装 `intelligence-hub-maintenance.timer`：北京时间偶数小时 15 分运行，Persistent 补跑，脚本执行，无 Agent、通知和外部消息步骤。
- 首轮 2026-09-30 01:32:06–01:32:09 北京时间，六个来源全部成功，systemd Result=success / ExecMainStatus=0；网站 141 条，数据指纹 bc31a15039799705。timer active，下一次 02:15。

## 新增技能不等同于信息源

11 个 scoped skills 中，AK RSS 是可直接进入无人值守维护的标准 RSS/Atom 采集器；AI influence 是依赖 opencli 的候选发现工序；X 文本/媒体是指定链接导入；LJG 七项是加工/阅读工序。`ljg-rank` 是概念降秩文章，不是资讯排行榜。

自动 RSS 输出与 AK skill 的 AI 精选输出须明确区分：采集仅保留未评分候选，不伪造评分。前端的按需任务引用项目内 skill 文件，材料以 JSON 作为数据传递；公开站点无执行 Agent 的接口。

项目本地复制版本保留来源和适配，不把可运行脚本的部署扩展成整个 skill 工具链的全局安装。维护包只新增 AK 适配器、原采集脚本和 OPML。


## X 浏览器采集验收

- 本轮用户修改了先前来源范围：AI influence 必须成为真实 X 来源，Google 走浏览器，移除 opencli 依赖。原技能 65 文件实际为 64 个唯一账号。
- Google `after:` 不能证明发帖日期：实际搜到 2079658951264920020，其 Snowflake 时间为 2026-07-21。采集另用帖子 ID 时间与白名单校验。Google 的 /goto 结果需正常浏览器导航得到真实 URL，跳转超时不能继承上一页 URL。
- Jina 官方支持匿名 Reader，但此 436 请求实际返回 AuthenticationRequiredError / AS36352；用户选择先摘要。无 key 时跳过 Jina，接口保留，密钥仅从服务环境读取，不发布。
- 第一次真实浏览器采集完成，后续 systemd 环境复跑命中 Google 验证检测。不能把 service Result=success 当成每个来源成功；网页需要展示本轮失败与上次成功快照日期。公开状态只含固定消息，错误堆栈留本地日志。
- 检测验证码时先区分真正的 Google interstitial 和讨论验证码的搜索摘要；后者包含 Search Results，不应单靠 not-a-robot 文本判为挑战。
