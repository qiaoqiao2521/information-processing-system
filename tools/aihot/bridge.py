#!/usr/bin/env python3
"""Push custom collector snapshots to AIHOT; RSS and X stay out of this schedule."""
from __future__ import annotations
import argparse
import fcntl
import json
import os
from pathlib import Path
import sys
import time
import urllib.request
import urllib.error

ROOT = Path(os.environ.get('HUB_COLLECTOR_ROOT', Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(ROOT))
from web.catalog import catalog, scrub
from web.refresh import refresh_sources

CUSTOM = ('hacker-news', 'juya', 'papers', 'trending', 'digest')


def batches(library):
    for source in CUSTOM:
        items = [{'title': r['title'], 'url': r['url'], 'publishedAt': r['publishedAt'],
                  'author': r.get('author'), 'summary': r.get('summary'), 'bodyText': r.get('body'),
                  'raw': {'legacyId': r['id'], 'collectedAt': r['collectedAt']}}
                 for r in library['items'] if r['sourceId'] == source and r['url']]
        for i in range(0, len(items), 50):
            yield {'sourceId': 'hub-' + source, 'items': scrub(items[i:i + 50])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path('/opt/intelligence-hub/aihot'))
    parser.add_argument('--base', default='http://127.0.0.1:8088')
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=True)
    with (args.root / '.bridge.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        snapshots = args.root / 'snapshots'
        snapshots.mkdir(exist_ok=True)
        # Private token never enters argv, response logs, or a committed file.
        values = dict(line.split('=', 1) for line in (args.root / 'app/.env').read_text().splitlines()
                      if '=' in line and not line.startswith('#'))
        token = values['INGEST_TOKEN']
        results = refresh_sources(snapshots, CUSTOM, args.root / 'collector-backup') if args.refresh else []
        created = 0
        for index, payload in enumerate(batches(catalog(snapshots, ROOT / 'web/data'))):
            if index and index % 8 == 0:
                time.sleep(62)  # Stay below the API's 10 requests/minute limit.
            request = urllib.request.Request(args.base + '/api/ingest/items', json.dumps(payload).encode(),
                headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    created += json.load(response)['created']
            except urllib.error.HTTPError as error:
                # Abort instead of hammering an unavailable/paused service; next timer is idempotent.
                raise RuntimeError(f'Ingest stopped: HTTP {error.code}') from None
        print(json.dumps({'created': created, 'collectors': [{'source': r['source'], 'status': r['status']} for r in results], 'x': 'paused'}))


if __name__ == '__main__':
    main()
