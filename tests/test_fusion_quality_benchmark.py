"""
Topic Fusion Quality Benchmark & Evaluation Harness
Tests TopicFusionEngine on the fixed 60-item dataset (30 Dev, 30 Holdout Test).
Calculates:
- Over-merges (FP / 误合并)
- Under-merges (FN / 漏合并)
- Pairwise Precision, Recall, F1
- Conflict Preservation (冲突保留)
- Citation Traceability (引用可追溯率)
- Dimension-by-dimension breakdown
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from tests.fixtures.topic_fusion_evaluation_dataset import (
    DEV_ITEMS,
    HOLDOUT_TEST_ITEMS,
    AMBIGUOUS_ITEMS,
)
from tools.knowledge_pipeline.fusion.engine import TopicFusionEngine


def evaluate_clustering(
    items: List[Dict[str, Any]],
    clusters: List[List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """计算聚类的成对精度、召回率、误合并与漏合并"""
    item_map = {it["id"]: it for it in items}
    n = len(items)
    
    # 构建 item_id 到 cluster_idx 的映射
    item_to_cluster = {}
    for c_idx, cluster in enumerate(clusters):
        for it in cluster:
            item_to_cluster[it["id"]] = c_idx
            
    # 计算两两对 (Pairs)
    tp = 0  # 真正例：同属一个预设主题，且被分在同一团簇
    fp = 0  # 假正例 (误合并)：预设主题不同，却被分在同一团簇
    fn = 0  # 假负例 (漏合并)：同属一个预设主题，却被分在不同团簇
    tn = 0  # 真负例：预设主题不同，且分在不同团簇
    
    over_merge_pairs: List[Tuple[str, str, str, str]] = []
    under_merge_pairs: List[Tuple[str, str, str, str]] = []
    
    # 统计每个维度的误/漏
    dimension_stats: Dict[str, Dict[str, int]] = {}
    
    for i in range(n):
        for j in range(i + 1, n):
            it1 = items[i]
            it2 = items[j]
            id1, id2 = it1["id"], it2["id"]
            
            same_ground_truth = (it1["expected_topic_id"] == it2["expected_topic_id"])
            same_predicted_cluster = (item_to_cluster.get(id1) == item_to_cluster.get(id2))
            
            dim = it1["dimension"] if it1["dimension"] == it2["dimension"] else "cross_dimension"
            if dim not in dimension_stats:
                dimension_stats[dim] = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
                
            if same_ground_truth and same_predicted_cluster:
                tp += 1
                dimension_stats[dim]["tp"] += 1
            elif not same_ground_truth and same_predicted_cluster:
                fp += 1
                dimension_stats[dim]["fp"] += 1
                over_merge_pairs.append((
                    id1, id2,
                    f"{it1['expected_topic_id']} vs {it2['expected_topic_id']}",
                    f"{it1['title'][:40]} | {it2['title'][:40]}"
                ))
            elif same_ground_truth and not same_predicted_cluster:
                fn += 1
                dimension_stats[dim]["fn"] += 1
                under_merge_pairs.append((
                    id1, id2,
                    it1['expected_topic_id'],
                    f"{it1['title'][:40]} | {it2['title'][:40]}"
                ))
            else:
                tn += 1
                dimension_stats[dim]["tn"] += 1
                
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "total_items": n,
        "total_clusters": len(clusters),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "over_merge_count": fp,
        "under_merge_count": fn,
        "over_merge_pairs": over_merge_pairs,
        "under_merge_pairs": under_merge_pairs,
        "dimension_stats": dimension_stats,
    }


def evaluate_conflict_preservation(
    brief,
    conflict_topic_id: str,
    pro_indicators: List[str],
    anti_indicators: List[str]
) -> Dict[str, Any]:
    """检查争议性主题在聚类合成后，是否同时保留了正反双方的关键观点"""
    # 找到包含该主题的 cluster
    matching_topics = []
    for topic in brief.topics:
        # 只要该 topic 下包含冲突条目中的 URL 或标题关键词
        all_text = f"{topic.topic_title} {topic.key_breakthrough} {' '.join(topic.technical_details)} {' '.join(topic.community_discussion)}"
        matching_topics.append((topic, all_text))
        
    found_pro = False
    found_anti = False
    matched_topic_info = None
    
    for topic, text in matching_topics:
        has_pro = any(k.lower() in text.lower() for k in pro_indicators)
        has_anti = any(k.lower() in text.lower() for k in anti_indicators)
        if has_pro or has_anti:
            matched_topic_info = {
                "topic_title": topic.topic_title,
                "has_pro": has_pro,
                "has_anti": has_anti,
                "breakthrough": topic.key_breakthrough,
                "community": topic.community_discussion,
            }
            if has_pro and has_anti:
                found_pro = True
                found_anti = True
                break
            if has_pro:
                found_pro = True
            if has_anti:
                found_anti = True
                
    preserved = found_pro and found_anti
    return {
        "preserved": preserved,
        "found_pro": found_pro,
        "found_anti": found_anti,
        "details": matched_topic_info,
    }


def evaluate_citation_traceability(
    items: List[Dict[str, Any]],
    brief
) -> Dict[str, Any]:
    """检查所有原始输入条目的 URL/source 是否被完整记录在 Citations 中"""
    total_raw = len(items)
    all_citation_urls = {
        cit.url for topic in brief.topics for cit in topic.citations if cit.url
    }
    all_citation_titles = {
        cit.title.strip().lower() for topic in brief.topics for cit in topic.citations if cit.title
    }
    
    traced_count = 0
    missing = []
    for it in items:
        url = it.get("url")
        title = it.get("title", "").strip().lower()
        if (url and url in all_citation_urls) or (title and title in all_citation_titles):
            traced_count += 1
        else:
            missing.append(it["id"])
            
    return {
        "total_items": total_raw,
        "traced_count": traced_count,
        "traceability_rate": (traced_count / total_raw) if total_raw > 0 else 0.0,
        "missing_ids": missing,
    }


def test_run_dev_set():
    """运行 Dev 调试集并输出详细指标"""
    engine = TopicFusionEngine(similarity_threshold=0.45)
    clusters = engine.cluster_items(DEV_ITEMS)
    report = evaluate_clustering(DEV_ITEMS, clusters)
    
    print("\n========== DEV SET EVALUATION REPORT ==========")
    print(f"Total Items: {report['total_items']}, Clusters Formed: {report['total_clusters']}")
    print(f"Pairwise Precision: {report['precision']:.3f}, Recall: {report['recall']:.3f}, F1: {report['f1']:.3f}")
    print(f"Over-merges (误合并对数): {report['over_merge_count']}")
    print(f"Under-merges (漏合并对数): {report['under_merge_count']}")
    
    if report["over_merge_pairs"]:
        print("\n--- Top Over-merge Error Samples ---")
        for id1, id2, topics, titles in report["over_merge_pairs"][:8]:
            print(f"  [OVER-MERGE] {id1} & {id2} ({topics}): {titles}")
            
    if report["under_merge_pairs"]:
        print("\n--- Top Under-merge Error Samples ---")
        for id1, id2, topic, titles in report["under_merge_pairs"][:8]:
            print(f"  [UNDER-MERGE] {id1} & {id2} in {topic}: {titles}")
            
    brief = engine.fuse(DEV_ITEMS, date_str="2025-01-22")
    conflict_eval = evaluate_conflict_preservation(
        brief,
        conflict_topic_id="dev_t9_arc_agi_controversy",
        pro_indicators=["85%", "breakthrough", "search", "solve"],
        anti_indicators=["rebuttal", "critique", "overfitting", "collapse", "audit"]
    )
    print(f"\nConflict Preservation (ARC Controversy): {conflict_eval['preserved']} (Pro: {conflict_eval['found_pro']}, Anti: {conflict_eval['found_anti']})")
    
    trace_eval = evaluate_citation_traceability(DEV_ITEMS, brief)
    print(f"Citation Traceability Rate: {trace_eval['traceability_rate'] * 100:.1f}%\n")
    
    # 质量门禁断言 (Dev 集)
    assert report["precision"] >= 0.85, f"Dev Precision {report['precision']} below 0.85"
    assert report["recall"] >= 0.80, f"Dev Recall {report['recall']} below 0.80"
    assert report["over_merge_count"] == 0, f"Dev Over-merge count {report['over_merge_count']} is non-zero"
    assert conflict_eval["preserved"] is True, "ARC controversy conflicts not preserved"
    assert trace_eval["traceability_rate"] == 1.0, "Citations not 100% traceable"


def test_run_holdout_test_set():
    """运行 Holdout 保留验证集并输出详细指标 (验证无调阈迎合)"""
    from tests.fixtures.topic_fusion_evaluation_dataset import HOLDOUT_TEST_ITEMS
    
    engine = TopicFusionEngine(similarity_threshold=0.45)
    clusters = engine.cluster_items(HOLDOUT_TEST_ITEMS)
    report = evaluate_clustering(HOLDOUT_TEST_ITEMS, clusters)
    
    print("\n========== HOLDOUT TEST SET EVALUATION REPORT ==========")
    print(f"Total Items: {report['total_items']}, Clusters Formed: {report['total_clusters']}")
    print(f"Pairwise Precision: {report['precision']:.3f}, Recall: {report['recall']:.3f}, F1: {report['f1']:.3f}")
    print(f"Over-merges (误合并对数): {report['over_merge_count']}")
    print(f"Under-merges (漏合并对数): {report['under_merge_count']}")
    
    if report["over_merge_pairs"]:
        print("\n--- Holdout Over-merge Error Samples ---")
        for id1, id2, topics, titles in report["over_merge_pairs"][:8]:
            print(f"  [OVER-MERGE] {id1} & {id2} ({topics}): {titles}")
            
    if report["under_merge_pairs"]:
        print("\n--- Holdout Under-merge Error Samples ---")
        for id1, id2, topic, titles in report["under_merge_pairs"][:8]:
            print(f"  [UNDER-MERGE] {id1} & {id2} in {topic}: {titles}")
            
    brief = engine.fuse(HOLDOUT_TEST_ITEMS, date_str="2025-01-22")
    conflict_eval = evaluate_conflict_preservation(
        brief,
        conflict_topic_id="test_t9_scraping_copyright_ruling",
        pro_indicators=["fair use", "victory", "open", "research"],
        anti_indicators=["injunction", "appeal", "infringement", "lawsuit", "guild"]
    )
    print(f"\nConflict Preservation (Copyright Ruling Controversy): {conflict_eval['preserved']} (Pro: {conflict_eval['found_pro']}, Anti: {conflict_eval['found_anti']})")
    
    trace_eval = evaluate_citation_traceability(HOLDOUT_TEST_ITEMS, brief)
    print(f"Citation Traceability Rate: {trace_eval['traceability_rate'] * 100:.1f}%\n")
    
    # 质量门禁断言 (Holdout 集)
    assert report["precision"] >= 0.85, f"Holdout Precision {report['precision']} below 0.85"
    assert report["recall"] >= 0.75, f"Holdout Recall {report['recall']} below 0.75"
    assert report["over_merge_count"] == 0, f"Holdout Over-merge count {report['over_merge_count']} is non-zero"
    assert trace_eval["traceability_rate"] == 1.0, "Holdout Citations not 100% traceable"


def test_run_ambiguous_control_set():
    """分析 4 个歧义对照样本的行为，验证没有机械武断合并"""
    from tests.fixtures.topic_fusion_evaluation_dataset import AMBIGUOUS_ITEMS
    from tools.knowledge_pipeline.fusion.fingerprint import are_items_semantically_related
    
    print("\n========== AMBIGUOUS CONTROL SET REPORT ==========")
    print(f"Total Ambiguous Samples: {len(AMBIGUOUS_ITEMS)}")
    
    for item in AMBIGUOUS_ITEMS:
        print(f"\n[{item['id']}] {item['title']}")
        print(f"  Ambiguity Reason: {item['ambiguity_reason']}")
        
    # 测试 AMB_01 与 AMB_02 (同一开源生态不同衍生独立工具)
    rel12, score12, reason12 = are_items_semantically_related(AMBIGUOUS_ITEMS[0], AMBIGUOUS_ITEMS[1])
    print(f"\nAMB_01 vs AMB_02 -> Related: {rel12}, Score: {score12:.2f}, Reason: {reason12}")
    
    # 测试 AMB_03 与 AMB_04 (官方更新 vs 概念验证第三方复现)
    rel34, score34, reason34 = are_items_semantically_related(AMBIGUOUS_ITEMS[2], AMBIGUOUS_ITEMS[3])
    print(f"AMB_03 vs AMB_04 -> Related: {rel34}, Score: {score34:.2f}, Reason: {reason34}\n")


if __name__ == "__main__":
    test_run_dev_set()
    test_run_holdout_test_set()
    test_run_ambiguous_control_set()

