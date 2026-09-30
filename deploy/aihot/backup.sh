#!/usr/bin/env bash
set -euo pipefail
umask 077
task_root=/opt/intelligence-hub/aihot
install -d -m 700 "$task_root/backups"
exec 9>"$task_root/.backup.lock"
flock -n 9 || exit 0
cd "$task_root/app"
task_file="$task_root/backups/aihot-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"
trap 'rm -f "$task_file.partial"' EXIT
docker compose -f docker-compose.yml -f compose.override.yaml exec -T db pg_dump -U aihot -d aihot | gzip > "$task_file.partial"
gzip -t "$task_file.partial"
mv "$task_file.partial" "$task_file"
# Prune only this job's completed backups; manually named rollback dumps are preserved.
python3 - <<'PY'
from pathlib import Path
for p in sorted(Path('/opt/intelligence-hub/aihot/backups').glob('aihot-????????T??????.sql.gz'),reverse=True)[7:]: p.unlink()
PY
printf 'Database backup completed\n'
