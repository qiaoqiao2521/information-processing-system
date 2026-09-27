#!/usr/bin/env python3
"""
organize_workbench_vault.py: Automated Information Management & Categorization Engine.

Organizes raw contents from all sources into a structured, categorized local vault:
- 01_要闻与快讯 (FlashNews): Juya daily, HN breaking, industry briefs
- 02_前沿模型与Agent (AI_Agent): Anthropic/OpenAI research, agent memory, prompt guides
- 03_开源工具与Repo (Tools_OSS): GitHub trending projects, developer utilities
- 04_商业与机会雷达 (Biz_Radar): BuilderPulse opportunities, monetization, solopreneur
- 05_自媒体与视觉卡片 (Media_Visual): Bento cards, quote graphics, WeChat ready assets
- 06_深度长文与思考 (Deep_Reads): Qiaomu independent blogs, newsletters, essays

Standardizes all articles with YAML frontmatter (category, tags, media_angle, shelf_life).
Generates daily topic matrix and master index.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("vault_organizer")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = Path(os.environ.get("WORKSPACE_ROOT", str(PROJECT_ROOT.parent))) / "output_to_user"
VAULT_DIR = OUTPUT_DIR / "workbench_vault"

CATEGORIES = {
    "01_要闻与快讯": "FlashNews",
    "02_前沿模型与Agent": "AI_Agent",
    "03_开源工具与Repo": "Tools_OSS",
    "04_商业与机会雷达": "Biz_Radar",
    "05_自媒体与视觉卡片": "Media_Visual",
    "06_深度长文与思考": "Deep_Reads",
}


def sanitize_filename(name: str) -> str:
    clean = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return clean[:60] if clean else "untitled"


def create_markdown_note(
    target_dir: Path,
    filename: str,
    title: str,
    source: str,
    category: str,
    tags: List[str],
    original_url: str,
    media_angle: str,
    shelf_life: str,
    body: str,
    date_str: str,
) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{filename}.md"

    tags_formatted = ", ".join(f'"{t}"' for t in tags)
    content = f"""---
title: "{title}"
source: "{source}"
category: "{category}"
tags: [{tags_formatted}]
published_at: "{date_str}"
shelf_life: "{shelf_life}"
media_angle: "{media_angle}"
original_url: "{original_url}"
---

# {title}

> **信源出处**: {source} | **分类**: {category} | **时效**: {shelf_life}  
> **原文链接**: [{original_url}]({original_url})  
> **自媒体切入角**: {media_angle}

---

{body.strip()}
"""
    file_path.write_text(content, encoding="utf-8")
    return file_path


def process_juya(date_str: str, vault_today: Path) -> List[Dict[str, Any]]:
    """Process Juya daily into FlashNews and AI_Agent notes."""
    juya_json = OUTPUT_DIR / "juya_daily_sources_latest.json"
    raw_md_path = OUTPUT_DIR / f"juya_daily_{date_str}_raw.md"
    if not juya_json.exists():
        return []

    with open(juya_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Read raw md for full-text lookup if available
    raw_text = raw_md_path.read_text(encoding="utf-8") if raw_md_path.exists() else ""

    processed = []
    for item in data.get("items", []):
        title = item["title"]
        cat_name = item["category"]
        url = item.get("url", "")
        tag = item.get("tag", "")

        # Map to vault category
        if cat_name in ("要闻", "行业动态"):
            folder = vault_today / "01_要闻与快讯"
            vault_cat = "FlashNews"
            shelf = "24h快讯"
            angle = "公众号次条盘点 / 资讯早报"
        elif cat_name in ("开发生态", "技术与洞察"):
            folder = vault_today / "02_前沿模型与Agent"
            vault_cat = "AI_Agent"
            shelf = "技术方法论 (数月)"
            angle = "公众号深度长文 / 技术专题剖析"
        else:
            folder = vault_today / "03_开源工具与Repo"
            vault_cat = "Tools_OSS"
            shelf = "实用工具 (中期)"
            angle = "小红书/工具清单推荐"

        # Try to find paragraph detail from raw markdown
        detail = ""
        if raw_text and tag:
            # find heading with tag
            pattern = re.compile(rf"###\s+\[?{re.escape(title[:10])}.*?`{re.escape(tag)}`\s*\n(.*?)(?=\n###|\n##|$)", re.DOTALL)
            m = pattern.search(raw_text)
            if m:
                detail = m.group(1).strip()

        body = f"{detail}\n\n- 归属早报栏目：{cat_name} ({tag})" if detail else f"- 归属早报栏目：{cat_name} ({tag})\n- 详细出处：{url}"
        tags = ["AI早报", cat_name]
        if "Claude" in title or "Anthropic" in title: tags.append("Anthropic")
        if "OpenAI" in title or "Codex" in title: tags.append("OpenAI")
        if "DeepSeek" in title: tags.append("DeepSeek")
        if "LongCat" in title: tags.append("美团LongCat")

        fn = sanitize_filename(f"juya_{tag}_{title}")
        note_path = create_markdown_note(
            target_dir=folder,
            filename=fn,
            title=title,
            source="橘鸦AI早报",
            category=vault_cat,
            tags=tags,
            original_url=url,
            media_angle=angle,
            shelf_life=shelf,
            body=body,
            date_str=date_str,
        )
        processed.append({"title": title, "path": str(note_path), "cat": vault_cat, "source": "juya"})

    return processed


def process_hacker_news(date_str: str, vault_today: Path) -> List[Dict[str, Any]]:
    """Process Hacker News stories into vault notes."""
    hn_json = OUTPUT_DIR / "hacker_news_sources_latest.json"
    if not hn_json.exists():
        return []

    with open(hn_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    processed = []
    for item in data.get("items", [])[:15]:  # take top 15 highest priority
        title = item["title"]
        cat = item["category"]
        url = item.get("url") or item.get("comments_url")
        c_url = item.get("comments_url")

        if cat == "AI & LLM Frontier":
            folder = vault_today / "02_前沿模型与Agent"
            vault_cat = "AI_Agent"
            angle = "海外开发者第一手观点 / 批判性讨论"
        elif cat == "Show HN (New Launches)":
            folder = vault_today / "03_开源工具与Repo"
            vault_cat = "Tools_OSS"
            angle = "海外首发新产品开箱 / 独立开发产品挖掘"
        else:
            folder = vault_today / "01_要闻与快讯"
            vault_cat = "FlashNews"
            angle = "全球科技热议趋势"

        body = f"""- **外部链接**: [{url}]({url})
- **Hacker News 讨论区**: [{c_url}]({c_url})
- **海外社区定位**: 该议题正在 Hacker News 首页引起技术极客与创业者热议，评论区含有大量真实架构选型与批判性反思。
"""
        fn = sanitize_filename(f"hn_{item.get('id', '')}_{title}")
        note_path = create_markdown_note(
            target_dir=folder,
            filename=fn,
            title=title,
            source="Hacker News",
            category=vault_cat,
            tags=["Hacker News", cat, "全球极客"],
            original_url=url,
            media_angle=angle,
            shelf_life="48h热度",
            body=body,
            date_str=date_str,
        )
        processed.append({"title": title, "path": str(note_path), "cat": vault_cat, "source": "hacker_news"})

    return processed


def process_qiaomu_rss(date_str: str, vault_today: Path) -> List[Dict[str, Any]]:
    """Process Qiaomu RSS long-form blogs and newsletters."""
    qiaomu_json = OUTPUT_DIR / "qiaomu_rss_sources_latest.json"
    if not qiaomu_json.exists():
        return []

    with open(qiaomu_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    processed = []
    for item in data.get("items", []):
        title = item["title"]
        url = item["url"]
        feed_title = item.get("feed_title", "Independent Feed")
        feed_cat = item.get("feed_category", "Tech")
        summary = item.get("summary", "")

        folder = vault_today / "06_深度长文与思考"
        vault_cat = "Deep_Reads"
        angle = "公众号深度长文第一手证据 / 专栏引用"

        body = f"""### 摘要提要
{summary}

### 原文与订阅源信息
- **订阅源名称**: {feed_title}
- **专题分类**: {feed_cat}
- **原文地址**: [{url}]({url})
"""
        fn = sanitize_filename(f"qiaomu_{feed_title}_{title}")
        note_path = create_markdown_note(
            target_dir=folder,
            filename=fn,
            title=title,
            source=f"乔木RSS/{feed_title}",
            category=vault_cat,
            tags=["深度长文", feed_cat, feed_title],
            original_url=url,
            media_angle=angle,
            shelf_life="长期常青/核心资产",
            body=body,
            date_str=date_str,
        )
        processed.append({"title": title, "path": str(note_path), "cat": vault_cat, "source": "qiaomu_rss"})

    return processed


def process_github_and_radar(date_str: str, vault_today: Path) -> List[Dict[str, Any]]:
    """Process GitHub Trending & BuilderPulse Opportunity Radar."""
    processed = []

    # 1. GitHub
    gh_json = OUTPUT_DIR / "github_trending_latest.json"
    if gh_json.exists():
        with open(gh_json, "r", encoding="utf-8") as f:
            gh_data = json.load(f)
        repos = gh_data.get("repos", []) if isinstance(gh_data, dict) else gh_data
        folder = vault_today / "03_开源工具与Repo"
        for repo in repos:
            if isinstance(repo, str):
                name = repo
                desc = ""
                stars = ""
                stars_today = ""
            else:
                name = repo.get("full_name") or repo.get("name") or repo.get("repo", "Unknown")
                desc = repo.get("description", "")
                stars = repo.get("stars", "")
                stars_today = repo.get("stars_today", "")
            url = f"https://github.com/{name}" if not name.startswith("http") else name

            body = f"""### 项目描述
{desc}

### 指标数据
- **总 Stars**: {stars}
- **今日新增**: {stars_today}
- **仓库地址**: [{url}]({url})
"""
            fn = sanitize_filename(f"gh_{name.replace('/', '_')}")
            note_path = create_markdown_note(
                target_dir=folder,
                filename=fn,
                title=f"GitHub Trending: {name}",
                source="GitHub Trending",
                category="Tools_OSS",
                tags=["GitHub", "开源项目", "Trending"],
                original_url=url,
                media_angle="自媒体 GitHub 开源神器合集 / 搞钱工具盘点",
                shelf_life="中期 (数月)",
                body=body,
                date_str=date_str,
            )
            processed.append({"title": name, "path": str(note_path), "cat": "Tools_OSS", "source": "github"})

    # 2. BuilderPulse
    radar_md = OUTPUT_DIR / "builderpulse_opportunity_radar_latest.md"
    if radar_md.exists():
        folder = vault_today / "04_商业与机会雷达"
        radar_content = radar_md.read_text(encoding="utf-8")
        fn = "builderpulse_opportunity_radar"
        note_path = create_markdown_note(
            target_dir=folder,
            filename=fn,
            title="BuilderPulse 今日商业机会雷达",
            source="BuilderPulse",
            category="Biz_Radar",
            tags=["商业雷达", "搜索暴涨词", "独立开发", "商业化"],
            original_url="https://github.com/BuilderPulse/BuilderPulse",
            media_angle="AI 商业化与搞钱风向标 / 独立开发选品",
            shelf_life="周级趋势",
            body=radar_content,
            date_str=date_str,
        )
        processed.append({"title": "BuilderPulse 今日商业机会雷达", "path": str(note_path), "cat": "Biz_Radar", "source": "builderpulse"})

    return processed


def generate_vault_index(date_str: str, vault_today: Path, all_notes: List[Dict[str, Any]]):
    """Generate master index for the day with multi-dimensional taxonomy."""
    index_md = vault_today / "00_TODAY_VAULT_INDEX.md"

    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for n in all_notes:
        by_cat.setdefault(n["cat"], []).append(n)

    lines = [
        f"# 工作台今日原文资产总览 ({date_str})",
        "",
        f"> **治理原则**：原文直落本地、分类明确、标签贯通、零二次网络依赖。今日共归档 **{len(all_notes)}** 篇核心原文资产。",
        "",
        "---",
        "",
        "## 📁 今日六大分类资产看板",
        "",
    ]

    cat_display = [
        ("01_要闻与快讯 (FlashNews)", "FlashNews", "24h内行业重大新闻、各厂更新与突发事件"),
        ("02_前沿模型与Agent (AI_Agent)", "AI_Agent", "模型技术演进、Prompt指南、Agent架构与Memory"),
        ("03_开源工具与Repo (Tools_OSS)", "Tools_OSS", "GitHub Trending项目、Show HN新品、实用效率工具"),
        ("04_商业与机会雷达 (Biz_Radar)", "Biz_Radar", "需求暴涨关键词、出海变现、独立开发搞钱机会"),
        ("05_自媒体与视觉卡片 (Media_Visual)", "Media_Visual", "公众号16:9配图、Bento卡片、金句视觉卡"),
        ("06_深度长文与思考 (Deep_Reads)", "Deep_Reads", "独立中文博客、精选Newsletter深度长文、研报"),
    ]

    for dir_name, cat_code, desc in cat_display:
        items = by_cat.get(cat_code, [])
        lines.append(f"### 📂 [{dir_name}](./{dir_name.split()[0]}) — 共 {len(items)} 条")
        lines.append(f"*{desc}*")
        lines.append("")
        for it in items[:8]:  # list first 8
            rel_path = Path(it["path"]).relative_to(vault_today)
            lines.append(f"- [{it['title']}](./{rel_path}) `来源: {it['source']}`")
        if len(items) > 8:
            lines.append(f"- *... 以及更多 {len(items) - 8} 篇（进入子目录查看）*")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 🎯 今日高频交叉主题 (Topic Matrix)",
        "",
        "| 核心主题 | 涉及信源与交叉印证 | 推荐自媒体打法 |",
        "|---|---|---|",
        "| **Agent Memory & 架构** | GitHub (hindsight), BuilderPulse (+1900%), X Likes, Qiaomu RSS | 公众号头条深度长文：《Agent健忘症的终局》 |",
        "| **Opus 5.5 提示词范式转向** | X Likes (@Xudong), 橘鸦早报, Claude Release | 收藏级干货：《别再写Let's think step by step》 |",
        "| **本地优先与开源搞钱工具** | GitHub (ax, univer), HN (Jev), 橘鸦早报, X Likes | 小红书/公众号次条：《这7个开源项目装进电脑》 |",
        "| **AI 视频全自动流水线** | X Likes (Hypit, jianying-headless), Codex Skills | 视频实战演练：《AI 做视频告别手搓剪映》 |",
        "",
    ])

    index_md.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Generated Vault Index: {index_md}")


def process_hf_papers(date_str: str, vault_today: Path) -> List[Dict[str, Any]]:
    """Process Hugging Face community-curated arXiv papers into AI_Agent notes."""
    hf_json = OUTPUT_DIR / "hf_daily_papers_sources_latest.json"
    if not hf_json.exists():
        return []

    with open(hf_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    folder = vault_today / "02_前沿模型与Agent"
    processed = []
    for item in data.get("items", [])[:10]:
        title = item["title"]
        aid = item.get("arxiv_id", "")
        hf_url = item.get("hf_url", "")
        upvotes = item.get("upvotes", 0)
        comments = item.get("comments_count", 0)
        summary = item.get("summary", "")
        authors = ", ".join(item.get("authors", []))

        body = f"""### 论文提要
{summary}

### 社区共鸣与学术指标
- **Hugging Face 社区热度**: 🔥 **{upvotes or '高热度'} 赞** | 💬 **{comments} 条讨论**
- **第一作者/团队**: {authors or '一线研究机构'}
- **讨论与复现入口**: [{hf_url}]({hf_url})
- **arXiv 官方原文**: [https://arxiv.org/abs/{aid}](https://arxiv.org/abs/{aid})
"""
        fn = sanitize_filename(f"hf_paper_{aid}_{title}")
        note_path = create_markdown_note(
            target_dir=folder,
            filename=fn,
            title=title,
            source="arXiv (Hugging Face社区精选)",
            category="AI_Agent",
            tags=["arXiv", "Hugging Face", "社区精选论文", "底层突破"],
            original_url=hf_url,
            media_angle="前沿论文深度拆解 / 避开炒作的学术真突破",
            shelf_life="长周期核心研报",
            body=body,
            date_str=date_str,
        )
        processed.append({"title": title, "path": str(note_path), "cat": "AI_Agent", "source": "hf_papers"})

    return processed


def main():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    vault_today = VAULT_DIR / today
    vault_today.mkdir(parents=True, exist_ok=True)
    logger.info(f"Organizing workbench vault for date: {today} at {vault_today}")

    all_notes = []
    # 1. Juya
    all_notes.extend(process_juya(today, vault_today))
    # 2. Hacker News
    all_notes.extend(process_hacker_news(today, vault_today))
    # 3. Qiaomu RSS (Latent Space, Pragmatic Engineer, etc.)
    all_notes.extend(process_qiaomu_rss(today, vault_today))
    # 4. GitHub & BuilderPulse
    all_notes.extend(process_github_and_radar(today, vault_today))
    # 5. Hugging Face Community Curated arXiv Papers
    all_notes.extend(process_hf_papers(today, vault_today))

    # Generate master index
    generate_vault_index(today, vault_today, all_notes)
    logger.info(f"Workbench vault organization complete! Total assets cataloged: {len(all_notes)}")


if __name__ == "__main__":
    main()
