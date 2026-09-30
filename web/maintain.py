#!/usr/bin/env python3
"""Unattended collection and atomic publication on the existing 436 origin."""
from __future__ import annotations

from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.catalog import OUTPUT_FILES, load
from web.publish import build_release
from web.refresh import DEFAULT_SOURCES, refresh_sources

ROOT = Path('/opt/intelligence-hub')
OWNER = 'intelligence-hub-maintenance'


def atomic_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def collection_status(results, checked_at):
    """Publish a bounded status, never internal tracebacks, paths or secrets."""
    sources = {}
    for result in results:
        failed = result['status'] == 'failed'
        challenge = failed and 'Google challenge:' in result.get('error', '')
        sources[result['source']] = {'status': result['status'], 'checkedAt': checked_at,
            'message': '自动搜索已暂停；按需操作须先检查风控状态' if result['status'] == 'paused' else
                       'Google 验证提示，本轮停止，保留上次结果' if challenge else
                       '本轮采集失败，保留上次结果' if failed else '本轮已更新'}
    return {'generated_at': checked_at, 'sources': sources}


def restart_origin():
    subprocess.run(['systemctl', 'restart', 'intelligence-hub.service'], check=True, timeout=30)


def verify_origin(expected):
    for attempt in range(30):
        try:
            with urllib.request.urlopen('http://127.0.0.1:8080/api/status', timeout=2) as response:
                actual = json.load(response)
            if actual['publicReadOnly'] is True and all(actual[key] == expected[key] for key in ('codeDigest', 'datasetDigest')):
                return
        except (OSError, ValueError, KeyError):
            pass
        time.sleep(.5)
    raise RuntimeError('Published origin did not pass the fingerprint/read-only health check')


def switch_link(root, release):
    link = root / '.maintenance-next'
    link.unlink(missing_ok=True)
    link.symlink_to(release)
    link.replace(root / 'current')


def activate(root, release, manifest, restart=restart_origin, verify=verify_origin):
    previous = (root / 'current').resolve(strict=True)
    previous_manifest = load(previous / 'release.json')
    switch_link(root, release)
    try:
        restart()
        verify(manifest)
    except BaseException:
        switch_link(root, previous)
        restart()
        verify(previous_manifest)
        raise
    return previous


def prune_releases(root, protected, keep=14):
    """Prune only versions created by this job; preserve manual releases and rollback targets."""
    candidates = []
    for path in (root / 'releases').iterdir():
        if not path.is_dir() or path.is_symlink():
            continue
        manifest = load(path / 'release.json') or {}
        if manifest.get('managedBy') == OWNER and manifest.get('id') == path.name:
            candidates.append(path)
    for path in sorted(candidates, key=lambda p: p.name, reverse=True)[keep:]:
        if path.resolve() not in protected:
            shutil.rmtree(path)


def maintain(root=ROOT):
    started = datetime.now(timezone.utc).isoformat()
    with (root / '.publish.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Another publication is running; skipping this cycle.', flush=True)
            return
        report = {'startedAt': started, 'status': 'running'}
        atomic_json(root / 'maintenance-last-run.json', report)
        try:
            current = (root / 'current').resolve(strict=True)
            with tempfile.TemporaryDirectory(prefix='.maintenance-', dir=root) as temporary:
                work = Path(temporary)
                output = work / 'snapshots'
                output.mkdir()
                for name in OUTPUT_FILES:
                    path = current / 'snapshots' / name
                    if path.is_file():
                        shutil.copy2(path, output / name)
                results = refresh_sources(output, DEFAULT_SOURCES, work / 'backup')
                results.append({'source': 'x', 'status': 'paused'})
                report['sources'] = results
                if not any(item['status'] == 'updated' for item in results):
                    raise RuntimeError('All sources failed; current website retained')
                atomic_json(output / 'collection_status.json', collection_status(results, datetime.now(timezone.utc).isoformat()))
                # Failed sources retain the previously published file and collection timestamp.
                archive, manifest = build_release(work / 'archives', output, current / 'web', managed_by=OWNER)
                release = root / 'releases' / manifest['id']
                release.mkdir()
                with tarfile.open(archive) as bundle:
                    bundle.extractall(release, filter='data')
                for name, expected in manifest['files'].items():
                    if hashlib.sha256((release / name).read_bytes()).hexdigest() != expected:
                        raise ValueError(f'File checksum mismatch: {name}')
                previous = activate(root, release, manifest)
                report.update(status='partial' if any(r['status'] == 'failed' for r in results) else 'ok',
                              release=manifest['id'], datasetDigest=manifest['datasetDigest'], itemCount=manifest['itemCount'])
                prune_releases(root, {release.resolve(), previous.resolve()})
        except Exception as error:
            report.update(status='failed', error=str(error))
            raise
        finally:
            report['finishedAt'] = datetime.now(timezone.utc).isoformat()
            atomic_json(root / 'maintenance-last-run.json', report)
            print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    maintain()
