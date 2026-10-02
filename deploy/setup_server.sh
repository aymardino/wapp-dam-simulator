#!/usr/bin/env bash
# Initial installation on an Ubuntu 22.04 or 24.04 server (run once, as root or with sudo).
# Usage: bash setup_server.sh https://github.com/<organisation>/wapp-dam-simulator.git wapp-dam-simulator.org
set -euo pipefail
REPO="${1:?URL du dépôt git}"; DOMAIN="${2:?nom de domaine}"
apt-get update && apt-get install -y ca-certificates curl git ufw
if ! command -v docker >/dev/null; then curl -fsSL https://get.docker.com | sh; fi
ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw --force enable
mkdir -p /opt/wapp && cd /opt/wapp
if [ ! -d app ]; then git clone "$REPO" app; fi
cd app
if [ ! -f .env ]; then cp .env.example .env; sed -i "s/wapp-dam-simulator.org/$DOMAIN/g" .env; fi
docker compose up -d --build
echo "Deployed: https://$DOMAIN  (logs: docker compose logs -f api)"
