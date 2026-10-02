#!/usr/bin/env bash
# Backup of the data volume (rooms, orders, clearings) into /opt/wapp/backups, kept for 14 days.
set -euo pipefail
mkdir -p /opt/wapp/backups
STAMP=$(date +%Y%m%d-%H%M)
docker run --rm -v app_wapp-data:/data -v /opt/wapp/backups:/backup alpine tar czf "/backup/wapp-data-$STAMP.tgz" -C /data .
find /opt/wapp/backups -name 'wapp-data-*.tgz' -mtime +14 -delete
echo "backup: /opt/wapp/backups/wapp-data-$STAMP.tgz"
