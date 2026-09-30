#!/usr/bin/env python3
"""Install the script-only maintenance runtime and native timer on the 436 origin."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    'web/__init__.py', 'web/catalog.py', 'web/refresh.py', 'web/publish.py', 'web/maintain.py',
    'web/systemd/intelligence-hub-maintenance.service', 'web/systemd/intelligence-hub-maintenance.timer',
    'tools/knowledge_pipeline/acquisition/fetch_hacker_news.py',
    'tools/knowledge_pipeline/acquisition/fetch_juya_daily.py',
    'tools/knowledge_pipeline/acquisition/fetch_hf_daily_papers.py',
    'tools/knowledge_pipeline/acquisition/fetch_qiaomu_rss.py',
    'tools/knowledge_pipeline/acquisition/fetch_ak_rss.py',
    'tools/knowledge_pipeline/acquisition/fetch_x_google.py',
    '.agents/skills/ai-influence-digest/references/accounts_65.txt',
    'web/requirements-maintenance.txt',
    'skills/ak-rss-digest/scripts/fetch_today_feed_items.py',
    'skills/ak-rss-digest/references/feeds.opml',
    'cron_tasks/daily-github-trending-ai-watch/scripts/fetch_github_trending.py',
    'cron_tasks/ai-builders-digest-5briefs/scripts/fetch_follow_builders.py',
    'cron_tasks/ai-builders-digest-5briefs/scripts/build_digest_outputs.py',
    'data/qiaomu-rss/tidings.json',
)

INSTALL = r'''
set -eu
base=/opt/intelligence-hub/maintenance
version="$1"
release="$base/releases/$version"
mkdir -p "$release"
tar --no-same-owner -xzf "/tmp/hub-maintenance-$version.tar.gz" -C "$release"
python3 - "$release" <<'VERIFY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1])
manifest=json.loads((root/'maintenance-package.json').read_text())
for name, expected in manifest['files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected, name
print('Maintenance package verified:', manifest['version'])
VERIFY
test -x "$base/venv/bin/python" || python3 -m venv "$base/venv"
"$base/venv/bin/python" -m pip install --disable-pip-version-check -r "$release/web/requirements-maintenance.txt"
ln -s "$release" "$base/.next"
mv -Tf "$base/.next" "$base/current"
install -m 644 "$release/web/systemd/intelligence-hub-maintenance.service" /etc/systemd/system/
install -m 644 "$release/web/systemd/intelligence-hub-maintenance.timer" /etc/systemd/system/
systemd-analyze verify /etc/systemd/system/intelligence-hub-maintenance.service /etc/systemd/system/intelligence-hub-maintenance.timer
systemctl daemon-reload
systemctl enable --now intelligence-hub-maintenance.timer
rm "/tmp/hub-maintenance-$version.tar.gz"
if [ "${2:-run}" = run ]; then systemctl start --no-block intelligence-hub-maintenance.service; fi
systemctl show intelligence-hub-maintenance.timer -p ActiveState -p NextElapseUSecRealtime
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-run', action='store_true', help='Install and enable timer without an immediate extra collection')
    args = parser.parse_args()
    version = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    checksums = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
    host = 'racknerd-436b0c0'
    with tempfile.TemporaryDirectory(prefix='hub-maintenance-install-') as temporary:
        package = Path(temporary) / 'maintenance-package.json'
        package.write_text(json.dumps({'version': version, 'files': checksums}, indent=2))
        archive = Path(temporary) / f'{version}.tar.gz'
        with tarfile.open(archive, 'w:gz') as bundle:
            for name in FILES:
                bundle.add(ROOT / name, arcname=name)
            bundle.add(package, arcname=package.name)
        subprocess.run(['scp', '-q', str(archive), f'{host}:/tmp/hub-maintenance-{version}.tar.gz'], check=True)
        subprocess.run(['ssh', '-o', 'BatchMode=yes', host, 'sh', '-s', '--', version, 'skip' if args.no_run else 'run'],
                       input=INSTALL, text=True, check=True)


if __name__ == '__main__':
    main()
