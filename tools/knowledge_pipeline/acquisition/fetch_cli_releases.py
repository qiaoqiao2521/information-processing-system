#!/usr/bin/env python3
"""Collect official CLI release metadata without model calls or authentication."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import urllib.request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]
FILENAME = 'cli_releases_sources_latest.json'
TIMEOUT = 25
MAX_BYTES = 8 * 1024 * 1024
ENDPOINTS = (
    'https://api.github.com/repos/anthropics/claude-code/releases/latest',
    'https://api.github.com/repos/openai/codex/releases/latest',
    'https://api.github.com/repos/openai/codex/releases?per_page=10',
)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Official release endpoint unexpectedly redirected')


def _fetch_json(url: str):
    if url not in ENDPOINTS:
        raise ValueError('Unrecognized official release endpoint')
    request = urllib.request.Request(url, headers={
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'Muqiao-Information-Collector/1.0',
    })
    with urllib.request.build_opener(_NoRedirect()).open(request, timeout=TIMEOUT) as response:
        length = response.headers.get('Content-Length')
        if length is not None and int(length) > MAX_BYTES:
            raise ValueError('Release response exceeds 8 MiB')
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Release response exceeds 8 MiB')
    return json.loads(raw.decode('utf-8'))


def _release(entry, repository: str, author: str, now: datetime):
    if not isinstance(entry, dict):
        raise ValueError('Release metadata must be an object')
    if type(entry.get('draft')) is not bool or type(entry.get('prerelease')) is not bool:
        raise ValueError('Release metadata needs boolean draft and prerelease fields')
    if entry['draft']:
        return None
    title = entry.get('name') or entry.get('tag_name')
    if not isinstance(title, str) or not title.strip():
        raise ValueError('Release metadata has no valid title')
    url = entry.get('html_url')
    if not isinstance(url, str) or any(character.isspace() for character in url):
        raise ValueError('Release metadata has no valid official URL')
    parsed = urlsplit(url)
    prefix = f'/{repository}/releases/tag/'
    if (parsed.scheme != 'https' or parsed.netloc != 'github.com'
            or parsed.query or parsed.fragment or not parsed.path.startswith(prefix)
            or not parsed.path[len(prefix):] or '..' in parsed.path.split('/')):
        raise ValueError('Release URL is outside its official repository')
    value = entry.get('published_at')
    if not isinstance(value, str):
        raise ValueError('Release metadata has no valid publication date')
    try:
        published = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError('Release metadata has no valid publication date') from error
    if published.tzinfo is None or published > now:
        raise ValueError('Release publication date is undated or in the future')
    body = entry.get('body')
    if body is not None and not isinstance(body, str):
        raise ValueError('Release body must be text or null')
    summary = ' '.join((body or '').split())
    summary = summary if len(summary) <= 600 else summary[:599].rstrip() + '…'
    return {'title': title.strip(), 'url': url,
            'publishedAt': published.astimezone(timezone.utc).isoformat(),
            'summary': summary, 'author': author}


def collect(now: datetime | None = None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Collection time must include a timezone')
    now = now.astimezone(timezone.utc)
    # Stable releases are fetched independently; they may be outside the ten recent entries.
    claude, codex, recent = (_fetch_json(url) for url in ENDPOINTS)
    selected = []
    for entry, repository, author in (
            (claude, 'anthropics/claude-code', 'Anthropic'),
            (codex, 'openai/codex', 'OpenAI')):
        item = _release(entry, repository, author, now)
        if item is None or entry['prerelease']:
            raise ValueError('Latest stable endpoint returned a draft or prerelease')
        selected.append(item)
    if not isinstance(recent, list):
        raise ValueError('Recent Codex releases must be an array')
    preview = None
    for entry in recent:
        item = _release(entry, 'openai/codex', 'OpenAI', now)
        if item is not None and entry['prerelease'] and preview is None:
            preview = item
    if preview is not None:
        selected.append(preview)
    seen, items = set(), []
    for item in selected:
        if item['url'] not in seen:
            seen.add(item['url'])
            items.append(item)
    return {'source': 'cli-releases', 'generated_at': now.isoformat(),
            'selection': 'unscored', 'source_urls': list(ENDPOINTS), 'items': items}


def harvest(output_dir: Path | None = None, now: datetime | None = None):
    document = collect(now)
    output_dir = Path(output_dir) if output_dir is not None else (
        Path(os.environ.get('WORKSPACE_ROOT', str(ROOT.parent))) / 'output_to_user')
    output_dir.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=output_dir,
                                         prefix=f'.{FILENAME}.', delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(document, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
        temporary.replace(output_dir / FILENAME)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return document


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outdir', type=Path)
    args = parser.parse_args(argv)
    document = harvest(args.outdir)
    print(json.dumps({'source': document['source'], 'items': len(document['items'])}))


if __name__ == '__main__':
    main()
