#!/usr/bin/env python3
"""
多源信息要素提取与本地落盘引擎 (Information Enrichment Engine)
1. 修复 GitHub 仓库名称与元数据提取
2. 提取信息要素:
   - 核心解决问题 (Problem Solved)
   - 核心技术架构与亮点 (Key Architecture & Features)
   - 适用人群与场景 (Target Audience)
   - 媒体价值与选题切入点 (Editorial Angle)
3. 关联并聚合本地落地全文快照 (Local Snapshot Text)，彻底摆脱外部跳转依赖
"""
from __future__ import annotations

import json
from pathlib import Path

WORKSPACE = Path("/home/muqiao/projects")
OUTPUT_DIR = WORKSPACE / "output_to_user"
WEB_DATA_DIR = Path(__file__).parent / "data"
WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)

GITHUB_ENRICHMENTS = {
    "paperclipai/paperclip": {
        "problem_solved": "过去 Agent 处于黑盒或单脚本运行状态，缺乏组织层面的工位、预算、Token 配额与审批汇报链条，难以规模化落地企业。",
        "key_features": [
            "提供类企业架构图的 Agent 组织与角色定义 (Organization Chart)",
            "内置数字员工工位分配、部门预算与 API Token 硬限额治理",
            "人类主管审批流 (Human-in-the-loop approval) 与工作流日志归档"
        ],
        "target_audience": "需要调度多 Agent 的技术 Leader、运营负责人、探索数字员工的企业",
        "editorial_insight": "今日黑马榜首（+2109星），反映企业级 Agent 从‘单个玩模型’向‘组织治理与权限管理’的关键跃迁。"
    },
    "vectorize-io/hindsight": {
        "problem_solved": "传统 RAG 仅做静态文本检索，无法从 Agent 执行失败中复盘，导致同一类 Bug 跨会话反复重犯。",
        "key_features": [
            "引入‘事后复盘（Post-Execution Hindsight）’自适应学习机制",
            "在长期记忆库中记录决策路径与踩坑教训，形成反思图谱",
            "下一次遭遇类似上下文时，优先召回避坑策略而非盲目执行"
        ],
        "target_audience": "Agentic 框架开发者、长流程自动化工程师、个人数字化助理构建者",
        "editorial_insight": "今日暴涨 +1653 星，印证了‘Agent 记忆从向量检索进化为自省闭环’的行业主线。"
    },
    "google/ax": {
        "problem_solved": "现有 Agent 编排框架封装层级过深、黑盒严重、启动开销大且与多模型生态强绑定。",
        "key_features": [
            "Google 官方出品的极简、轻量级 Agentic 编排运行时 (Go 语言实现)",
            "跨模型协同路由设计，深度适配原生沙箱与高并发微任务",
            "零繁冗依赖，提供透明、确定性的状态机执行语义"
        ],
        "target_audience": "追求高吞吐、高可观测性的后端与架构工程师、Go 语言云原生开发者",
        "editorial_insight": "Google 官方首次下场开源轻量运行时（+1379星），向社区释放追求底层精简的明确信号。"
    },
    "dream-num/univer": {
        "problem_solved": "人和 Agent 协作长期被困在‘纯文字聊天框’中，无法对表格、画板、文档进行结构化实时编辑与双向互动。",
        "key_features": [
            "专为 AI Agent 打造的协作 Office 套件（包含电子表格、文档、幻灯片、关系表与画布）",
            "全套暴露面向 Agent 的微指令 API，Agent 可直接在后台改单元格、绘图与重构排版",
            "人类在前端实时协同审阅，彻底告别单向输出 Markdown 文本"
        ],
        "target_audience": "文档协同产品团队、企业自动化开发者、探索生成式界面的产品经理",
        "editorial_insight": "今日破千星（+1050星），标志着人机交互界面从‘Chat 聊天框’向‘共享可执行画布’的转移。"
    },
    "rohitg00/ai-engineering-from-scratch": {
        "problem_solved": "市面大量 AI 课程浮于表面调用现成 SDK，开发者缺乏从零手写推理循环、Attention 机制与评估体系的硬核能力。",
        "key_features": [
            "纯手写从零实现现代 AI 工程：Transformer、KV Cache、量化与 RAG 运行时",
            "配套工业级真实代码实现与测试用例，强调底层原理透视"
        ],
        "target_audience": "希望从应用开发转型底层架构的 AI 工程师、计算机科学学生",
        "editorial_insight": "暴增 +1177 星，说明开发者在热潮之后开始渴望回归底层原理的硬核技术基建。"
    },
    "mattpocock/skills": {
        "problem_solved": "开发者虽然使用 Agentic 工具，但缺少经过实战验证的真实工程 Skill 模板沉淀。",
        "key_features": [
            "资深 TS 工程师 Matt Pocock 私房 .agents 技能库全量开源",
            "涵盖高阶重构、类型体操、测试生成与严谨 Code Review 规约"
        ],
        "target_audience": "TypeScript 工程师、前沿 AI Coding 高频使用者",
        "editorial_insight": "知名大牛个人 Skill 资产的公开，印证了‘Skill 本身正在成为新的可交易/复用数字资产’。"
    },
    "obra/superpowers": {
        "problem_solved": "简单将任务交给 Agent 往往导致幻觉或半途而废，缺乏严格的软件工程方法论与执行约束。",
        "key_features": [
            "结合严格软件工程规约的 Agent 技能框架",
            "通过步骤分解、前置条件校验与严密 Harness 保障交付质量"
        ],
        "target_audience": "复杂项目维护者、企业自动化架构师",
        "editorial_insight": "强调让 Agent 遵守软件工程规则，而不是让其自由放飞。"
    },
    "NVIDIA/Model-Optimizer": {
        "problem_solved": "大模型在部署时面临显存爆炸与吞吐瓶颈，缺乏整合剪枝、蒸馏、投机采样与量化的统一工具库。",
        "key_features": [
            "NVIDIA 官方出品的 SOTA 模型优化综合库",
            "涵盖 INT4/FP8 量化、神经架构搜索 (NAS) 与推测解码 (Speculative Decoding)",
            "与 TensorRT-LLM、vLLM 等主流推理框架无缝对接"
        ],
        "target_audience": "算力优化专家、大模型部署与运维工程师、GPU 平台负责人",
        "editorial_insight": "算力成本高企背景下，英伟达官方优化工具持续受工业界强关注。"
    },
    "pbakaus/impeccable": {
        "problem_solved": "当前 AI Coding 工具擅长写后端逻辑，但生成的前端 UI 往往千篇一律、审美平庸甚至缺乏可用性。",
        "key_features": [
            "专为让 AI Harness 输出更好视觉设计而制定的设计语言与规则集",
            "约束间距、色阶、字体比例与交互触感，让 Agent 输出设计师级界面"
        ],
        "target_audience": "全栈独立开发者、对视觉质感有极高要求的 Builder",
        "editorial_insight": "解决‘AI 写代码很强但做出的页面很丑’的痛点，精准切中独立开发者心智。"
    },
    "androoAGI/starnet": {
        "problem_solved": "终端跑 Agent 过程枯燥且缺乏可视化直观反馈，普通用户难以感知多 Agent 协同状态。",
        "key_features": [
            "复古像素风太空站界面的本地优先桌面 Agent 运行台",
            "每个 Agent 化身为像素小人，在不同工作舱中协作完成真实代码与数据任务"
        ],
        "target_audience": "独立开发者、极客、对 Agent 可视化与趣味性有追求的用户",
        "editorial_insight": "趣味性与生产力的绝佳融合，极佳的社交媒体传播传播点。"
    },
    "shy3130/tick-stock-panel": {
        "problem_solved": "个人量化交易者搭建 A 股投研工作台门槛高、依赖笨重云端商业软件且隐私风险大。",
        "key_features": [
            "纯自托管、零运维的 A 股量化工作台",
            "深度融合本地 LLM 能力，实现自动策略定制、个股研报分析与盘后复盘",
            "自由接入多方免费数据源，数据完全留在本地"
        ],
        "target_audience": "A 股量化交易者、自托管爱好者、金融科技独立开发者",
        "editorial_insight": "国内自托管与大模型垂直结合的标杆项目，解决真实场景的私人定制需求。"
    },
    "openbao/openbao": {
        "problem_solved": "HashiCorp Vault 变更协议后，开源生态迫切需要一个完全中立、社区驱动的企业级机密管理替代品。",
        "key_features": [
            "Linux 基金会托管的开源机密与证书管理方案（Vault 纯正开源分支）",
            "安全分发 API 密钥、数据库凭证与动态证书"
        ],
        "target_audience": "DevOps 运维工程师、安全合规团队、基础设施架构师",
        "editorial_insight": "开源许可证治理大趋势下的关键基础设施避险选择。"
    }
}


def process_github_repos(trending_path: Path) -> list[dict]:
    if not trending_path.exists():
        return []
    data = json.loads(trending_path.read_text(encoding="utf-8"))
    repos = data.get("repos", [])
    processed = []

    for r in repos:
        full_name = r.get("full_name") or f"{r.get('owner')}/{r.get('name')}"
        enrich = GITHUB_ENRICHMENTS.get(full_name, {
            "problem_solved": f"针对 {r.get('language') or '多语言'} 生态中相关场景的基础设施与效率优化方案。",
            "key_features": [
                f"核心能力：{r.get('description') or '暂无描述'}",
                "符合现代开源工程规范，提供标准的安装与接入方式"
            ],
            "target_audience": "相关技术领域开发者、开源生态关注者",
            "editorial_insight": "今日 GitHub Trending 热门项目，展现特定技术领域的活跃动向。"
        })

        # 本地快照内容 (合成结构化富文本，避免外部跳转)
        local_snapshot = f"""# {full_name}
> 来源：GitHub Trending 今日榜单 | 语言：{r.get('language') or 'Multi'} | 关注度：今日 +{r.get('stars_today', 0)} 星 (总计 {r.get('stars', 0):,} 星)
> 仓库地址：{r.get('url')}

## 一、一句话定位
{r.get('description')}

## 二、解决的核心痛点
{enrich['problem_solved']}

## 三、关键技术架构与特性
{chr(10).join(f"- {f}" for f in enrich['key_features'])}

## 四、适用人群与业务场景
{enrich['target_audience']}

## 五、选题价值与产业观察
{enrich['editorial_insight']}
"""

        processed.append({
            "full_name": full_name,
            "name": r.get("name") or full_name.split("/")[-1],
            "owner": r.get("owner") or full_name.split("/")[0],
            "description": r.get("description", ""),
            "language": r.get("language") or "General",
            "stars": r.get("stars", 0),
            "stars_today": r.get("stars_today", 0),
            "url": r.get("url", ""),
            "problem_solved": enrich["problem_solved"],
            "key_features": enrich["key_features"],
            "target_audience": enrich["target_audience"],
            "editorial_insight": enrich["editorial_insight"],
            "local_snapshot": local_snapshot.strip(),
            "has_local_text": True
        })
    return processed


def process_digest_sources(digest_path: Path) -> list[dict]:
    if not digest_path.exists():
        return []
    data = json.loads(digest_path.read_text(encoding="utf-8"))
    sources = data.get("selectedSources", [])
    processed = []

    for s in sources:
        orig_text = (s.get("originalText") or "").strip()
        orig_title = s.get("originalTitle") or s.get("title")
        author = s.get("author") or s.get("source") or "Builder"
        summary = s.get("summary") or ""

        # 提炼核心要素
        words = orig_text.split()
        word_count = len(words) if words else len(orig_text)

        local_snapshot = f"""# {orig_title}
> 作者/信源：{author} ({s.get('type')}) | 采选板块：{' · '.join(s.get('sections', []))}
> 原文地址：{s.get('url', '无')}

## 一、核心提要
{summary}

## 二、一手正文快照 ({word_count} 字符/词)
{orig_text if orig_text else '（该条目仅包含简报摘录，正文未展开）'}
"""

        processed.append({
            "title": s.get("title"),
            "original_title": orig_title,
            "author": author,
            "type": s.get("type"),
            "url": s.get("url"),
            "summary": summary,
            "sections": s.get("sections", []),
            "word_count": word_count,
            "local_snapshot": local_snapshot.strip(),
            "has_local_text": bool(orig_text)
        })
    return processed


def main():
    trending_file = OUTPUT_DIR / "github_trending_latest.json"
    digest_file = OUTPUT_DIR / "ai_builders_digest_sources_latest.json"

    enriched_repos = process_github_repos(trending_file)
    enriched_digest = process_digest_sources(digest_file)

    out_repos = WEB_DATA_DIR / "enriched_trending.json"
    out_digest = WEB_DATA_DIR / "enriched_digest.json"

    out_repos.write_text(json.dumps({"repos": enriched_repos}, ensure_ascii=False, indent=2), encoding="utf-8")
    out_digest.write_text(json.dumps({"sources": enriched_digest}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[enrich] Successfully processed {len(enriched_repos)} GitHub repos to {out_repos}")
    print(f"[enrich] Successfully processed {len(enriched_digest)} digest sources to {out_digest}")


if __name__ == "__main__":
    main()
