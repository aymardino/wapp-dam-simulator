#!/usr/bin/env bash
# Sauvegarde du volume de données (salles, ordres, clearings) dans /opt/wapp/backups, 14 jours conservés.
set -euo pipefail
mkdir -p /opt/wapp/backups
STAMP=$(date +%Y%m%d-%H%M)
docker run --rm -v app_wapp-data:/data -v /opt/wapp/backups:/backup alpine tar czf "/backup/wapp-data-$STAMP.tgz" -C /data .
find /opt/wapp/backups -name 'wapp-data-*.tgz' -mtime +14 -delete
echo "sauvegarde : /opt/wapp/backups/wapp-data-$STAMP.tgz"
