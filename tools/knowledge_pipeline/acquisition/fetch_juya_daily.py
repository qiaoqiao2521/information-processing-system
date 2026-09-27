#!/usr/bin/env python3
"""
fetch_juya_daily.py: Zero-dependency harvester for 橘鸦 AI 早报 (Juya AI Daily).

Directly accesses the official daily markdown archive from daily.juya.uk/markdown/{date}.md
Parses structured categories (要闻, 开发生态, 产品应用, 技术与洞察, 行业动态).
Extracts titles, outbound links, and detailed summary commentary.
Outputs canonical Markdown digest and Knowledge Pack compatible JSON manifest.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import re
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("juya_harvester")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = Path(os.environ.get("WORKSPACE_ROOT", str(PROJECT_ROOT.parent))) / "output_to_user"

JUYA_SITE = "https://daily.juya.uk"


def get_latest_available_date() -> str:
    """Probe archive page to find the newest daily date."""
    archive_url = f"{JUYA_SITE}/archive/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(archive_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        dates = re.findall(r"(\d{4}-\d{2}-\d{2})", html)
        if dates:
            # return sorted newest
            return sorted(set(dates), reverse=True)[0]
    except Exception as e:
        logger.warning(f"Could not probe archive page: {e}")

    # Fallback to today
    return datetime.datetime.now().strftime("%Y-%m-%d")


def fetch_juya_content(date_str: str) -> Optional[str]:
    """Fetch raw markdown for given date."""
    md_url = f"{JUYA_SITE}/markdown/{date_str}.md"
    logger.info(f"Fetching Juya daily from: {md_url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(md_url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        logger.error(f"Failed to fetch {md_url}: {e}")
        return None


def parse_juya_markdown(md_text: str, date_str: str) -> Dict[str, Any]:
    """Parse Juya markdown into structured items and categories."""
    lines = md_text.splitlines()

    cover_image = ""
    for line in lines[:8]:
        m = re.match(r"^!\[\]\((.+)\)$", line.strip())
        if m:
            cover_image = m.group(1)
            break

    # Parse overview items
    categories: Dict[str, List[Dict[str, Any]]] = {}
    current_cat = "要闻"
    all_items = []

    in_overview = False
    for line in lines:
        sline = line.strip()
        if sline.startswith("## 概览"):
            in_overview = True
            continue
        if in_overview and sline.startswith("---"):
            in_overview = False
            break
        if in_overview and sline.startswith("### "):
            current_cat = sline.replace("### ", "").strip()
            continue
        if in_overview and sline.startswith("- "):
            # e.g. - 美团LongCat发布LongCat-2.5-Preview [↗](url) `#1`
            content = sline[2:].strip()
            link_match = re.search(r"\[↗\]\(([^)]+)\)", content)
            tag_match = re.search(r"`(#\d+)`", content)
            link = link_match.group(1) if link_match else ""
            tag = tag_match.group(1) if tag_match else ""

            title = content
            if link_match:
                title = title.replace(link_match.group(0), "")
            if tag_match:
                title = title.replace(tag_match.group(0), "")
            title = title.strip()

            item = {
                "title": title,
                "url": link,
                "tag": tag,
                "category": current_cat,
                "date": date_str,
            }
            categories.setdefault(current_cat, []).append(item)
            all_items.append(item)

    return {
        "date": date_str,
        "cover_image": cover_image,
        "categories": categories,
        "items": all_items,
        "raw_text": md_text,
    }


def harvest(output_dir: Path = DEFAULT_OUTPUT_DIR) -> Dict[str, Any]:
    """Harvest Juya daily and write outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = get_latest_available_date()

    raw_md = fetch_juya_content(date_str)
    if not raw_md:
        # try yesterday
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        logger.info(f"Retrying yesterday: {yesterday}")
        raw_md = fetch_juya_content(yesterday)
        date_str = yesterday

    if not raw_md:
        logger.error("Failed to acquire any Juya content.")
        return {}

    parsed = parse_juya_markdown(raw_md, date_str)
    logger.info(f"Successfully parsed {len(parsed['items'])} items from 橘鸦 AI 早报 ({date_str}).")

    # 1. Manifest
    manifest_data = {
        "source_id": "juya-ai-daily",
        "date": date_str,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "cover_image": parsed.get("cover_image", ""),
        "total_items": len(parsed["items"]),
        "items": parsed["items"],
    }
    manifest_path = output_dir / "juya_daily_sources_latest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)

    # 2. Markdown digest
    md_lines = [
        f"# 橘鸦 AI 早报精选 ({date_str})",
        "",
        f"> 数据源：`daily.juya.uk`（全网高质量 AI 新闻、大模型更新与工程动态，共 {len(parsed['items'])} 条）",
        "",
    ]
    if parsed.get("cover_image"):
        md_lines.extend([f"![早报封面]({parsed['cover_image']})", ""])

    md_lines.append("---")
    md_lines.append("")

    for cat, items in parsed["categories"].items():
        md_lines.append(f"## {cat}")
        md_lines.append("")
        for it in items:
            t = it["title"]
            u = it["url"]
            tag = it["tag"]
            if u:
                md_lines.append(f"- **[{t}]({u})** `{tag}`")
            else:
                md_lines.append(f"- **{t}** `{tag}`")
        md_lines.append("")

    digest_path = output_dir / "juya_daily_digest_latest.md"
    with open(digest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    # Also save raw copy
    raw_path = output_dir / f"juya_daily_{date_str}_raw.md"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(raw_md)

    logger.info(f"Saved Juya manifest: {manifest_path}")
    logger.info(f"Saved Juya digest: {digest_path}")

    return manifest_data


if __name__ == "__main__":
    harvest()
