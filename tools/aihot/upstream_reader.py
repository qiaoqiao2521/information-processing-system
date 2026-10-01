#!/usr/bin/env python3
"""Refresh the user's private upstream results, without models or public ingestion."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import time
import urllib.error
from upstream_feed import FEEDS, sync, atomic_json
from upstream_api import ApiCache, story_id, now


def refresh(root, pause=1, admin_export_dir=None):
    results = []; errors = []
    rate_limited = False
    root.mkdir(parents=True, exist_ok=True); root.chmod(0o700)
    with (root / '.reader.lock').open('a') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return {'status': 'already-running'}
        def run(name, fn):
            nonlocal rate_limited
            if rate_limited:
                errors.append({'name': name, 'error': 'SkippedAfterRateLimit', 'http': None})
                return
            try: results.append({'name': name, 'result': fn()})
            except Exception as error:
                errors.append({'name': name, 'error': type(error).__name__, 'http': getattr(error, 'code', None)})
                rate_limited = getattr(error, 'code', None) == 429
            time.sleep(pause)
        for feed in FEEDS:
            run('rss:' + feed, lambda feed=feed: sync(feed, root))
        api = ApiCache(root / 'api')
        run('selected', api.selected)
        run('daily-api', lambda: {'date': api.get('/api/v1/dailies/latest', 'daily-latest')['report']['date']})
        ids = []
        def hot():
            value = api.get('/api/v1/hot-topics', 'hot-topics')
            items = value.get('items')
            if not isinstance(items, list) or len(items) > 10: raise ValueError('Invalid hot topics')
            ids.extend(story_id(i['links']['story']) for i in items if i['links'].get('story'))
            return {'items': len(items)}
        run('hot-topics', hot)
        def story(key):
            value = api.get('/api/v1/stories/' + key, 'story-' + key)['story']
            return {'reports': len(value['reports']), 'hasDigest': bool(value.get('digest')),
                    'timeline': len(value.get('storyline') or [])}
        for key in dict.fromkeys(ids):
            run('story:' + key, lambda key=key: story(key))
        if any(r['name'] == 'hot-topics' for r in results): api.prune(set(ids))
        # Keep selected/category RSS views consistent with explicit deselection and corrected API answers.
        state_path = root / 'api/selected-state.json'
        if state_path.exists():
            state = json.loads(state_path.read_text()); removed = set(state['removed']); selected = state['items']
            for feed in ('selected', 'ai-models', 'ai-products', 'industry', 'paper', 'tip'):
                path = root / (feed + '.json')
                if not path.exists(): continue
                cache = json.loads(path.read_text()); items = []
                for item in cache['items']:
                    if item['id'] in removed: continue
                    upstream = selected.get(item['id'])
                    if upstream and feed != 'selected' and upstream.get('category') != feed:
                        continue
                    if upstream:
                        item = {**item, 'title': upstream['title'], 'summary': upstream.get('summary'),
                                'score': upstream.get('score'), 'selected': upstream['selected'],
                                'links': upstream['links'], 'attribution': upstream['attribution']}
                    items.append(item)
                cache['items'] = items; atomic_json(path, cache)
        report = {'checkedAt': now().isoformat(), 'privateOnly': True, 'results': results, 'errors': errors}
        atomic_json(root / 'reader-status.json', report)
        if admin_export_dir is not None and state_path.exists():
            admin_export_dir.mkdir(parents=True, exist_ok=True); admin_export_dir.chmod(0o700)
            state = json.loads(state_path.read_text())
            target = admin_export_dir / 'snapshot.json'
            atomic_json(target, {'checkedAt':state['fetchedAt'], 'items':state['items'],
                                 'removed':state['removed'], 'complete':state['complete'], 'privateOnly':True})
            if os.geteuid() == 0:
                os.chown(admin_export_dir,1000,1000); os.chown(target,1000,1000)
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, default=Path.home() / '.local/share/information-hub/aihot-reader')
    parser.add_argument('--admin-export-dir', type=Path, help='Private read-only projection for the UID1000 API container')
    args = parser.parse_args(); result = refresh(args.cache_dir, admin_export_dir=args.admin_export_dir)
    print(json.dumps(result, ensure_ascii=False))
    return 1 if result.get('errors') else 0


if __name__ == '__main__':
    raise SystemExit(main())
