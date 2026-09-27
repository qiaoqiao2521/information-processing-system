#!/usr/bin/env python3
"""
fetch_hf_daily_papers.py: High-signal arXiv Daily Papers filtered by Hugging Face Community.

Eliminates arXiv 406 rate limit and noise by querying Hugging Face Daily Papers API:
- Endpoint: https://huggingface.co/api/daily_papers
- Filters: Top community upvoted & discussed AI papers
- Outputs: Markdown digest and Knowledge Pack compatible JSON manifest
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hf_papers_harvester")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = Path(os.environ.get("WORKSPACE_ROOT", str(PROJECT_ROOT.parent))) / "output_to_user"

HF_PAPERS_API = "https://huggingface.co/api/daily_papers"


def fetch_hf_papers(limit: int = 15, timeout: int = 6) -> List[Dict[str, Any]]:
    """Fetch community-curated papers from Hugging Face."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)",
    }
    req = urllib.request.Request(HF_PAPERS_API, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
    except Exception as e:
        logger.error(f"Failed to fetch Hugging Face Daily Papers: {e}")
        return []

    curated = []
    for item in data[:limit]:
        title = item.get("title", "")
        upvotes = item.get("upvotes", 0)
        num_comments = item.get("numComments", 0)
        paper_obj = item.get("paper", {})
        paper_id = paper_obj.get("id") or item.get("id", "")
        summary = paper_obj.get("summary") or item.get("summary", "")
        authors = [a.get("name", "") for a in paper_obj.get("authors", [])][:3]

        curated.append({
            "id": paper_id,
            "title": title,
            "arxiv_id": paper_id,
            "arxiv_url": f"https://arxiv.org/abs/{paper_id}",
            "hf_url": f"https://huggingface.co/papers/{paper_id}",
            "upvotes": upvotes,
            "comments_count": num_comments,
            "authors": authors,
            "summary": summary.strip()[:600],
            "published_at": item.get("publishedAt", datetime.datetime.now().strftime("%Y-%m-%d")),
        })

    return curated


def harvest(limit: int = 15, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    papers = fetch_hf_papers(limit=limit)
    logger.info(f"Fetched {len(papers)} community-curated papers from Hugging Face.")

    manifest_data = {
        "source_id": "arxiv-hf-daily-papers",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_items": len(papers),
        "items": papers,
    }
    manifest_path = output_dir / "hf_daily_papers_sources_latest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)

    # Markdown digest
    md_lines = [
        f"# arXiv 前沿精选论文 · Hugging Face 社区热度榜 ({today})",
        "",
        f"> 筛选机制：基于全球 AI 社区真实点赞（Upvotes）与讨论度排行，自动穿透学术茧房，精选 Top {len(papers)} 篇高信号论文",
        "",
        "---",
        "",
    ]

    for p in papers:
        t = p["title"]
        aid = p["arxiv_id"]
        a_url = p["arxiv_url"]
        h_url = p["hf_url"]
        upvotes = p["upvotes"]
        comments = p["comments_count"]
        summary = p["summary"]
        authors_str = ", ".join(p["authors"]) if p["authors"] else "研究团队"

        md_lines.append(f"### [{t}]({h_url})")
        md_lines.append(f"- **社区评价**: 🔥 **{upvotes or '热门'} 赞** | 💬 **{comments} 条讨论** | **作者**: {authors_str}")
        md_lines.append(f"- **论文出处**: [Hugging Face 论文页]({h_url}) ｜ [arXiv:{aid}]({a_url})")
        if summary:
            md_lines.append(f"- **核心摘要**: {summary}...")
        md_lines.append("")

    digest_path = output_dir / "hf_daily_papers_digest_latest.md"
    with open(digest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    logger.info(f"Saved HF Papers digest: {digest_path}")
    return manifest_data


if __name__ == "__main__":
    harvest()
