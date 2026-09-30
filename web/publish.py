#!/usr/bin/env python3
"""Build an allowlisted snapshot and optionally atomically deploy it to 436."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone

if not __package__:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.catalog import catalog, code_digest, dataset_digest, source_paths, scrub

WEB = Path(__file__).resolve().parent
CODE_FILES = ('__init__.py', 'server.py', 'catalog.py', 'public/index.html', 'public/app.js', 'public/style.css', 'public/workflows.json')


def build_release(destination, output_dir, web_dir=WEB, *, managed_by=None):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='hub-release-') as temporary:
        root = Path(temporary)
        for name in CODE_FILES:
            target = root / 'web' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(web_dir / name, target)
        (root / 'snapshots').mkdir()
        (root / 'web/data').mkdir()
        for name, source in source_paths(output_dir, web_dir / 'data').items():
            if not source.is_file():
                continue
            # Invalid JSON is a failed build, never a silently dropped source.
            value = scrub(json.loads(source.read_text(encoding='utf-8')))
            payload = json.dumps(value, ensure_ascii=False, indent=2)
            if re.search(r'/home/muqiao|/root/|cfut_[A-Za-z0-9_-]{12,}|-----BEGIN [A-Z ]*PRIVATE KEY-----', payload):
                raise ValueError(f'Private data pattern in {name}; review before publication')
            target = root / ('web/data' if source.parent == web_dir / 'data' else 'snapshots') / name
            target.write_text(payload, encoding='utf-8')
            shutil.copystat(source, target)
        library = catalog(root / 'snapshots', root / 'web/data')
        if not library['items']:
            raise ValueError('No reading items available for publication')
        now = datetime.now(timezone.utc)
        code = code_digest(root / 'web')
        data = dataset_digest(root / 'snapshots', root / 'web/data')
        release_id = f'{now:%Y%m%dT%H%M%S}-{code[:8]}-{data[:8]}'
        revision = subprocess.run(['git', '-C', str(web_dir.parent), 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
        if not revision and (web_dir.parent / 'release.json').is_file():
            revision = json.loads((web_dir.parent / 'release.json').read_text()).get('sourceRevision', '')
        manifest = {'id': release_id, 'publishedAt': now.isoformat(), 'sourceRevision': revision,
                    'codeDigest': code, 'datasetDigest': data, 'itemCount': len(library['items']),
                    'files': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}}
        if managed_by:
            manifest['managedBy'] = managed_by
        (root / 'release.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        archive = destination / f'{release_id}.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            for file in sorted(root.rglob('*')):
                if file.is_file():
                    tar.add(file, arcname=str(file.relative_to(root)))
    return archive, manifest


REMOTE_DEPLOY = r'''
set -eu
root=/opt/intelligence-hub
exec 9>"$root/.publish.lock"
flock -w 360 9
release_id="$1"
archive="/tmp/hub-${release_id}.tar.gz"
release="$root/releases/$release_id"
previous=$(readlink "$root/current" || true)
install -d -m 755 "$root/releases"
mkdir "$release"
tar --no-same-owner -xzf "$archive" -C "$release"
python3 - "$release" <<'VERIFY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]); m=json.loads((root/'release.json').read_text())
for name, expected in m['files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected, name
print('Verified release:',m['id'],'items:',m['itemCount'])
VERIFY
install -d /etc/systemd/system/intelligence-hub.service.d
dropin=/etc/systemd/system/intelligence-hub.service.d/20-release.conf
if [ -f "$dropin" ]; then cp "$dropin" "$release/previous-service.conf"; fi
rollback() {
  if [ -n "$previous" ]; then ln -sfn "$previous" "$root/.rollback"; mv -Tf "$root/.rollback" "$root/current"; else rm -f "$root/current"; fi
  if [ -f "$release/previous-service.conf" ]; then cp "$release/previous-service.conf" "$dropin"; else rm -f "$dropin"; fi
  systemctl daemon-reload
  systemctl restart intelligence-hub.service
  printf 'Deployment failed; previous service restored.\n' >&2
}
cat > "$dropin" <<'UNIT'
[Service]
WorkingDirectory=/opt/intelligence-hub/current
Environment=HUB_PUBLIC_READONLY=1
Environment=HUB_OUTPUT_DIR=/opt/intelligence-hub/current/snapshots
Environment=HUB_HOST=127.0.0.1
ExecStart=
ExecStart=/usr/bin/python3 /opt/intelligence-hub/current/web/server.py 8080
UNIT
ln -s "$release" "$root/.current-next"
mv -Tf "$root/.current-next" "$root/current"
trap rollback EXIT
systemctl daemon-reload
systemctl restart intelligence-hub.service
python3 - "$release" <<'HEALTH'
import json,sys,time,urllib.request,urllib.error
from pathlib import Path
expected=json.loads((Path(sys.argv[1])/'release.json').read_text())
for attempt in range(30):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8080/api/status',timeout=2) as r: actual=json.load(r)
        assert actual['publicReadOnly'] is True
        assert all(actual[k]==expected[k] for k in ('codeDigest','datasetDigest'))
        print('Origin verified:',actual['codeDigest'],actual['datasetDigest'])
        break
    except (OSError,AssertionError,ValueError):
        time.sleep(.5)
else:
    raise SystemExit('Origin did not become ready')
HEALTH
trap - EXIT
rm "$archive"
printf 'Current release: %s\nPrevious release: %s\n' "$release" "${previous:-legacy /opt/intelligence-hub}"
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, default=WEB.parent.parent / 'output_to_user')
    p.add_argument('--destination', type=Path, required=True, help='Local directory for the release archive')
    p.add_argument('--deploy', action='store_true', help='Publish the generated archive to racknerd-436b0c0')
    args = p.parse_args()
    archive, manifest = build_release(args.destination, args.output_dir)
    print(json.dumps({k:v for k,v in manifest.items() if k != 'files'}, ensure_ascii=False, indent=2), flush=True)
    print(archive, flush=True)
    if args.deploy:
        host = 'racknerd-436b0c0'
        subprocess.run(['scp', '-q', str(archive), f'{host}:/tmp/hub-{manifest["id"]}.tar.gz'], check=True)
        subprocess.run(['ssh', '-o', 'BatchMode=yes', host, 'sh', '-s', '--', manifest['id']], input=REMOTE_DEPLOY, text=True, check=True)

if __name__ == '__main__':
    main()
