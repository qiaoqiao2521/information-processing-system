#!/usr/bin/env python3
"""Bounded private read-only API cache with atomic selected-result cursor updates."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request
from upstream_feed import MAX_BYTES, atomic_json

BASE = 'https://aihot.news'
TTL = 1800
MAX_SELECTED = 200


def now():
    return datetime.now(timezone.utc)


def validate(value):
    if not isinstance(value, dict) or value.get('schemaVersion') != 1:
        raise ValueError('Unsupported upstream API schema')
    return value


def validate_resource(path, value):
    validate(value)
    endpoint = urllib.parse.urlsplit(path).path
    if endpoint == '/api/v1/hot-topics':
        items = value.get('items')
        if not isinstance(items, list) or len(items) > 10:
            raise ValueError('Invalid hot topics')
        for item in items:
            story_id(item['links']['story'])
    elif endpoint.startswith('/api/v1/stories/'):
        story = value.get('story')
        if not isinstance(story, dict) or not isinstance(story.get('reports'), list):
            raise ValueError('Invalid story reports')
    elif endpoint == '/api/v1/dailies/latest':
        report = value.get('report')
        if not isinstance(report, dict) or not isinstance(report.get('date'), str) or not isinstance(report.get('sections'), list):
            raise ValueError('Invalid daily report')
    return value


def validate_item(item):
    if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id']:
        raise ValueError('Invalid selected item')
    if not isinstance(item.get('title'), str) or not isinstance(item.get('selected'), bool):
        raise ValueError('Incomplete selected item')
    if not isinstance(item.get('links'), dict) or not isinstance(item.get('attribution'), dict):
        raise ValueError('Missing attribution')
    for url in (item['links'].get('aihot'), item['attribution'].get('url')):
        u = urllib.parse.urlsplit(url or '')
        if u.scheme != 'https' or u.hostname not in ('aihot.news', 'aihot.virxact.com'):
            raise ValueError('Invalid attribution URL')
    score = item.get('score')
    if score is not None and (isinstance(score, bool) or not isinstance(score, (float, int)) or not 0 <= score <= 100):
        raise ValueError('Invalid upstream score')
    return item


def bounded(items):
    def stamp(item):
        value = item.get('publishedAt') or item.get('discoveredAt')
        return datetime.fromisoformat(value.replace('Z', '+00:00')) if value else now() - timedelta(days=8)
    cutoff = now() - timedelta(days=7)
    recent = [i for i in items.values() if stamp(i) >= cutoff]
    recent.sort(key=stamp, reverse=True)
    return {i['id']: i for i in recent[:MAX_SELECTED]}


class ApiCache:
    def __init__(self, root: Path, opener=urllib.request.urlopen):
        self.root = root
        root.mkdir(parents=True, exist_ok=True); root.chmod(0o700)
        self.opener = opener

    def get(self, path, key, force=False):
        if not re.fullmatch(r'[A-Za-z0-9_-]+', key) or not path.startswith('/api/v1/') or path.startswith('//'):
            raise ValueError('Invalid cache endpoint')
        file = self.root / (key + '.json')
        old = json.loads(file.read_text()) if file.exists() else None
        if old and old.get('url') == BASE + path and not force and (now() - datetime.fromisoformat(old['fetchedAt'])).total_seconds() < TTL:
            return old['data']
        headers = {'Accept': 'application/json', 'User-Agent': 'Muqiao-PrivateReader/1.0'}
        if old and old.get('url') == BASE + path and old.get('etag'):
            headers['If-None-Match'] = old['etag']
        try:
            with self.opener(urllib.request.Request(BASE + path, headers=headers), timeout=30) as response:
                u = urllib.parse.urlsplit(response.geturl())
                if response.status != 200 or u.hostname != 'aihot.news' or u.scheme != 'https':
                    raise ValueError('Unexpected upstream API response')
                cache_control = response.headers.get('Cache-Control') or ''
                if 'no-store' in cache_control.lower():
                    raise ValueError('Upstream forbids persistent caching')
                body = response.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    raise ValueError('Oversized upstream response')
                value = {'data': validate_resource(path, json.loads(body)), 'etag': response.headers.get('ETag'), 'url': BASE + path,
                         'cacheControl': cache_control, 'privateOnly': True}
        except urllib.error.HTTPError as error:
            if error.code in (404, 410):
                file.unlink(missing_ok=True)  # Removed resource must not remain available in this cache.
            if error.code != 304 or not old or old.get('url') != BASE + path:
                raise
            value = old
        value['fetchedAt'] = now().isoformat()
        atomic_json(file, value)
        return value['data']

    def selected(self):
        path = self.root / 'selected-state.json'
        state = json.loads(path.read_text()) if path.exists() else None
        if state and (now() - datetime.fromisoformat(state['fetchedAt'])).total_seconds() < TTL and state.get('complete', False):
            return {'items': len(state['items']), 'changes': 0, 'status': 'cached'}
        reset = False
        for attempt in range(2):
            if state is None:
                # Only obtain a watermark, not the complete historical database. Then seed recent reading items.
                seed = self.get('/api/v1/selected/snapshot?limit=1', 'selected-seed', force=reset)
                recent = self.get('/api/v1/items?mode=selected&window=7d&by=published&limit=100', 'selected-recent', force=reset)
                if not isinstance(seed.get('cursor'), str) or not isinstance(recent.get('items'), list):
                    raise ValueError('Missing initial selected cursor/items')
                items = {i['id']: i for i in (validate_item(i) for i in recent['items']) if i['selected']}
                state = {'cursor': seed['cursor'], 'items': bounded(items), 'removed': [], 'complete': False,
                         'coverage': 'recent7d, seed100, maximum200; not a full historical mirror', 'privateOnly': True,
                         'fetchedAt': now().isoformat()}
                atomic_json(path, state)
            changes = 0
            try:
                for _ in range(5):  # <=500 mutations per run; leave the continuation cursor for the next run.
                    cursor = state['cursor']
                    page = self.get('/api/v1/selected/changes?' + urllib.parse.urlencode({'cursor': cursor, 'limit': 100}), 'selected-changes', force=True)
                    if not isinstance(page.get('cursor'), str) or not isinstance(page.get('hasMore'), bool) or not isinstance(page.get('changes'), list):
                        raise ValueError('Invalid selected changes envelope')
                    if page.get('count') != len(page['changes']) or len(page['changes']) > 100:
                        raise ValueError('Invalid selected changes count')
                    if page['hasMore'] and page['cursor'] == cursor:
                        raise ValueError('Cursor did not advance')
                    items = dict(state['items']); removed = list(state['removed'])
                    for change in page['changes']:
                        if change.get('op') == 'remove' and isinstance(change.get('id'), str):
                            key = change['id']; items.pop(key, None)
                            removed = [x for x in removed if x != key] + [key]
                        elif change.get('op') == 'upsert':
                            item = validate_item(change.get('item')); key = item['id']
                            removed = [x for x in removed if x != key]
                            if item['selected']: items[key] = item
                            else: items.pop(key, None); removed.append(key)
                        else:
                            raise ValueError('Invalid selected mutation')
                    state = {**state, 'cursor': page['cursor'], 'items': bounded(items), 'removed': removed[-200:],
                             'complete': not page['hasMore'], 'fetchedAt': now().isoformat()}
                    atomic_json(path, state)  # Answer mutations and their watermark commit together.
                    changes += len(page['changes'])
                    if not page['hasMore']:
                        break
                return {'items': len(state['items']), 'changes': changes, 'complete': state['complete'], 'reset': reset}
            except urllib.error.HTTPError as error:
                if error.code != 409 or attempt:
                    raise
                state = None; reset = True  # Upstream epoch expired: fresh bounded baseline.
        raise ValueError('Could not reset selected cursor')

    def prune(self, story_ids):
        for file in self.root.glob('story-*.json'):
            if file.stem.removeprefix('story-') not in story_ids:
                file.unlink()


def story_id(link):
    u = urllib.parse.urlsplit(link)
    if u.scheme != 'https' or u.hostname not in ('aihot.news', 'aihot.virxact.com'):
        raise ValueError('Invalid upstream story link')
    match = re.fullmatch(r'/story/([A-Za-z0-9_-]{1,128})', u.path)
    if not match:
        raise ValueError('Invalid upstream story ID')
    return match[1]
