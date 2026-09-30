#!/usr/bin/env python3
"""Adapt the project AK feed bundle to the public reading catalog; no AI selection."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from web.catalog import iso_date, safe_url


def normalize(payload, collected_at):
    errors = payload.get('errors', [])
    feed_count = payload['feed_count']
    if feed_count <= len(errors):
        raise ValueError('All AK feeds failed; previous snapshot retained')
    items, seen = [], set()
    for entry in payload['items']:
        url = safe_url(entry.get('link'))
        published = iso_date(entry.get('published_at'))
        if not url or url in seen or not entry.get('title') or not published:
            continue
        seen.add(url)
        content = entry.get('summary', '')
        excerpt = content if len(content) <= 400 else content[:400].rsplit(' ', 1)[0] + '…'
        items.append({'title': entry['title'], 'url': url, 'published_at': published,
                      'summary': excerpt, 'content': content if len(content) > 400 else '',
                      'feed_title': entry.get('feed_name', '')})
    if not items:
        raise ValueError('No dated AK articles available; previous snapshot retained')
    items.sort(key=lambda item: datetime.fromisoformat(item['published_at']), reverse=True)
    return {'source': 'ak-rss', 'generated_at': collected_at,
            'window': {key: payload[key] for key in ('start_date', 'target_date', 'days', 'timezone')},
            'coverage': {'total': feed_count, 'succeeded': feed_count - len(errors), 'failed': len(errors)},
            'selection': 'unscored', 'candidate_count': len(items), 'limit': 150,
            'items': items[:150], 'errors': errors}


def main():
    script = ROOT / 'skills/ak-rss-digest/scripts/fetch_today_feed_items.py'
    result = subprocess.run([sys.executable, str(script), '--days', '7', '--timeout', '8',
                             '--workers', '12', '--format', 'json'],
                            capture_output=True, text=True, timeout=105, check=True)
    document = normalize(json.loads(result.stdout), datetime.now(timezone.utc).isoformat())
    output = Path(os.environ.get('WORKSPACE_ROOT', str(ROOT.parent))) / 'output_to_user'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'ak_rss_sources_latest.json').write_text(
        json.dumps(document, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'items': len(document['items']), 'coverage': document['coverage']}))


if __name__ == '__main__':
    main()
