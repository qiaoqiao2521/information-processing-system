#!/usr/bin/env python3
"""
fetch_qiaomu_rss.py: Zero-dependency harvester for Qiaomu RSS ecosystem feeds.

Ingests curated feeds from:
- tidings.json: 718 curated AI, tech, podcasts & engineering feeds
- independent-blogs.json: 1,342 Chinese independent developer blogs

Features:
- Pure Python 3 standard library (zero external pip packages).
- Robust XML parsing for both RSS 2.0 (<channel><item>) and Atom (<feed><entry>).
- Pack-based filtering ('ai', 'top200', 'weeklies', 'engineering', 'chinese').
- OPML export for universal RSS readers (Follow, NetNewsWire, Reeder).
- Downstream manifest generation compatible with knowledge_pack schema.
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import logging
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("qiaomu_rss_harvester")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "qiaomu-rss"
TIDINGS_FILE = DATA_DIR / "tidings.json"
BLOGS_FILE = DATA_DIR / "independent-blogs.json"

DEFAULT_OUTPUT_DIR = Path(os.environ.get("WORKSPACE_ROOT", str(PROJECT_ROOT.parent))) / "output_to_user"


def parse_xml_entry(item_elem: ET.Element, is_atom: bool = False) -> Optional[Dict[str, Any]]:
    """Parse RSS <item> or Atom <entry> into a standardized dict."""
    def clean_text(text: Optional[str]) -> str:
        if not text:
            return ""
        # Strip HTML tags
        clean = re.sub(r"<[^>]+>", " ", text)
        clean = html.unescape(clean)
        return " ".join(clean.split())

    title, link, desc, pub_date = "", "", "", ""

    if is_atom:
        for child in item_elem:
            tag = child.tag.split("}")[-1].lower()
            if tag == "title":
                title = clean_text(child.text)
            elif tag == "link":
                href = child.attrib.get("href") or child.text
                rel = child.attrib.get("rel", "alternate")
                if href and (rel == "alternate" or not link):
                    link = href.strip()
            elif tag in ("summary", "content"):
                if not desc:
                    desc = clean_text(child.text)
            elif tag in ("published", "updated"):
                if not pub_date:
                    pub_date = (child.text or "").strip()
    else:  # RSS 2.0
        for child in item_elem:
            tag = child.tag.split("}")[-1].lower()
            if tag == "title":
                title = clean_text(child.text)
            elif tag == "link":
                link = (child.text or "").strip()
            elif tag in ("description", "encoded"):
                if not desc:
                    desc = clean_text(child.text)
            elif tag in ("pubdate", "date"):
                if not pub_date:
                    pub_date = (child.text or "").strip()

    if not title and not link:
        return None

    return {
        "title": title or "Untitled",
        "url": link,
        "summary": desc[:500] if desc else "",
        "published_at": pub_date,
    }


def fetch_feed_items(feed_url: str, timeout: int = 8, max_items: int = 5) -> List[Dict[str, Any]]:
    """Fetch and parse feed items using urllib and ElementTree."""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    }
    req = urllib.request.Request(feed_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read()
    except Exception as e:
        logger.debug(f"Failed to fetch {feed_url}: {e}")
        return []

    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return []

    tag = root.tag.split("}")[-1].lower()
    is_atom = tag == "feed"

    items = []
    if is_atom:
        for entry in root.findall("{*}entry"):
            parsed = parse_xml_entry(entry, is_atom=True)
            if parsed and parsed.get("url"):
                items.append(parsed)
            if len(items) >= max_items:
                break
    else:
        channel = root.find("channel") or root.find("{*}channel") or root
        for item in channel.findall("item") or channel.findall("{*}item"):
            parsed = parse_xml_entry(item, is_atom=False)
            if parsed and parsed.get("url"):
                items.append(parsed)
            if len(items) >= max_items:
                break

    return items


def load_curated_feeds(pack: str = "ai", limit: int = 50) -> List[Dict[str, Any]]:
    """Load and filter feeds from tidings.json and independent-blogs.json."""
    selected_feeds: List[Dict[str, Any]] = []

    if TIDINGS_FILE.exists():
        with open(TIDINGS_FILE, "r", encoding="utf-8") as f:
            tidings = json.load(f)
        for feed in tidings.get("feeds", []):
            packs = feed.get("packs", [])
            feed_url = feed.get("feed_url")
            if not feed_url:
                continue
            if pack == "all" or pack in packs:
                selected_feeds.append({
                    "id": feed.get("id"),
                    "title": feed.get("title", "Unknown Feed"),
                    "feed_url": feed_url,
                    "site_url": feed.get("site_url", ""),
                    "category": feed.get("category", "General"),
                    "packs": packs,
                    "language": feed.get("language", "zh"),
                })
            if len(selected_feeds) >= limit:
                break

    if len(selected_feeds) < limit and pack in ("all", "blogs", "chinese", "personal") and BLOGS_FILE.exists():
        with open(BLOGS_FILE, "r", encoding="utf-8") as f:
            blogs = json.load(f)
        for item in blogs.get("items", []):
            url = item.get("url")
            if not url:
                continue
            selected_feeds.append({
                "id": item.get("id"),
                "title": item.get("name", "Blog"),
                "feed_url": url,
                "site_url": item.get("site", ""),
                "category": "Independent Blog",
                "packs": ["blogs", "chinese"],
                "language": "zh",
                "tags": item.get("tags", []),
            })
            if len(selected_feeds) >= limit:
                break

    return selected_feeds


def export_opml(feeds: List[Dict[str, Any]], out_path: Path):
    """Export feed collection to universal OPML 2.0 format."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<opml version="2.0">',
        '  <head>',
        '    <title>Qiaomu RSS Ecosystem Feeds</title>',
        f'    <dateCreated>{datetime.datetime.now(datetime.timezone.utc).isoformat()}</dateCreated>',
        '  </head>',
        '  <body>',
    ]

    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for f in feeds:
        cat = f.get("category", "General")
        by_category.setdefault(cat, []).append(f)

    for cat, cat_feeds in by_category.items():
        lines.append(f'    <outline text="{html.escape(cat)}" title="{html.escape(cat)}">')
        for f in cat_feeds:
            title = html.escape(f.get("title", "Feed"))
            feed_url = html.escape(f.get("feed_url", ""))
            site_url = html.escape(f.get("site_url", ""))
            lines.append(f'      <outline type="rss" text="{title}" title="{title}" xmlUrl="{feed_url}" htmlUrl="{site_url}"/>')
        lines.append('    </outline>')

    lines.extend(['  </body>', '</opml>'])
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info(f"Exported OPML with {len(feeds)} feeds to {out_path}")


def harvest(pack: str = "ai", sample_size: int = 15, items_per_feed: int = 3, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Dict[str, Any]:
    """Harvest recent articles from selected feeds."""
    feeds = load_curated_feeds(pack=pack, limit=sample_size)
    logger.info(f"Loaded {len(feeds)} candidate feeds for pack '{pack}'. Harvesting...")

    harvested_items = []
    feed_stats = {"total_feeds": len(feeds), "successful_feeds": 0, "total_items": 0}

    for f in feeds:
        feed_url = f["feed_url"]
        logger.info(f"Polling [{f['title']}] -> {feed_url}")
        items = fetch_feed_items(feed_url, timeout=6, max_items=items_per_feed)
        if items:
            feed_stats["successful_feeds"] += 1
            for it in items:
                it["feed_title"] = f["title"]
                it["feed_category"] = f.get("category", "Tech")
                it["feed_language"] = f.get("language", "zh")
                it["source_pack"] = pack
                harvested_items.append(it)

    feed_stats["total_items"] = len(harvested_items)
    logger.info(f"Harvest complete. Got {len(harvested_items)} items from {feed_stats['successful_feeds']} feeds.")

    # Write outputs
    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    # 1. Manifest JSON
    manifest_data = {
        "source_id": "qiaomu-rss-ecosystem",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pack": pack,
        "stats": feed_stats,
        "items": harvested_items,
    }
    manifest_path = output_dir / "qiaomu_rss_sources_latest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)

    # 2. Markdown Digest
    md_lines = [
        f"# 乔木 RSS 生态精选简报 ({today})",
        "",
        f"> 策展范围：**{pack.upper()}** 精选池（覆盖 {feed_stats['successful_feeds']}/{feed_stats['total_feeds']} 个活跃源，共采纳 {feed_stats['total_items']} 条前沿长文）",
        "",
        "---",
        "",
    ]

    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for item in harvested_items:
        by_cat.setdefault(item.get("feed_category", "综合前沿"), []).append(item)

    for cat, items in by_cat.items():
        md_lines.append(f"## {cat}")
        md_lines.append("")
        for it in items:
            title = it["title"]
            url = it["url"]
            source = it["feed_title"]
            pub = it.get("published_at", "")
            summary = it.get("summary", "")
            md_lines.append(f"### [{title}]({url})")
            md_lines.append(f"- **来源**: {source} | **发布时间**: {pub or '近期'}")
            if summary:
                md_lines.append(f"- **核心摘要**: {summary[:200]}...")
            md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    digest_path = output_dir / "qiaomu_rss_digest_latest.md"
    with open(digest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    logger.info(f"Saved manifest: {manifest_path}")
    logger.info(f"Saved digest: {digest_path}")

    return manifest_data


def main():
    parser = argparse.ArgumentParser(description="Qiaomu RSS Harvester")
    parser.add_argument("--pack", default="ai", help="Feed pack: ai, engineering, weeklies, top200, all")
    parser.add_argument("--limit", type=int, default=20, help="Number of feeds to sample")
    parser.add_argument("--items-per-feed", type=int, default=3, help="Max items per feed")
    parser.add_argument("--export-opml", type=str, help="Export OPML to given path")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Output directory")

    args = parser.parse_args()

    if args.export_opml:
        feeds = load_curated_feeds(pack=args.pack, limit=args.limit)
        export_opml(feeds, Path(args.export_opml))
        return

    harvest(
        pack=args.pack,
        sample_size=args.limit,
        items_per_feed=args.items_per_feed,
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()
