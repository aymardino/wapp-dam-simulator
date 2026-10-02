#!/usr/bin/env bash
# Server update after a git push: pulls the code, rebuilds the image, restarts with minimal downtime.
set -euo pipefail
cd /opt/wapp/app
git pull --ff-only
docker compose up -d --build
docker image prune -f >/dev/null
docker compose ps
