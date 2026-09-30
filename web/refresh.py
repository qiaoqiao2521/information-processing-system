#!/usr/bin/env python3
"""Collect live reading sources safely, then optionally publish the snapshot to 436."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.catalog import safe_url

ROOT = Path(__file__).resolve().parents[1]
COLLECTORS = {
    'hacker-news': ('fetch_hacker_news.py', 'hacker_news_sources_latest.json'),
    'juya': ('fetch_juya_daily.py', 'juya_daily_sources_latest.json'),
    'papers': ('fetch_hf_daily_papers.py', 'hf_daily_papers_sources_latest.json'),
    'rss': ('fetch_qiaomu_rss.py', 'qiaomu_rss_sources_latest.json'),
    'ak-rss': ('fetch_ak_rss.py', 'ak_rss_sources_latest.json'),
    'x': ('fetch_x_google.py', 'x_google_sources_latest.json'),
    'trending': ('fetch_github_trending.py', 'github_trending_latest.json'),
    'digest': ('fetch_follow_builders.py', 'ai_builders_digest_sources_latest.json'),
}
DEFAULT_SOURCES = tuple(source for source in COLLECTORS if source != 'x')


def validate(source, document):
    key = 'repos' if source == 'trending' else 'selectedSources' if source == 'digest' else 'items'
    items = document.get(key, [])
    if not isinstance(items, list) or not items:
        raise ValueError('Collector returned no items; previous snapshot retained')
    for item in items:
        title = item.get('title') or item.get('full_name') or item.get('originalTitle')
        url = item.get('url') or item.get('arxiv_url') or item.get('hf_url')
        if not title or not safe_url(url):
            raise ValueError('Collector returned an item without a title or valid source URL')
    if not (document.get('generated_at') or document.get('generatedAt')):
        raise ValueError('Collector did not record its collection time')
    return len(items)


def promote(source, staged, output_dir, backup_dir):
    """Validate before any replacement; keep the original timestamps in the backup."""
    manifest = staged / COLLECTORS[source][1]
    document = json.loads(manifest.read_text(encoding='utf-8'))
    count = validate(source, document)
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(staged.iterdir()):
        if not path.is_file():
            continue
        target = output_dir / path.name
        if target.exists():
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup_dir / path.name)
        with tempfile.NamedTemporaryFile(dir=output_dir, prefix='.refresh-', delete=False) as tmp:
            temporary = Path(tmp.name)
        try:
            shutil.copy2(path, temporary)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    return {'source': source, 'status': 'updated', 'count': count,
            'collectedAt': document.get('generated_at') or document.get('generatedAt'),
            'editionDate': document.get('date'), **({'coverage': document['coverage']} if 'coverage' in document else {})}


def collect(source, output_dir, backup_dir):
    script, filename = COLLECTORS[source]
    with tempfile.TemporaryDirectory(prefix=f'hub-{source}-') as temporary:
        workspace = Path(temporary)
        staged = workspace / 'output_to_user'
        staged.mkdir()
        env = dict(os.environ, WORKSPACE_ROOT=str(workspace), FOLLOW_BUILDERS_FEED_MODE='remote')
        if source == 'x':
            env['HUB_PREVIOUS_X_SNAPSHOT'] = str(output_dir / filename)

        def run(path, *args):
            result = subprocess.run([sys.executable, str(path), *map(str, args)], cwd=ROOT,
                                    env=env, capture_output=True, text=True, timeout=270 if source == 'x' else 120)
            if result.returncode:
                raise RuntimeError(f'{path.name} exited {result.returncode}: {result.stderr[-500:]}')
            return result.stdout

        if source == 'trending':
            payload = json.loads(run(ROOT / 'cron_tasks/daily-github-trending-ai-watch/scripts' / script))
            payload['generated_at'] = datetime.now(timezone.utc).isoformat()
            (staged / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        elif source == 'digest':
            scripts = ROOT / 'cron_tasks/ai-builders-digest-5briefs/scripts'
            bundle = workspace / 'bundle.json'
            bundle.write_text(run(scripts / script), encoding='utf-8')
            run(scripts / 'build_digest_outputs.py', '--bundle-path', bundle)
        else:
            args = ('--limit', '3', '--items-per-feed', '2') if source == 'rss' else ()
            run(ROOT / 'tools/knowledge_pipeline/acquisition' / script, *args)
        return promote(source, staged, output_dir, backup_dir)


def refresh_sources(output_dir, sources, backup):
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = {pool.submit(collect, source, output_dir, backup): source for source in dict.fromkeys(sources)}
        for future in as_completed(pending):
            source = pending[future]
            try:
                result = future.result()
            except Exception as error:
                result = {'source': source, 'status': 'failed', 'error': str(error)}
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT.parent / 'output_to_user')
    parser.add_argument('--sources', nargs='+', choices=tuple(COLLECTORS), default=list(DEFAULT_SOURCES))
    parser.add_argument('--deploy', action='store_true')
    parser.add_argument('--destination', type=Path, help='Release archive directory; required with --deploy')
    args = parser.parse_args()
    if args.deploy and not args.destination:
        parser.error('--deploy requires --destination')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    backup = args.output_dir / '.refresh-history' / run_id
    results = refresh_sources(args.output_dir, args.sources, backup)
    backup.mkdir(parents=True, exist_ok=True)
    (backup / 'result.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    # A partial collection is reviewable; automatic publication requires every requested source to succeed.
    if any(result['status'] != 'updated' for result in results):
        raise SystemExit('Some sources failed; no automatic publication. Valid snapshots were preserved.')
    if args.deploy:
        subprocess.run([sys.executable, str(ROOT / 'web/publish.py'), '--output-dir', str(args.output_dir),
                        '--destination', str(args.destination), '--deploy'], check=True)


if __name__ == '__main__':
    main()
