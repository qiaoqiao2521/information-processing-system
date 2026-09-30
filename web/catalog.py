"""Normalize existing collector outputs into a public, provenance-aware reading feed."""
from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit

OUTPUT_FILES = (
    'consolidated_daily_brief.json', 'github_trending_latest.json',
    'builderpulse_opportunity_radar_sources_latest.json', 'ai_builders_digest_sources_latest.json',
    'hacker_news_sources_latest.json', 'hf_daily_papers_sources_latest.json',
    'juya_daily_sources_latest.json', 'qiaomu_rss_sources_latest.json', 'ak_rss_sources_latest.json',
    'x_google_sources_latest.json',
    'collection_status.json',
)
DATA_FILES = ('media_assets.json', 'enriched_trending.json', 'enriched_digest.json')
SOURCES = (
    ('hacker-news', 'Hacker News', '社区讨论', 'hacker_news_sources_latest.json'),
    ('juya', '橘鸦 AI 日报', '行业动态', 'juya_daily_sources_latest.json'),
    ('papers', 'HF 每日论文', '研究论文', 'hf_daily_papers_sources_latest.json'),
    ('rss', '乔木 RSS', '订阅文章', 'qiaomu_rss_sources_latest.json'),
    ('ak-rss', 'AK RSS', '订阅文章', 'ak_rss_sources_latest.json'),
    ('x', 'X 关注动态', '公开帖文', 'x_google_sources_latest.json'),
    ('trending', 'GitHub 趋势', '开源项目', 'github_trending_latest.json'),
    ('digest', 'AI Builders', '一线动态', 'ai_builders_digest_sources_latest.json'),
    ('radar', '机会雷达', '机会观察', 'builderpulse_opportunity_radar_sources_latest.json'),
    ('topics', '融合简报', '主题汇总', 'consolidated_daily_brief.json'),
    ('assets', '媒体素材', '创作素材', 'media_assets.json'),
)


def scrub(value):
    """Keep publication content; exclude host-specific provenance fields."""
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items() if k not in {'local_path', 'git_head'}}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


def load(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def iso_date(value):
    if not value:
        return None
    try:
        d = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(value)):
            return str(value)
    except ValueError:
        try:
            d = parsedate_to_datetime(str(value))
        except (ValueError, TypeError):
            return None
    return d.replace(tzinfo=d.tzinfo or timezone.utc).isoformat()


def safe_url(value):
    if not isinstance(value, str):
        return ''
    try:
        u = urlsplit(value.strip())
        return value.strip() if u.scheme in {'https', 'http'} and u.hostname and not u.username and not u.password else ''
    except ValueError:
        return ''


def text(value):
    return html.unescape(str(value if value is not None else '')).replace('\\n', '\n').strip()


def rows(value, key):
    return [r for r in value.get(key, []) if isinstance(r, dict)] if isinstance(value, dict) and isinstance(value.get(key), list) else []


def source_paths(output_dir, data_dir):
    return {**{f: output_dir / f for f in OUTPUT_FILES}, **{f: data_dir / f for f in DATA_FILES}}


def dataset_digest(output_dir, data_dir):
    content = {}
    for name, path in source_paths(output_dir, data_dir).items():
        doc = load(path)
        embedded_date = isinstance(doc, dict) and (doc.get('generated_at') or doc.get('generatedAt') or doc.get('date'))
        content[name] = {'content': scrub(doc)}
        if doc is not None and not embedded_date:
            content[name]['fileUpdatedAt'] = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    return hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def code_digest(web_dir):
    digest = hashlib.sha256()
    for name in ('server.py', 'catalog.py', 'public/index.html', 'public/app.js', 'public/style.css', 'public/workflows.json'):
        path = web_dir / name
        digest.update(name.encode())
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def catalog(output_dir: Path, data_dir: Path):
    paths = source_paths(output_dir, data_dir)
    data = {name: load(p) for name, p in paths.items()}
    health = data.get('collection_status.json') or {}
    items, sources = [], []
    for source_id, name, description, filename in SOURCES:
        doc, path = data.get(filename), paths[filename]
        if source_id in {'trending', 'digest'} and not isinstance(doc, dict):
            filename = f'enriched_{source_id}.json'
            doc, path = data[filename], paths[filename]
        timestamp = iso_date(doc.get('generated_at') or doc.get('generatedAt') or doc.get('date')) if isinstance(doc, dict) else None
        time_kind = 'collected'
        if not timestamp and path.is_file() and doc is not None:
            timestamp = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
            time_kind = 'file'
        source = {'id': source_id, 'name': name, 'description': description, 'updatedAt': timestamp,
                  'timeKind': time_kind, 'status': 'ready' if doc is not None else ('invalid' if path.exists() else 'missing'), 'count': 0}
        sources.append(source)
        attempt = health.get('sources', {}).get(source_id)
        if isinstance(attempt, dict):
            source['lastAttempt'] = {k: attempt[k] for k in ('status', 'checkedAt', 'message') if k in attempt}
        if source_id == 'ak-rss' and isinstance(doc, dict):
            source['description'] = '近七天订阅文章 · 未经 AI 筛选'
            source['coverage'] = doc.get('coverage')
            source['window'] = doc.get('window')
        if source_id == 'x' and isinstance(doc, dict):
            source['description'] = '近七天公开搜索候选 · 非完整时间线 · 摘要以原帖为准'
            source['coverage'] = doc.get('coverage')
            source['reading'] = doc.get('reading')
            source['window'] = doc.get('window')

        def add(title, summary='', body='', url='', published=None, author='', fields=(), links=(), prompt='', identity=''):
            if not text(title):
                return
            address = safe_url(url)
            item_id = hashlib.sha256(f'{source_id}:{identity or address or title}'.encode()).hexdigest()[:20]
            normalized_links = [{'label': text(label), 'url': safe_url(link)} for label, link in links if safe_url(link)]
            item = {'id': item_id, 'sourceId': source_id, 'sourceName': name, 'kind': description,
                    'title': text(title), 'summary': text(summary), 'body': text(body), 'url': address,
                    'publishedAt': iso_date(published), 'collectedAt': timestamp, 'timeKind': time_kind,
                    'author': text(author), 'fields': [{'label': label, 'value': text(value)} for label, value in fields if value is not None and value != ''],
                    'links': normalized_links, 'prompt': text(prompt)}
            items.append(item)
            source['count'] += 1

        if source_id == 'trending':
            extras = {r.get('full_name'): r for r in rows(data['enriched_trending.json'], 'repos')}
            for r in rows(doc, 'repos'):
                e = extras.get(r.get('full_name'), {})
                if r.get('description') != e.get('description'):
                    e = {}
                add(r.get('full_name') or r.get('name'), r.get('description'), e.get('local_snapshot'), r.get('url'),
                    author=r.get('owner'), fields=[('语言', r.get('language')), ('本次日榜新增星标', r.get('stars_today')),
                    ('总星标', r.get('stars')), ('加工笔记 · 解决问题', e.get('problem_solved')),
                    ('加工笔记 · 特性', '\n'.join(e.get('key_features', [])))])
        elif source_id == 'digest':
            for r in rows(doc, 'selectedSources' if isinstance(doc, dict) and 'selectedSources' in doc else 'sources'):
                add(r.get('originalTitle') or r.get('original_title') or r.get('title'), r.get('summary'),
                    r.get('originalText') or r.get('local_snapshot'), r.get('url'), r.get('publishedAt'), r.get('author'))
        elif source_id == 'radar':
            for section in rows(doc, 'selected_sections'):
                for r in rows(section, 'items'):
                    report = doc.get('report') or {}
                    report_url = report.get('report_url') or report.get('url') or report.get('source_url') or report.get('github_url') or ''
                    add(r.get('question') or r.get('title'), r.get('key_judgment') or r.get('summary'), r.get('signal') or r.get('text'),
                        report_url, published=report.get('date'), fields=[('栏目', section.get('section') or section.get('heading')), ('相反观点', r.get('contrarian_view'))],
                        identity=r.get('question') or r.get('title'))
        elif source_id == 'topics':
            for r in rows(doc, 'topics'):
                citations = [(c.get('title') or '参考来源', c.get('url') or c.get('canonical_url')) for c in rows(r, 'citations')]
                add(r.get('topic_title'), r.get('key_breakthrough'), '\n\n'.join(r.get('technical_details', [])),
                    fields=[('主题分类', r.get('primary_category')), ('参与合并的条目', r.get('raw_item_count'))], links=citations, identity=r.get('topic_id'))
        elif source_id == 'assets':
            for r in doc if isinstance(doc, list) else []:
                add(r.get('viralTitle') or r.get('techTitle'), r.get('techTitle'), r.get('rawBody'),
                    fields=[('内容形态', r.get('format')), ('加工笔记', '\n'.join(r.get('facts', [])))], prompt=r.get('prompt'), identity=r.get('id'))
        else:
            for r in rows(doc, 'items'):
                address = r.get('url') or r.get('arxiv_url') or r.get('hf_url')
                add(r.get('title'), r.get('summary') or r.get('description'), r.get('content') or r.get('body'), address,
                    r.get('published_at') or r.get('date'), r.get('author') or r.get('feed_title') or ', '.join(r.get('authors', [])),
                    fields=[('分类', r.get('category') or r.get('feed_category'))] + (
                        [('正文状态', 'Jina 已提取正文' if r.get('content_status') == 'full-text' else '搜索摘要 · 正文未取得'),
                         ('正文读取时间', r.get('body_fetched_at')), ('发现方式', 'Google 浏览器搜索'),
                         ('发帖时间依据', 'X 帖子 ID 时间戳')] if source_id == 'x' else []),
                    links=[('HN 讨论', r.get('comments_url')), ('HF 论文页', r.get('hf_url'))])
                if source_id == 'x' and items and items[-1]['sourceId'] == 'x':
                    items[-1]['kind'] = 'Jina 正文' if r.get('content_status') == 'full-text' else '搜索摘要'
    return {'sources': sources, 'items': items, 'datasetDigest': dataset_digest(output_dir, data_dir)}
