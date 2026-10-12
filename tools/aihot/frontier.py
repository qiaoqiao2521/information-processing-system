#!/usr/bin/env python3
"""Fixed public frontier sources → Firecrawl v2 → existing AIHOT ingest/publication.

No model or account browser is used. Durable receipts bound paid attempts, including
failures/unknowns. Cached pending items replay ingest without paying for a new scrape.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup

CONFIG = Path(__file__).with_name('frontier_sources.json')
DATE = re.compile(r'\b(?:20\d{2}-\d{2}-\d{2}(?:T[0-9:.]+(?:Z|[+-]\d{2}:?\d{2}))?|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2},?\s+20\d{2}|\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2})\b', re.I)


def timestamp(value):
    if not isinstance(value, str):
        return None
    value = re.sub(r'(\d)(st|nd|rd|th)\b', r'\1', value).strip()
    value = re.sub(r'([A-Za-z]{3})\.', r'\1', value)
    for fmt in (None, '%Y-%m-%d', '%B %d, %Y', '%b %d, %Y', '%B %d %Y', '%b %d %Y', '%d %B %Y'):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00')) if fmt is None else datetime.strptime(value, fmt)
            dt = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
            return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        except ValueError:
            pass
    return None


def clean_url(url):
    u = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((u.scheme, u.netloc, u.path, '', ''))


def allowed(url, source):
    u = urllib.parse.urlsplit(url)
    return (u.scheme == 'https' and not u.username and not u.password
            and u.netloc == urllib.parse.urlsplit(source['index']).netloc
            and re.fullmatch(source['pattern'], url) is not None
            and u.path.rstrip('/') not in {p.rstrip('/') for p in source.get('denyPaths', [])})


def listing(data, source):
    soup = BeautifulSoup(data.get('html', ''), 'html.parser')
    found = {}
    for a in soup.select(source.get('itemSelector', 'a[href]')):
        url = clean_url(urllib.parse.urljoin(source['index'], a['href']))
        if not allowed(url, source):
            continue
        title = a.get_text(' ', strip=True)
        if not title and a.get('aria-labelledby'):
            title = ' '.join(node.get_text(' ', strip=True) for key in a['aria-labelledby'].split()
                             if (node := soup.find(id=key)) is not None)
        parent = a
        date = None
        for _ in range(4):
            parent = parent.parent
            if parent is None or parent.name in {'body', 'html'}:
                break
            t = parent.find('time')
            if t and timestamp(t.get('datetime') or t.get_text(' ', strip=True)):
                date = timestamp(t.get('datetime') or t.get_text(' ', strip=True)); break
            text = parent.get_text(' ', strip=True)
            if len(text) < 1500:
                dates = DATE.findall(text)
                if len(dates) == 1 and timestamp(dates[0]):
                    date = timestamp(dates[0]); break
        old = found.get(url)
        if old is None or (date and not old['publishedAt']):
            found[url] = {'url': url, 'title': title, 'publishedAt': date}
    return sorted(found.values(), key=lambda x: x['publishedAt'] or '', reverse=True)


def material(data, item, source, baseline):
    meta = data.get('metadata', {})
    if meta.get('statusCode', 200) != 200:
        raise ValueError('non-200 target response')
    final_url = clean_url(meta.get('url') or meta.get('sourceURL') or item['url'])
    if not allowed(final_url, source):
        raise ValueError('unexpected target redirect')
    soup = BeautifulSoup(data.get('html', ''), 'html.parser')
    heading = soup.find('h1')
    title = (heading.get_text(' ', strip=True) if heading else '') or meta.get('ogTitle') or meta.get('title') or item['title']
    if not isinstance(title, str) or len(title.strip()) < 8 or re.search(r'access denied|just a moment|captcha|sign in to continue', title, re.I):
        raise ValueError('missing title or verification page')
    date = None
    for key in ('article:published_time', 'datePublished', 'publishedTime', 'publicationDate'):
        date = timestamp(meta.get(key))
        if date:
            break
        tag = soup.find('meta', attrs={'property': key}) or soup.find('meta', attrs={'name': key})
        date = timestamp(tag.get('content')) if tag else None
        if date:
            break
    if not date:
        tag = soup.find('time')
        date = timestamp(tag.get('datetime') or tag.get_text(' ', strip=True)) if tag else None
    # JSON-LD datePublished is preferred over a text-page guessed date.
    if not date:
        for script in soup.find_all('script', type='application/ld+json'):
            match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', script.get_text())
            if match and timestamp(match[1]):
                date = timestamp(match[1]); break
    date = date or item.get('publishedAt')
    if not date:
        area = soup.find('article') or soup.find('main')
        text = area.get_text(' ', strip=True)[:1200] if area else ''
        dates = DATE.findall(text)
        if len(dates) == 1:
            date = timestamp(dates[0])
    description = meta.get('description') or meta.get('ogDescription')
    if not description:
        tag = soup.find('meta', attrs={'name': 'description'})
        description = tag.get('content') if tag else ''
    # Public original description is bounded; full source text stays in the private cache.
    description = re.sub(r'\s+', ' ', str(description or '')).strip()[:900]
    if not description:
        description = '原站未提供摘要；请阅读原文。'
    summary = f'【{source["signal"]}｜原始材料，待AI处理】{description}'
    return {'url': item['url'], 'title': title.strip()[:500], 'summary': summary,
            'publishedAt': date, 'bodyText': '',
            'raw': {'collector': 'firecrawl-v2', 'signalKind': source['signal'],
                    'originalDescription': description, 'dateEvidence': 'original' if date else 'unknown',
                    '_aihot': {'baseline': baseline}}}


def save(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False)); tmp.chmod(0o600); tmp.replace(path)


def env_file(path):
    values = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith('#') and '=' in line:
            key, val = line.split('=', 1)
            values[key.strip()] = val.strip().strip('"').strip("'")
    return values


class Scraper:
    def __init__(self, state, path, key, cap):
        self.state, self.path, self.key, self.cap = state, path, key, cap

    def scrape(self, url):
        now = time.time()
        receipts = self.state.setdefault('receipts', [])
        receipts[:] = [r for r in receipts if r['at'] > now - 7 * 86400]
        if sum(r['at'] > now - 86400 for r in receipts) >= self.cap:
            raise RuntimeError('24h attempt budget exhausted')
        # A crash/unknown result never produces an immediate paid retry.
        if any(r['url'] == url and r['status'] != 'ok' and r['at'] > now - 86400 for r in receipts):
            raise RuntimeError('failed or unknown scrape in 24h cooldown')
        receipt = {'at': now, 'url': url, 'status': 'started'}
        receipts.append(receipt); save(self.path, self.state)
        req = urllib.request.Request('https://api.firecrawl.dev/v2/scrape',
            json.dumps({'url': url, 'formats': ['html', 'links'], 'onlyMainContent': False,
                        'timeout': 45000, 'maxAge': 3600000}).encode(),
            headers={'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                value = json.load(response)
            if value.get('success') is not True or not isinstance(value.get('data'), dict):
                raise RuntimeError('Firecrawl did not confirm success')
            if value['data'].get('metadata', {}).get('statusCode', 200) != 200:
                raise RuntimeError('target did not return HTTP200')
            receipt.update(status='ok', credits=value.get('data', {}).get('metadata', {}).get('creditsUsed'),
                           scrapeId=value.get('data', {}).get('metadata', {}).get('scrapeId'))
            save(self.path, self.state)
            return value['data']
        except Exception as error:
            receipt['status'] = 'failed' if isinstance(error, urllib.error.HTTPError) else 'unknown'
            receipt['httpStatus'] = getattr(error, 'code', None); save(self.path, self.state)
            raise RuntimeError(f'Firecrawl {receipt["status"]}; HTTP {receipt["httpStatus"]}') from None


def ingest(items, source, base, token):
    req = urllib.request.Request(base + '/api/ingest/items',
        json.dumps({'sourceId': source['id'], 'sourceName': source['name'], 'items': items}).encode(),
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.load(response)
        if result.get('ok') is not True:
            raise RuntimeError('ingest not confirmed')
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'Ingest HTTP {error.code}') from None
    publish(source['id'])
    return result['created']


def publish(source_id, check=False):
    code = Path(__file__).with_name('frontier_publish.mjs').read_text()
    subprocess.run(['docker', 'exec', '-i', 'muqiao-intel-api-1', 'node', '--input-type=module', '-', source_id,
                    *(['--check'] if check else [])], input=code, text=True, check=True, timeout=90)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path('/opt/intelligence-hub/aihot'))
    parser.add_argument('--base', default='http://127.0.0.1:8088')
    parser.add_argument('--sources', nargs='+')
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text())
    sources = [s for s in config['sources'] if not s.get('nativeConfig')]
    if args.sources:
        if set(args.sources) - {s['id'] for s in sources}:
            parser.error('unsupported source')
        sources = [s for s in sources if s['id'] in args.sources]
    root = args.root / 'frontier'; root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / '.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({'status': 'already_running'})); return
        path = root / 'state.json'
        state = json.loads(path.read_text()) if path.exists() else {'receipts': [], 'sources': {}}
        secret = env_file(args.root / 'frontier.env')['FIRECRAWL_API_KEY']
        token = env_file(args.root / 'app/.env')['INGEST_TOKEN']
        scraper = Scraper(state, path, secret, config['dailyAttemptCap'])
        results = []
        for source in sources:
            current = state['sources'].setdefault(source['id'], {'seen': []})
            try:
                publish(source['id'], check=True)
                if current.get('pending'):
                    created = ingest(current['pending'], source, args.base, token)
                    current['seen'] = list(dict.fromkeys(current['seen'] + [i['url'] for i in current['pending']]))
                    del current['pending']; save(path, state)
                    results.append({'source': source['id'], 'status': 'replayed', 'created': created}); continue
                if current.get('checkedAt', 0) > time.time() - config['intervalHours'] * 3600:
                    results.append({'source': source['id'], 'status': 'not_due'}); continue
                data = scraper.scrape(source['index'])
                links = listing(data, source)
                if not links:
                    raise RuntimeError('no recognized article links')
                save(root / (source['id'] + '-index.json'), data)
                baseline = not current.get('initialized')
                new = [i for i in links if i['url'] not in current['seen']][:config['itemsPerSource']]
                items = []
                for item in new:
                    page = scraper.scrape(item['url'])
                    save(root / (source['id'] + '-' + __import__('hashlib').sha256(item['url'].encode()).hexdigest()[:16] + '.json'), page)
                    items.append(material(page, item, source, baseline))
                    # Preserve a successful detail if the next paid request or ingest fails.
                    current['pending'] = items; save(path, state)
                created = ingest(items, source, args.base, token) if items else 0
                if baseline:
                    current['seen'] = [i['url'] for i in links]  # Existing history is not dribbled in as news.
                else:
                    current['seen'] = list(dict.fromkeys(current['seen'] + [i['url'] for i in items]))
                current.update(initialized=True, checkedAt=time.time())
                current.pop('pending', None); save(path, state)
                results.append({'source': source['id'], 'status': 'ok', 'found': len(links), 'created': created})
            except Exception as error:
                current['lastError'] = str(error)[:160]; save(path, state)
                results.append({'source': source['id'], 'status': 'failed', 'error': str(error)[:160]})
        print(json.dumps({'sources': results, 'attempts24h': sum(r['at'] > time.time() - 86400 for r in state['receipts'])}, ensure_ascii=False))
        if any(r['status'] == 'failed' for r in results):
            raise SystemExit(1)


if __name__ == '__main__':
    main()
