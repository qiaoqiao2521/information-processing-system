#!/usr/bin/env python3
"""Private AIHOT RSS reader cache. No ingestion, publishing, model calls or notifications."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

FEEDS = {'selected': '/feed.xml', 'all': '/feed/all.xml', 'daily': '/feed/daily.xml',
         **{k: f'/feed/category/{k}.xml' for k in ('ai-models', 'ai-products', 'industry', 'paper', 'tip')}}
MAX_BYTES = 4 * 1024 * 1024


class Description(HTMLParser):
    def __init__(self):
        super().__init__(); self.texts = []; self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href', '')
            if urllib.parse.urlsplit(href).scheme in ('https', 'http'):
                self.links.append(href)
        if tag in ('p', 'br', 'li'):
            self.texts.append('\n')
    def handle_data(self, data):
        self.texts.append(data)


def parse_feed(body: bytes):
    if len(body) > MAX_BYTES or b'<!DOCTYPE' in body.upper() or b'<!ENTITY' in body.upper():
        raise ValueError('Oversized feed or unsupported XML declarations')
    root = ET.fromstring(body)
    if root.tag != 'rss' or root.find('channel') is None:
        raise ValueError('Expected RSS channel')
    result = []; seen = set()
    for item in root.findall('./channel/item')[:100]:
        get = lambda name: (item.findtext(name) or '').strip()
        title, link = get('title'), get('link')
        u = urllib.parse.urlsplit(link)
        if not title or u.scheme != 'https' or u.hostname != 'aihot.news':
            raise ValueError('Invalid upstream item identity')
        identity = get('guid') or link
        if identity in seen:
            continue
        seen.add(identity)
        description = Description(); description.feed(get('description'))
        original = next((x for x in description.links if urllib.parse.urlsplit(x).hostname != 'aihot.news'), None)
        result.append({'id': identity, 'title': title, 'summary': ''.join(description.texts).strip(),
                       'publishedAt': get('pubDate') or None, 'source': get('author'),
                       'category': get('category'), 'links': {'aihot': link, 'original': original},
                       'attribution': {'name': 'AIHOT', 'url': link}})
    return result


def atomic_json(path: Path, value):
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
        temp = Path(f.name)
        os.chmod(temp, 0o600)
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
    os.replace(temp, path)


def sync(feed: str, root: Path, opener=urllib.request.urlopen):
    root.mkdir(parents=True, exist_ok=True); root.chmod(0o700)
    path = root / (feed + '.json')
    old = json.loads(path.read_text()) if path.exists() else None
    url = 'https://aihot.news' + FEEDS[feed]
    headers = {'User-Agent': 'Muqiao-PrivateReader/1.0', 'Accept': 'application/rss+xml, application/xml'}
    if old and old.get('etag'):
        headers['If-None-Match'] = old['etag']
    # RSS ttl=30: do not poll on every manual command. Keep this private reading cache bounded.
    if old and (datetime.now(timezone.utc) - datetime.fromisoformat(old['fetchedAt'])).total_seconds() < 1800:
        return {'feed': feed, 'status': 'cached', 'items': len(old['items']), 'path': str(path)}
    try:
        with opener(urllib.request.Request(url, headers=headers), timeout=30) as response:
            if response.status != 200:
                raise ValueError('Unexpected feed response')
            if urllib.parse.urlsplit(response.geturl()).hostname != 'aihot.news':
                raise ValueError('Unexpected feed redirect')
            if 'no-store' in (response.headers.get('Cache-Control') or '').lower():
                raise ValueError('Upstream forbids persistent caching')
            items = parse_feed(response.read(MAX_BYTES + 1))
            value = {'url': url, 'etag': response.headers.get('ETag'), 'items': items,
                     'cacheControl': response.headers.get('Cache-Control'), 'privateOnly': True}
            status = 200
    except urllib.error.HTTPError as error:
        if error.code != 304 or not old:
            raise
        value = old; status = 304
    value['fetchedAt'] = datetime.now(timezone.utc).isoformat()
    atomic_json(path, value)
    return {'feed': feed, 'status': status, 'items': len(value['items']), 'path': str(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--feed', choices=FEEDS, default='selected')
    parser.add_argument('--cache-dir', type=Path, default=Path.home() / '.local/share/information-hub/aihot-reader')
    args = parser.parse_args()
    print(json.dumps(sync(args.feed, args.cache_dir), ensure_ascii=False))


if __name__ == '__main__':
    main()
