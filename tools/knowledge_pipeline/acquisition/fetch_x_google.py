#!/usr/bin/env python3
"""Public X candidates: browser Google search and optional Jina Reader text.

No X API, browser credentials, model calls or notifications. Failed/empty scans
exit before writing so web.refresh retains the previous source and timestamp.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import html
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import parse_qs, urlencode, urlsplit
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
ACCOUNTS = ROOT / '.agents/skills/ai-influence-digest/references/accounts_65.txt'
FILENAME = 'x_google_sources_latest.json'
HOSTS = {'x.com', 'www.x.com', 'm.x.com', 'mobile.x.com', 'twitter.com', 'www.twitter.com', 'mobile.twitter.com'}


def risk_gate(action='check'):
    command = [os.getenv('HUB_ACCOUNT_RISK_GUARD', '/usr/local/bin/ops-account-risk'), action,
               '--scope', os.getenv('HUB_ACCOUNT_RISK_SCOPE', 'google:racknerd-436b0c0')]
    if action == 'trip':
        command += ['--reason', 'verification']
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError('Account risk gate unavailable; browser collection stopped') from None
    if result.returncode:
        raise RuntimeError('Account risk hold or unavailable state; browser collection stopped')


def stop_for_challenge():
    risk_gate('trip')
    raise RuntimeError('Google challenge: shared risk hold recorded; manual review required')


def canonical_url(value):
    try:
        u = urlsplit(value)
        if u.scheme not in {'http', 'https'} or u.hostname not in HOSTS or u.username or u.password or u.port:
            return ''
        match = re.fullmatch(r'/([A-Za-z0-9_]{1,15})/status/([1-9][0-9]{14,19})(?:/(?:photo|video)/[0-9]+)?/?', u.path)
        if match:
            return f'https://x.com/{match[1].lower()}/status/{match[2]}'
    except (ValueError, TypeError):
        pass
    return ''


def published_at(url):
    # Twitter's original Snowflake: 41 timestamp bits, 22 worker/sequence bits.
    number = int(url.rsplit('/', 1)[-1])
    if not 0 < number < 2**63:
        raise ValueError('Invalid Snowflake ID')
    return datetime.fromtimestamp(((number >> 22) + 1288834974657) / 1000, timezone.utc)


def read_accounts(path):
    handles = [s.strip().lstrip('@') for s in path.read_text().splitlines() if s.strip() and not s.lstrip().startswith('#')]
    if not handles or any(not re.fullmatch(r'[A-Za-z0-9_]{1,15}', s) for s in handles):
        raise ValueError('Account list is empty or invalid')
    return list(dict.fromkeys(s.lower() for s in handles))


def valid_candidate(url, allowed, start, now):
    url = canonical_url(url)
    if not url or url.split('/')[3] not in allowed:
        return ''
    try:
        return url if start <= published_at(url) <= now else ''
    except (ValueError, OverflowError):
        return ''


def clean_snippet(value):
    value = re.sub(r'^.*?\b(?:\d+ (?:days?|hours?|minutes?) ago)\s*[—–-]\s*', '', value, flags=re.S)
    value = re.sub(r'\s*Read more\s*$', '', value).strip()
    if any(s in value.lower() for s in ('no information is available', 'sign in to x', 'log in or sign up', 'continue with phone', 'something went wrong')):
        return ''
    return value[:1800]


def extract_jina(document, url):
    data = document.get('data') or {}
    if canonical_url(data.get('url', '')) != url:
        raise ValueError('Reader returned a different page')
    content = data.get('content', '')
    if not isinstance(content, str):
        raise ValueError('Reader returned no text')
    # Keep only the post section, never a login page, recommendations or replies.
    marker = re.search(r'(?m)^(?:#{1,3} (?:Post|Conversation)\s*|(?:Post|Conversation)\n[-=]+)\n', content)
    if not marker:
        raise ValueError('Reader post section not found')
    content = content[marker.end():]
    author = re.search(r'(?im)^.*@' + re.escape(url.split('/')[3]) + r'\b[^\n]*\n', content)
    if not author:
        raise ValueError('Reader author not found')
    content = content[author.end():]
    content = re.split(r'(?im)^(?:Quote\b|#{0,3}\s*New to X\??|Reply\b|\[.*(?:\d{1,2}:\d{2}|Views).*\]\(|\d{1,2}:\d{2}\s*[AP]M)', content)[0]
    content = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', content)
    content = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', content)
    content = html.unescape(content).strip()
    if len(content) < 30 or not clean_snippet(content):
        raise ValueError('Reader returned no usable post body')
    return content[:16000]


def read_jina(url, api_key=''):
    headers = {'Accept': 'application/json', 'X-Timeout': '12'}
    if api_key:
        headers['Authorization'] = 'Bearer ' + api_key
    request = urllib.request.Request('https://r.jina.ai/' + url, headers=headers)
    with urllib.request.urlopen(request, timeout=18) as response:
        document = json.loads(response.read(1_000_000))
    return extract_jina(document, url)


def merge_items(previous, discoveries, allowed, start, now):
    merged = {}
    for item in [*previous, *discoveries]:
        url = valid_candidate(item.get('url', ''), allowed, start, now)
        if not url:
            continue
        old = merged.get(url, {})
        current = {**item, 'url': url, 'author': '@' + url.split('/')[3], 'published_at': published_at(url).isoformat()}
        # A transient read failure must not replace an existing body with a snippet.
        if old.get('content') and not current.get('content'):
            for key in ('content', 'content_status', 'reader', 'body_fetched_at'):
                if key in old:
                    current[key] = old[key]
        merged[url] = current
    return sorted(merged.values(), key=lambda r: r['published_at'], reverse=True)[:64]


def is_search_challenge(url, body):
    # A result may itself discuss CAPTCHAs. Do not confuse its snippet with a
    # Google interstitial, which does not contain the actual results section.
    return '/sorry/' in urlsplit(url).path or ('Search Results' not in body and any(
        s in body.lower() for s in ('unusual traffic', 'not a robot', 'verify you are human')))


def check_search_page(page):
    body = page.locator('body').inner_text(timeout=4000)
    if is_search_challenge(page.url, body):
        stop_for_challenge()
    if urlsplit(page.url).hostname != 'www.google.com' or 'Search Results' not in body:
        raise RuntimeError('Google results not available; previous snapshot retained')


def collect(args):
    risk_gate()  # Before even attaching to a browser; missing state fails closed.
    from playwright.sync_api import sync_playwright, TimeoutError as BrowserTimeout

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=args.days)
    handles = read_accounts(args.accounts)
    batches = [handles[i:i + args.batch_size] for i in range(0, len(handles), args.batch_size)]
    deadline = time.monotonic() + 230
    previous = []
    prior = os.getenv('HUB_PREVIOUS_X_SNAPSHOT')
    if prior:
        try:
            previous = json.loads(Path(prior).read_text()).get('items', [])
        except (OSError, ValueError):
            pass
    discovered, seen = [], set()
    coverage = {'total': len(batches), 'succeeded': 0, 'failed': 0, 'accounts': len(handles), 'rejected': 0, 'unresolved': 0}
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(args.cdp_url, timeout=10000)
        # Owned anonymous context only. Never touch the default context's tabs or credentials.
        context = browser.new_context(locale='en-US')
        try:
            page, resolver = context.new_page(), context.new_page()
            for batch in batches:
                risk_gate()
                if time.monotonic() > deadline - 40:
                    break
                sites = ' OR '.join(f'site:x.com/{handle}/status' for handle in batch)
                query = f'({sites}) after:{start.date().isoformat()}'
                try:
                    page.goto('https://www.google.com/search?' + urlencode({'q': query, 'hl': 'en', 'num': args.per_search}),
                              wait_until='domcontentloaded', timeout=15000)
                    try:
                        page.locator('h3').first.wait_for(timeout=4000)
                    except BrowserTimeout:
                        pass
                    check_search_page(page)
                    # Read result headings and their visible snippets, not scripts or browser storage.
                    rows = page.locator('h3').evaluate_all('''heads => heads.map(h => {
                      const a=h.closest('a'); let n=h, best=h;
                      for(let i=0;i<8 && n;i++,n=n.parentElement){
                        if(n.querySelectorAll('h3').length>1 || n.innerText.length>2500) break;
                        best=n;
                      }
                      return {title:h.innerText, href:a?.href||'', text:best.innerText,
                        heading:a?.innerText||h.innerText};
                    })''')
                    coverage['succeeded'] += 1
                except BrowserTimeout:
                    continue
                # Google sometimes uses opaque /goto links. Follow in an owned page;
                # never decode them, make up a status ID, or harvest auth/session data.
                for row in rows[:args.per_search]:
                    risk_gate()
                    if time.monotonic() > deadline - 40:
                        break
                    url = canonical_url(row['href'])
                    if not url:
                        target = urlsplit(row['href'])
                        if target.hostname != 'www.google.com' or target.path not in {'/url', '/goto'}:
                            continue
                        params = parse_qs(target.query)
                        url = canonical_url((params.get('q') or params.get('url') or [''])[0])
                        if not url:
                            try:
                                # A timed-out navigation must not reuse the previous
                                # result's URL and assign this snippet to the wrong post.
                                resolver.goto('about:blank', timeout=3000)
                                resolver.goto(row['href'], wait_until='domcontentloaded', timeout=8000)
                                url = canonical_url(resolver.url)
                                if '/sorry/' in resolver.url:
                                    stop_for_challenge()
                            except BrowserTimeout:
                                url = canonical_url(resolver.url)
                    if not url:
                        coverage['unresolved'] += 1
                        continue
                    if not valid_candidate(url, handles, start, now):
                        coverage['rejected'] += 1
                        continue
                    if url in seen:
                        continue
                    seen.add(url)
                    snippet = clean_snippet(row['text'].replace(row['heading'], '', 1).strip())
                    if len(snippet) < 25:
                        continue
                    discovered.append({'url': url, 'title': snippet.replace('\n', ' ')[:110] + ('…' if len(snippet) > 110 else ''),
                                       'summary': snippet, 'content': '', 'content_status': 'snippet',
                                       'reader': 'google-browser', 'discovered_at': now.isoformat()})
                time.sleep(1)
        finally:
            context.close()  # Do not close the shared Chrome process.
    coverage['failed'] = coverage['total'] - coverage['succeeded']
    if not coverage['succeeded'] or not discovered:
        raise RuntimeError('No verified recent X candidates; previous snapshot retained')
    items = merge_items(previous, discovered, handles, start, now)
    api_key = os.getenv('JINA_API_KEY', '')
    reading = {'provider': 'Jina Reader', 'status': 'ready' if api_key else 'not-configured',
               'attempted': 0, 'failed': 0, 'fullText': 0, 'snippets': 0}
    # 436 rejects anonymous Reader calls. The explicit deployment choice is to
    # retain Google snippets until a key is configured, with no repeated 401s.
    if api_key:
        for item in items:
            if item.get('content') or reading['attempted'] >= 16 or time.monotonic() > deadline - 20:
                continue
            reading['attempted'] += 1
            try:
                item['content'] = read_jina(item['url'], api_key)
                item.update(content_status='full-text', reader='jina-reader', body_fetched_at=datetime.now(timezone.utc).isoformat())
            except urllib.error.HTTPError as error:
                reading['failed'] += 1
                if error.code in {401, 403, 429}:
                    reading['status'] = 'authentication-required' if error.code != 429 else 'rate-limited'
                    break
            except (OSError, ValueError):
                reading['failed'] += 1
            time.sleep(3.1)
    reading['fullText'] = sum(bool(i.get('content')) for i in items)
    reading['snippets'] = len(items) - reading['fullText']
    return {'generated_at': now.isoformat(), 'source': 'x', 'selection': 'unscored',
            'window': {'start': start.isoformat(), 'end': now.isoformat()},
            'coverage': coverage, 'reading': reading, 'items': items}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accounts', type=Path, default=ACCOUNTS)
    parser.add_argument('--days', type=int, default=7, choices=range(1, 31))
    parser.add_argument('--batch-size', type=int, default=8, choices=range(1, 17))
    parser.add_argument('--per-search', type=int, default=8, choices=range(1, 21))
    parser.add_argument('--outdir', type=Path, default=Path(os.getenv('WORKSPACE_ROOT', str(ROOT.parent))) / 'output_to_user')
    parser.add_argument('--cdp-url', default=os.getenv('HUB_BROWSER_CDP_URL', 'http://127.0.0.1:9222'))
    args = parser.parse_args()
    if urlsplit(args.cdp_url).hostname not in {'127.0.0.1', 'localhost', '::1'}:
        parser.error('Use the existing loopback browser or an SSH local forward')
    result = collect(args)
    args.outdir.mkdir(parents=True, exist_ok=True)
    target = args.outdir / FILENAME
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    temporary.replace(target)
    print(json.dumps({'items': len(result['items']), 'coverage': result['coverage'], 'reading': result['reading']}, ensure_ascii=False))
    return target


if __name__ == '__main__':
    main()
