#!/usr/bin/env bash
# Mise à jour du serveur après un git push : récupère le code, reconstruit l'image, redémarre sans interruption longue.
set -euo pipefail
cd /opt/wapp/app
git pull --ff-only
docker compose up -d --build
docker image prune -f >/dev/null
docker compose ps
