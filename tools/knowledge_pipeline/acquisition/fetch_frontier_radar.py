#!/usr/bin/env python3
"""Bounded public API adapters for community discussion, releases and trend observations."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.request
from urllib.parse import urlencode, urlsplit

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / 'tools/aihot/radar_sources.json'
FILES = {'hacker-news': 'hacker_news_sources_latest.json',
         'github-releases': 'github_releases_sources_latest.json',
         'oss-insight': 'oss_insight_sources_latest.json'}
HN = 'https://hacker-news.firebaseio.com/v0/'
OSS = 'https://api.ossinsight.io/v1/trends/repos/?'
MAX_BYTES = 4 * 1024 * 1024
INTEREST = re.compile(r'\b(ai|llms?|gpt|agents?|claude|gemini|openai|anthropic|deepseek|models?|'
                      r'inference|reasoning|rag|neural|cuda|gpu|robotics?|mcp|coding|compiler|database|'
                      r'postgres|linux|rust|python|kubernetes|security|browser)\b', re.I)
REPOSITORY = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Public API unexpectedly redirected')


def fetch_json(url):
    host = urlsplit(url).netloc
    if host not in {'hacker-news.firebaseio.com', 'api.github.com', 'api.ossinsight.io'}:
        raise ValueError('Unrecognized public API')
    request = urllib.request.Request(url, headers={
        'Accept': 'application/json', 'User-Agent': 'Muqiao-Information-Collector/1.0'})
    with urllib.request.build_opener(_NoRedirect()).open(request, timeout=12) as response:
        if int(response.headers.get('Content-Length', '0')) > MAX_BYTES:
            raise ValueError('Public API response too large')
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('Public API response too large')
    return json.loads(data)


class _PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}:
            self.hidden += 1
        if tag in {'p', 'br', 'li'}:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in {'script', 'style'}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain(value):
    parser = _PlainText()
    parser.feed(str(value or ''))
    return '\n'.join(' '.join(line.split()) for line in ''.join(parser.parts).splitlines()).strip()


def timestamp(value, now):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        result = datetime.fromtimestamp(value, timezone.utc)
    else:
        result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if result.tzinfo is None or result > now:
        raise ValueError('Missing, naive or future publication date')
    return result.astimezone(timezone.utc).isoformat()


def item(title, url, published, body, raw, author=''):
    # The ingest API trims bodyText; hash the same representation it stores.
    body = body.strip()
    raw = {**raw, 'bodySha256': sha256(body.encode()).hexdigest()}
    return {'title': title, 'url': url, 'publishedAt': published, 'author': author,
            'summary': body[:600], 'body': body, 'raw': raw}


def hacker_news(config, now):
    ids = fetch_json(HN + 'topstories.json')
    if not isinstance(ids, list) or not all(type(i) is int and i > 0 for i in ids):
        raise ValueError('Invalid Hacker News story list')
    failures = []

    def get(identifier):
        try:
            return fetch_json(HN + f'item/{identifier}.json')
        except (OSError, ValueError) as error:
            failures.append({'id': identifier, 'error': type(error).__name__})
            return None

    with ThreadPoolExecutor(max_workers=6) as pool:
        stories = list(pool.map(get, ids[:config['scan_limit']]))
    items = []
    for story in stories:
        if not isinstance(story, dict) or story.get('type') != 'story' or story.get('deleted') or story.get('dead'):
            continue
        title = plain(story.get('title'))
        if not title or not INTEREST.search(title):
            continue
        published = timestamp(story.get('time'), now)
        if datetime.fromisoformat(published) < now - timedelta(hours=48):
            continue
        identifier = story['id']
        thread = f'https://news.ycombinator.com/item?id={identifier}'
        comments = []
        children = [i for i in story.get('kids', []) if type(i) is int and i > 0]
        with ThreadPoolExecutor(max_workers=3) as pool:
            values = list(pool.map(get, children[:config['comments_per_story']]))
        for comment in values:
            if (not isinstance(comment, dict) or comment.get('type') != 'comment'
                    or comment.get('deleted') or comment.get('dead') or comment.get('parent') != identifier):
                continue
            text = plain(comment.get('text'))[:1200]
            if not text:
                continue
            comments.append({'id': comment['id'], 'author': comment.get('by', ''),
                             'publishedAt': timestamp(comment.get('time'), now), 'text': text,
                             'url': f"https://news.ycombinator.com/item?id={comment['id']}",
                             'textSha256': sha256(text.encode()).hexdigest()})
        lines = [f'讨论主题：{title}', f'讨论页：{thread}', f"原文链接：{story.get('url') or thread}"]
        if story.get('text'):
            lines.append('帖子正文：' + plain(story['text'])[:4000])
        lines.append('以下为公开评论摘录，仅代表对应作者观点；不代表共识或原文独立核验。')
        for index, comment in enumerate(comments, 1):
            lines.append(f"\n评论 C{index}｜{comment['author']}｜{comment['publishedAt']}\n出处：{comment['url']}\n{comment['text']}")
        if not comments:
            lines.append('本次没有取得可用评论，不生成讨论结论。')
        body = '\n'.join(lines)
        items.append(item('HN 讨论：' + title, thread, published, body,
                          {'kind': 'community_discussion', 'threadId': identifier,
                           'originalUrl': story.get('url'), 'comments': comments,
                           'score': story.get('score'), 'commentCount': story.get('descendants'),
                           'sampling': 'first ranked top-level comments; not a consensus sample'}, story.get('by', '')))
        if len(items) >= config['max_items']:
            break
    if not items:
        raise ValueError('No current matching Hacker News stories; previous snapshot retained')
    return items, {'requestFailures': failures, 'comments': sum(len(i['raw']['comments']) for i in items)}


def github_releases(config, now):
    from tools.knowledge_pipeline.acquisition.fetch_cli_releases import _release
    items, failures = [], []
    for repository in config['repositories']:
        if not REPOSITORY.fullmatch(repository):
            raise ValueError('Invalid configured repository')
        try:
            release = fetch_json(f'https://api.github.com/repos/{repository}/releases/latest')
            normalized = _release(release, repository, repository.split('/')[0], now)
            if normalized is None or release['prerelease']:
                raise ValueError('Latest stable endpoint returned a draft or preview')
            body = f"仓库：{repository}\n稳定版本：{release.get('tag_name')}\n官方发布说明：\n{(release.get('body') or '')[:18000]}"
            items.append(item(repository + ' · ' + normalized['title'], normalized['url'],
                              normalized['publishedAt'], body,
                              {'kind': 'release', 'repository': repository, 'releaseId': release.get('id'),
                               'tag': release.get('tag_name'), 'prerelease': False}, normalized['author']))
        except (OSError, ValueError) as error:
            failures.append({'repository': repository, 'error': type(error).__name__})
    if failures:
        # Do not promote a partial watchlist as a healthy complete collection.
        raise ValueError('GitHub release collection incomplete: ' + json.dumps(failures))
    return items, {'repositories': len(items)}


def oss_insight(config, now):
    endpoint = OSS + urlencode({key: config[key] for key in ('period', 'language')})
    payload = fetch_json(endpoint)
    quality = payload.get('data_quality') or {}
    if quality.get('status') not in {None, 'available', 'ok'}:
        return [], {'status': 'unavailable', 'dataQuality': quality, 'endpoint': endpoint}
    rows = payload.get('data', {}).get('rows')
    if not isinstance(rows, list) or not rows:
        raise ValueError('OSS Insight returned no usable ranking; previous snapshot retained')
    items = []
    for row in rows:
        repository = row.get('repo_name', '')
        if not REPOSITORY.fullmatch(repository) or not INTEREST.search(repository + ' ' + str(row.get('description', ''))):
            continue
        url = 'https://github.com/' + repository
        # No release date is supplied. DiscoveredAt remains separate in the ingest contract.
        body = (f"OSS Insight 趋势观测：{repository}\n窗口：{config['period']}\n"
                f"窗口内星标事件数：{row.get('stars')}\n语言：{row.get('primary_language') or '未知'}\n"
                f"项目说明：{row.get('description') or ''}\n来源：{endpoint}\n"
                '这是关注度信号，不证明项目质量、能力或发布新版本。')
        items.append(item(repository + ' · OSS Insight 趋势观测', url, None, body,
                          {'kind': 'trend_observation', 'observedAt': now.isoformat(),
                           'period': config['period'], 'endpoint': endpoint, 'metrics': row,
                           'publishedAtBasis': 'unknown; observation is not a release'}))
        if len(items) >= config['max_items']:
            break
    return items, {'endpoint': endpoint, 'dataQuality': quality}


def collect(source, now=None):
    now = now or datetime.now(timezone.utc)
    config = json.loads(CONFIG.read_text())
    collectors = {'hacker-news': (hacker_news, 'hacker_news'),
                  'github-releases': (github_releases, 'github_releases'),
                  'oss-insight': (oss_insight, 'oss_insight')}
    collector, key = collectors[source]
    items, coverage = collector(config[key], now)
    return {'source_id': source, 'generated_at': now.isoformat(), 'selection': 'unscored',
            'items': items, 'coverage': coverage}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, choices=FILES)
    args = parser.parse_args(argv)
    document = collect(args.source)
    output = Path(os.environ.get('WORKSPACE_ROOT', str(ROOT.parent))) / 'output_to_user'
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=output, encoding='utf-8', delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(document, handle, ensure_ascii=False)
    temporary.replace(output / FILES[args.source])


if __name__ == '__main__':
    # Direct script execution and module execution use the same imports.
    import sys
    sys.path.insert(0, str(ROOT))
    main()
