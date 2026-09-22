"""
跨源语义去重与主题聚类融合引擎核心实现 (Topic Fusion Engine)
采用 Average-Linkage 层次聚类算法，根治单链传递击穿（Chaining Problem），
支持观点冲突双向保留与三层高密度摘要提炼。
"""
from __future__ import annotations

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Any, List, Dict, Tuple, Set

from .models import (
    SourceCitation,
    TopicCluster,
    ConsolidatedDailyBrief,
)
from .fingerprint import (
    extract_entities,
    are_items_semantically_related,
)


# 观点冲突关键词词典
PRO_KEYWORDS = {
    "breakthrough", "claims", "achievement", "victory", "transformative",
    "fair use", "unlocked", "milestone", "applauds", "superior", "exceeds"
}
CON_KEYWORDS = {
    "rebuttal", "critique", "overfitting", "caution", "dispute", "appeal",
    "memorization", "infringement", "collapse", "audit", "warning", "flawed",
    "reversal", "denounce", "overturn"
}


def categorize_topic(topic_title: str, tags: List[str], entities: List[str]) -> str:
    """自动判断主题分类"""
    lower_text = f"{topic_title} {' '.join(tags)} {' '.join(entities)}".lower()
    
    if any(k in lower_text for k in ["robot", "arm", "slam", "ros2", "nav2", "hardware", "firmware", "lidar", "humanoid", "boston"]):
        return "Robotics & Embodied AI"
    elif any(k in lower_text for k in ["agent", "harness", "reasoning", "orchestrat", "mcp", "tool", "autogen", "langchain"]):
        return "AI Agents & Tooling"
    elif any(k in lower_text for k in ["model", "llm", "transformer", "arxiv", "paper", "dataset", "benchmark", "deepseek", "llama", "qwen", "moe", "r1"]):
        return "Foundational Models & Research"
    elif any(k in lower_text for k in ["browser", "web", "automation", "scraping", "operator"]):
        return "Browser & Web Automation"
    elif any(k in lower_text for k in ["postgres", "pgvector", "milvus", "qdrant", "database", "python", "no-gil", "system", "infra", "mongodb"]):
        return "Systems & Infrastructure"
    elif any(k in lower_text for k in ["crypto", "finance", "regulation", "sec", "nydfs", "exchange"]):
        return "Fintech & Digital Assets"
    return "AI & Technology Breakthroughs"


def synthesize_cluster_layers(items: List[Dict[str, Any]]) -> Tuple[str, List[str], List[str]]:
    """
    分层提取并合成：
    1. 【关键突破】(Key Breakthrough)
    2. 【技术细节】(Technical Details)
    3. 【社区与产业讨论 / 争议核实】(Community & Industry Discussion / Controversy)
    """
    # 按照信源类型划分信息
    arxiv_items = [it for it in items if "arxiv" in it.get("source_id", "").lower()]
    github_items = [it for it in items if "builderpulse" in it.get("source_id", "").lower() or "github" in it.get("source_id", "").lower()]
    news_items = [it for it in items if it not in arxiv_items and it not in github_items]
    
    # 1. 关键突破：以最具代表性的标题和摘要为核心
    primary_item = items[0]
    if news_items:
        primary_item = news_items[0]
    elif github_items:
        primary_item = github_items[0]
        
    lead_title = primary_item.get("title", "").strip()
    lead_summary = (primary_item.get("summary") or primary_item.get("raw_text") or "").strip()
    
    first_sentence = lead_summary.split("\n")[0] if lead_summary else lead_title
    if len(first_sentence) > 200:
        first_sentence = first_sentence[:197] + "..."
    key_breakthrough = f"{lead_title}：{first_sentence}"

    # 2. 技术细节：从论文、代码仓库或技术摘要中提取
    tech_details: List[str] = []
    
    for it in arxiv_items:
        title = it.get("title", "")
        summary = (it.get("summary") or it.get("raw_text") or "").strip()
        short_summary = summary.replace("\n", " ")[:240]
        tech_details.append(f"【学术论文/理论】《{title}》：{short_summary}...")
        
    for it in github_items:
        title = it.get("title", "")
        desc = (it.get("summary") or it.get("raw_text") or "").strip()
        url = it.get("url", "")
        tech_details.append(f"【代码仓库/架构实现】{title} ({url})：{desc[:200]}")
        
    if not tech_details:
        for it in items[:2]:
            s = it.get("summary", "")
            if s and s != first_sentence:
                tech_details.append(s[:220])

    # 3. 社区反响与观点冲突保留
    community_notes: List[str] = []
    
    # 检测团簇内是否存在观点冲突对立
    pro_items = []
    con_items = []
    for it in items:
        all_text = f"{it.get('title', '')} {it.get('summary', '')}".lower()
        has_pro = any(k in all_text for k in PRO_KEYWORDS)
        has_con = any(k in all_text for k in CON_KEYWORDS)
        if has_pro:
            pro_items.append(it)
        if has_con:
            con_items.append(it)
            
    is_controversial = bool(pro_items and con_items)
    
    if is_controversial:
        community_notes.append("【观点分歧与多方立场核查】:")
        for it in pro_items[:2]:
            s_snip = (it.get("summary") or "")[:120].replace("\n", " ")
            community_notes.append(f"  - [突破主张/支持方] {it.get('title')}: {s_snip}...")
        for it in con_items[:2]:
            s_snip = (it.get("summary") or "")[:120].replace("\n", " ")
            community_notes.append(f"  - [质疑反驳/审慎方] {it.get('title')}: {s_snip}...")
        community_notes.append("本主题存在显著学术或行业观点争议，各方论据与出处均已完整保留收录。")
    else:
        for it in news_items:
            source_name = it.get("source_id", "资讯")
            title = it.get("title", "")
            selected_reason = it.get("selected_reason", "")
            if selected_reason:
                community_notes.append(f"[{source_name}] 采选动因与背景：{selected_reason}")
            else:
                community_notes.append(f"[{source_name}] 报道聚焦：{title}")
                
        if len(items) > 1:
            sources_list = ", ".join(sorted({it.get("source_id", "unknown") for it in items}))
            community_notes.append(f"本事件同时被多源关注报道 ({sources_list})，呈现跨界协同讨论趋势。")
        
    return key_breakthrough, tech_details, community_notes


class TopicFusionEngine:
    """跨源语义去重与主题聚类引擎"""
    
    def __init__(self, similarity_threshold: float = 0.45):
        self.similarity_threshold = similarity_threshold

    def cluster_items(self, items: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        基于 Average-Linkage 凝聚层次聚类，杜绝并查集单链击穿（Chaining Problem）。
        只有当两组材料的平均相似度超过阈值，且不存在硬冲突时，才允许融合。
        """
        if not items:
            return []
            
        n = len(items)
        
        # 预计算成对相似度矩阵与关联标记
        score_matrix = [[0.0] * n for _ in range(n)]
        related_matrix = [[False] * n for _ in range(n)]
        conflict_matrix = [[False] * n for _ in range(n)]
        
        for i in range(n):
            score_matrix[i][i] = 1.0
            related_matrix[i][i] = True
            for j in range(i + 1, n):
                rel, score, reason = are_items_semantically_related(
                    items[i], items[j], sim_threshold=self.similarity_threshold
                )
                score_matrix[i][j] = score
                score_matrix[j][i] = score
                related_matrix[i][j] = rel
                related_matrix[j][i] = rel
                if reason.startswith("conflict:"):
                    conflict_matrix[i][j] = True
                    conflict_matrix[j][i] = True
                
        # 初始化：每个元素自成一个团簇
        clusters: List[List[int]] = [[i] for i in range(n)]
        
        while len(clusters) > 1:
            best_pair: Tuple[int, int] | None = None
            best_avg_sim = 0.0
            
            for a in range(len(clusters)):
                for b in range(a + 1, len(clusters)):
                    ca = clusters[a]
                    cb = clusters[b]
                    
                    # 强判据要求：两团簇之间必须至少有一对元素被明确判定为 related
                    has_related = any(related_matrix[i][j] for i in ca for j in cb)
                    if not has_related:
                        continue
                        
                    # 显式硬冲突拦截：两团簇之间任意元素均不得存在显式冲突 (版本/领域/旧闻/综述隔离)
                    has_hard_conflict = any(conflict_matrix[i][j] for i in ca for j in cb)
                    if has_hard_conflict:
                        continue
                        
                    # 计算团簇间所有两两对的平均相似度 (Average Linkage)
                    cross_scores = [score_matrix[i][j] for i in ca for j in cb]
                    avg_sim = sum(cross_scores) / len(cross_scores)
                    min_sim = min(cross_scores)
                    
                    # 聚合条件：平均相似度达标，且最小相似度不至于过分撕裂
                    if avg_sim >= self.similarity_threshold and (min_sim >= 0.12 or len(ca) + len(cb) <= 4):
                        if avg_sim > best_avg_sim:
                            best_avg_sim = avg_sim
                            best_pair = (a, b)
                            
            if best_pair is not None:
                a, b = best_pair
                clusters[a] = clusters[a] + clusters[b]
                clusters.pop(b)
            else:
                break
                
        return [[items[idx] for idx in c] for c in clusters]

    def fuse(self, raw_items: List[Dict[str, Any]], date_str: str | None = None) -> ConsolidatedDailyBrief:
        """执行完整聚类融合管线，产出结构化的高密度日报数据"""
        if not date_str:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
        clusters = self.cluster_items(raw_items)
        topic_clusters: List[TopicCluster] = []
        
        for cluster in clusters:
            primary_title = max([it.get("title", "") for it in cluster], key=lambda t: len(t.strip()))
            
            all_text = "\n".join([f"{it.get('title', '')}\n{it.get('summary', '')}" for it in cluster])
            entities = extract_entities(all_text)
            
            tags = sorted({t for it in cluster for t in it.get("tags", []) if t})
            observed_sources = sorted({it.get("source_id", "unknown") for it in cluster})
            
            key_breakthrough, tech_details, community_disc = synthesize_cluster_layers(cluster)
            
            citations: List[SourceCitation] = []
            seen_urls = set()
            for it in cluster:
                url = it.get("url")
                if url and url in seen_urls:
                    continue
                if url:
                    seen_urls.add(url)
                citations.append(SourceCitation(
                    source_id=it.get("source_id", "unknown"),
                    title=it.get("title", "Untitled"),
                    url=url,
                    canonical_url=it.get("metadata", {}).get("canonical_url"),
                    snippet=(it.get("summary") or "")[:180],
                    published_at=it.get("published_at") or it.get("freshness", {}).get("published_at")
                ))

            id_seed = f"{entities[:3]}_{primary_title[:30]}"
            topic_id = "topic_" + hashlib.sha256(id_seed.encode("utf-8")).hexdigest()[:12]

            category = categorize_topic(primary_title, tags, entities)

            topic_clusters.append(TopicCluster(
                topic_id=topic_id,
                topic_title=primary_title,
                primary_category=category,
                entities=entities[:10],
                key_breakthrough=key_breakthrough,
                technical_details=tech_details,
                community_discussion=community_disc,
                observed_sources=observed_sources,
                citations=citations,
                tags=tags,
                raw_item_count=len(cluster)
            ))

        total_raw = len(raw_items)
        total_fused = len(topic_clusters)
        reduction = ((total_raw - total_fused) / total_raw * 100) if total_raw > 0 else 0.0
        
        return ConsolidatedDailyBrief(
            date=date_str,
            total_raw_items=total_raw,
            total_topics=total_fused,
            compression_ratio=f"{reduction:.1f}% 去重与聚合",
            topics=topic_clusters
        )

    def render_markdown(self, brief: ConsolidatedDailyBrief) -> str:
        """将结构化高密度简报渲染为适合 NotebookLM 和阅读的优雅 Markdown"""
        lines = [
            f"# 每日情报高密度聚类总报 ({brief.date})",
            "",
            "> **跨源语义融合层产出**：通过实体识别与语义相似度网络，合并 ArXiv、GitHub、News 等多源重复采集，提炼高密度深度情报。",
            "",
            f"- **原始情报输入**: {brief.total_raw_items} 条",
            f"- **融合深度主题**: {brief.total_topics} 项",
            f"- **去重降噪压缩率**: {brief.compression_ratio}",
            f"- **生成时间**: `{brief.generated_at}`",
            "",
            "---",
            ""
        ]
        
        by_category: Dict[str, List[TopicCluster]] = {}
        for top in brief.topics:
            by_category.setdefault(top.primary_category, []).append(top)
            
        for cat, topics in by_category.items():
            lines.append(f"## 📌 领域板块：{cat}")
            lines.append("")
            
            for t in topics:
                cross_source_badge = f" [多源交叉验证: {', '.join(t.observed_sources)}]" if len(t.observed_sources) > 1 else f" [{t.observed_sources[0]}]"
                lines.append(f"### 🔥 {t.topic_title}{cross_source_badge}")
                if t.entities:
                    lines.append(f"**核心实体**: `{ '` · `'.join(t.entities) }`")
                lines.append("")
                
                # 1. 关键突破
                lines.append(f"**💡 【关键突破】**: {t.key_breakthrough}")
                lines.append("")
                
                # 2. 技术细节
                if t.technical_details:
                    lines.append("**⚙️ 【技术细节与架构】**:")
                    for td in t.technical_details:
                        lines.append(f"- {td}")
                    lines.append("")
                    
                # 3. 社区反响与争议
                if t.community_discussion:
                    lines.append("**💬 【社区反响与产业影响】**:")
                    for cd in t.community_discussion:
                        lines.append(f"- {cd}")
                    lines.append("")
                    
                # 溯源清单
                if t.citations:
                    lines.append("**🔗 溯源凭据与原文链接**:")
                    for cit in t.citations:
                        url_str = f"({cit.url})" if cit.url else ""
                        lines.append(f"  - [{cit.source_id}] {cit.title} {url_str}")
                    lines.append("")
                    
                lines.append("---")
                lines.append("")
                
        return "\n".join(lines)
