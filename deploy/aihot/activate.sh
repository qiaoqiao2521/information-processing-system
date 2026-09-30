#!/usr/bin/env bash
# Run on 436 after the new origin is verified. Never remove the old site or volumes.
set -euo pipefail
task_root=/opt/intelligence-hub/aihot
task_backup="$task_root/rollback/$(date -u +%Y%m%dT%H%M%SZ)"
install -d -m 700 "$task_backup"
cp -p /etc/cloudflared/intelligence-hub.yml "$task_backup/tunnel.yml"
chmod 600 "$task_backup/tunnel.yml"
readlink -f /opt/intelligence-hub/current > "$task_backup/old-release.txt"
systemctl is-enabled intelligence-hub-maintenance.timer > "$task_backup/old-timer-enabled.txt" || true
curl -fsS http://127.0.0.1:8088/api/health > "$task_backup/new-health.json"
install -m 644 "$task_root/units/intelligence-hub-aihot-bridge.service" /etc/systemd/system/
install -m 644 "$task_root/units/intelligence-hub-aihot-bridge.timer" /etc/systemd/system/
systemctl daemon-reload
python3 - <<'PY'
from pathlib import Path
p=Path('/etc/cloudflared/intelligence-hub.yml')
v=p.read_text()
if v.count('service: http://127.0.0.1:8080') != 1:
    raise SystemExit('Expected exactly one old origin; configuration retained')
t=p.with_suffix('.next');t.write_text(v.replace('service: http://127.0.0.1:8080','service: http://127.0.0.1:8088'))
t.chmod(p.stat().st_mode & 0o777);t.replace(p)
PY
systemctl disable --now intelligence-hub-maintenance.timer
systemctl enable --now intelligence-hub-aihot-bridge.timer
systemctl restart cloudflared-intelligence-hub.service
if ! curl --retry 3 --retry-delay 2 --retry-all-errors -fsS https://intel.muqiao.xyz/api/health > "$task_backup/public-health.json"; then
  cp -p "$task_backup/tunnel.yml" /etc/cloudflared/intelligence-hub.yml
  systemctl restart cloudflared-intelligence-hub.service
  systemctl disable --now intelligence-hub-aihot-bridge.timer
  systemctl enable --now intelligence-hub-maintenance.timer
  exit 1
fi
ln -sfn "$task_backup" "$task_root/rollback-current"
printf 'Activated; rollback backup: %s\n' "$task_backup"
