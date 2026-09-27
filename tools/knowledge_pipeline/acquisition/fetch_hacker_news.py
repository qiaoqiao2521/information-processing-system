#!/usr/bin/env python3
"""
fetch_hacker_news.py: Zero-dependency harvester for Hacker News top tech & AI stories.

Fetches live frontpage stories from news.ycombinator.com/rss.
Extracts title, external URL, HN discussion comments link, and published date.
Categorizes stories (AI / LLM / Agent, Developer Tools & Infra, General Tech).
Outputs canonical Markdown digest and Knowledge Pack compatible JSON manifest.
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import logging
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hn_harvester")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = Path(os.environ.get("WORKSPACE_ROOT", str(PROJECT_ROOT.parent))) / "output_to_user"

HN_RSS_URL = "https://news.ycombinator.com/rss"


def fetch_hn_stories(timeout: int = 6) -> List[Dict[str, Any]]:
    """Fetch stories from Hacker News RSS."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    }
    req = urllib.request.Request(HN_RSS_URL, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
    except Exception as e:
        logger.error(f"Failed to fetch Hacker News RSS: {e}")
        return []

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML: {e}")
        return []

    stories = []
    channel = root.find("channel") or root
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        comments_link = (item.findtext("comments") or "").strip()

        # Extract item ID from comments link (e.g. id=49853175)
        item_id = ""
        m = re.search(r"id=(\d+)", comments_link)
        if m:
            item_id = m.group(1)

        # Categorize
        category = "General Tech"
        ai_pattern = r"(ai|llm|gpt|agent|claude|gemini|openai|anthropic|deepseek|model|reasoning|prompt|rag|vision|neural)"
        infra_pattern = r"(database|postgres|linux|kernel|rust|python|compiler|build|cloud|k8s|kubernetes|security|browser)"
        
        if re.search(ai_pattern, title, re.IGNORECASE):
            category = "AI & LLM Frontier"
        elif re.search(infra_pattern, title, re.IGNORECASE):
            category = "Dev Tools & Infra"
        elif title.startswith("Show HN:"):
            category = "Show HN (New Launches)"
        elif title.startswith("Ask HN:"):
            category = "Ask HN (Discussions)"

        stories.append({
            "id": item_id,
            "title": html.unescape(title),
            "url": link,
            "comments_url": comments_link or f"https://news.ycombinator.com/item?id={item_id}",
            "category": category,
            "published_at": pub_date,
        })

    return stories


def harvest(output_dir: Path = DEFAULT_OUTPUT_DIR) -> Dict[str, Any]:
    """Execute harvest and write output files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    stories = fetch_hn_stories()
    logger.info(f"Fetched {len(stories)} stories from Hacker News.")

    manifest_data = {
        "source_id": "hacker-news",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_items": len(stories),
        "items": stories,
    }
    manifest_path = output_dir / "hacker_news_sources_latest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)

    # Markdown digest
    md_lines = [
        f"# Hacker News 全球科技精选 ({today})",
        "",
        f"> 数据源：`news.ycombinator.com` 实时热榜（精选 {len(stories)} 条全球前沿议题）",
        "",
        "---",
        "",
    ]

    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for s in stories:
        by_cat.setdefault(s["category"], []).append(s)

    # Preferred order
    order = ["AI & LLM Frontier", "Show HN (New Launches)", "Dev Tools & Infra", "Ask HN (Discussions)", "General Tech"]
    for cat in order:
        items = by_cat.get(cat, [])
        if not items:
            continue
        md_lines.append(f"## {cat}")
        md_lines.append("")
        for it in items:
            t = it["title"]
            u = it["url"]
            c_url = it["comments_url"]
            pub = it["published_at"]
            md_lines.append(f"### [{t}]({u})")
            md_lines.append(f"- **讨论入口**: [Hacker News 评论区]({c_url}) | **发布时间**: {pub}")
            md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    digest_path = output_dir / "hacker_news_digest_latest.md"
    with open(digest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    logger.info(f"Saved HN manifest: {manifest_path}")
    logger.info(f"Saved HN digest: {digest_path}")

    return manifest_data


if __name__ == "__main__":
    harvest()
