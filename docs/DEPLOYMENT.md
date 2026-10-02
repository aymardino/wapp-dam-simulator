# Running and hosting the simulator

*Practical guide, October 2026. Version française : [fr/DEPLOIEMENT.md](fr/DEPLOIEMENT.md).*

## 1. Production architecture

```
Internet ──HTTPS 443──▶ Caddy or Render (automatic certificate, www → apex redirect)
                           │
                           └──HTTP──▶ api (uvicorn): public page + application + REST API
                                         └── persistent volume: data/rooms.db (rooms, orders, clearings)
```

A single Docker image (`Dockerfile.app`) compiles the React front end and packages the API; `docker-compose.yml` assembles it with Caddy on a server, `render.yaml` deploys it on Render (section 3). The public page is served at `/`, the application (room hall) at `/app`, the API at `/api/v1`, its documentation at `/docs`.

## 2. Before publishing the repository

The server deploys from the git repository; publication is also the condition of open access (Apache 2.0 licence). Checks to repeat after any change:

- `data/`, `*.db`, `.env`, `.venv/`, `web/node_modules`, `web/dist`, `private/` are ignored (`.gitignore`);
- no password or token in the code or in the history. The repository history was rewritten on 3 October 2026 before publication to remove a former default administrator password and two images that were not free of rights. If a secret ever lands in a commit, treat it as compromised: rotate it, then rewrite the history (`git filter-repo` or `git filter-branch`) and force-push;
- `LICENSE`, `NOTICE` and the non-affiliation statement are present;
- `web/src/links.ts` points to the real repository and, when published, to the technical note.

## 3. Option A: Render (managed platform)

Render builds the `Dockerfile.app` image from GitHub and serves it with HTTPS; no machine to administer. The `render.yaml` file at the root describes everything (Docker web service, persistent disk for the rooms, health check, variables).

1. Push the repository to GitHub.
2. In the Render dashboard: **New → Blueprint**, pick the repository, confirm. Render creates the `wapp-dam-simulator` service on the Starter plan with a 1 GB disk mounted on `/app/data`. The first build takes 3 to 5 minutes (front-end compilation, then Python installation).
   Without a Blueprint: **New → Web Service → the repository → Runtime Docker**, *Dockerfile path* `Dockerfile.app`, *Health check path* `/api/v1/health`, then the *Disks* tab: add a disk mounted on `/app/data`, and the *Environment* tab: the variables of `.env.example`.
3. Check `https://<service>.onrender.com/api/v1/health`, then create a room and run a clearing.
4. Domain name: *Settings → Custom Domains → Add* `wapp-dam-simulator.org` and `www.wapp-dam-simulator.org`. Render shows the DNS records to create at the registrar (an A or ALIAS record for the apex, a CNAME for www) and obtains the certificate by itself. Then put the domain in `WAPP_CORS_ORIGINS` (already the case in `render.yaml`).
5. Updates: every `git push` on `main` redeploys (*autoDeploy*). Backups: *Disks → Snapshots* (daily, kept 7 days); for a local copy, `render ssh` then `sqlite3 /app/data/rooms.db .dump`.

Points of attention: the Free plan accepts no disk (rooms would be lost at every restart) and puts the service to sleep after fifteen minutes of inactivity; take the Starter plan ($7/month, plus $0.25/month for the disk). With a disk attached, a deployment interrupts the service for a few seconds. The container listens on the port provided by Render (`PORT`); the image handles both cases.

## 4. Option B: virtual server

| Item | Recommended choice | Price range |
|---|---|---|
| Domain name | `wapp-dam-simulator.org` at a registrar (Gandi, OVH, Infomaniak, Namecheap) | €12 to €20 per year |
| Virtual server | Hetzner CX22, OVH VPS, Scaleway DEV1-S: 2 vCPU, 4 GB, Ubuntu 24.04 | €4 to €8 per month |

Sizing: a reference clearing takes 0.5 s, a training case with blocks a few seconds; a room of 20 participants runs comfortably on 2 vCPU. Disk needs are a few tens of MB. An institutional alternative (a subdomain of the school or of SENELEC) is a CNAME record towards the server, or a relay by the IT department to port 443; the `DOMAIN` variable of the `.env` file then takes that name.

1. At the registrar, create two DNS records towards the server's IPv4 address: `A @` and `A www`. Allow up to an hour of propagation.
2. Connect to the server and run the installation script (it installs Docker and the firewall, clones the repository, creates `.env`, starts the services):

```bash
ssh root@<server-address>
curl -fsSL https://raw.githubusercontent.com/<account>/wapp-dam-simulator/main/deploy/setup_server.sh -o setup_server.sh
bash setup_server.sh https://github.com/<account>/wapp-dam-simulator.git wapp-dam-simulator.org
```

3. Check: `https://wapp-dam-simulator.org` shows the site, `https://wapp-dam-simulator.org/api/v1/health` answers `{"status":"ok", …}`, `https://www.wapp-dam-simulator.org` redirects to the apex. The certificate is obtained on first access (a few seconds).
4. Create a room, join it from a phone, run a clearing.

The `/opt/wapp/app/.env` file holds the settings (template in `.env.example`):

| Variable | Role | Default |
|---|---|---|
| `DOMAIN` | name served by Caddy | wapp-dam-simulator.org |
| `WAPP_CORS_ORIGINS` | allowed origins for the API | https://wapp-dam-simulator.org |
| `WAPP_ROOM_TTL_DAYS` | purge of inactive rooms | 30 |
| `WAPP_MAX_ROOMS_PER_IP_PER_DAY` | room creation quota | 20 |

### Operating the server

| Need | Command (on the server, in `/opt/wapp/app`) |
|---|---|
| Update after a `git push` | `deploy/update.sh` |
| Back up the rooms | `deploy/backup.sh` (archives in `/opt/wapp/backups`, 14 days) |
| Nightly automatic backup | `echo '0 3 * * * /opt/wapp/app/deploy/backup.sh' \| crontab -` |
| Logs | `docker compose logs -f api` |
| Service status | `docker compose ps` |
| Restart | `docker compose restart` |
| Start from scratch (erases the rooms) | `docker compose down -v && docker compose up -d` |

The server needs no daily maintenance: Caddy renews the certificate, the API purges inactive rooms, Docker restarts the services after a reboot. Run `apt upgrade` from time to time.

### Other managed platforms

Fly.io or Railway work like Render with `Dockerfile.app`: provide a persistent disk mounted on `/app/data` (or `WAPP_API_DATABASE_URL` towards a managed Postgres, with `psycopg[binary]` in the image) and set `WAPP_CORS_ORIGINS`. Streamlit Community Cloud is not suitable (it only hosts Streamlit applications).

## 5. Before announcing the site

- `web/src/links.ts`: repository address, technical note when it is published.
- Test from a phone: landing page, room creation, order submission, clearing.
- The disclaimers (independent simulator, estimated NTC, simulated prices) are on the landing page and in `NOTICE`.
- A backup has been made and restored at least once.

## 6. On your own machine (development and demonstration)

Requirements: Python 3.10 or newer, Node 20 or newer (for the front end).

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd web && npm install && npm run build && cd ..          # compiles the front end into web/dist
uvicorn api.main:app --reload --port 8000
```

Open `http://localhost:8000` (public page), `http://localhost:8000/app` (rooms) and `http://localhost:8000/docs` (API). To develop the front end with hot reload: `cd web && npm run dev`, then `http://localhost:5173` (`/api` calls are proxied to port 8000). After any change under `web/src`, run `npm run build` again: the API serves the compiled folder. The historical Streamlit application remains available: `streamlit run app.py`.

Data: the API writes `data/rooms.db` (SQLite). To start from scratch, delete that file. Postgres: `export WAPP_API_DATABASE_URL=postgresql+psycopg://user:password@host/database`.

Local Docker image, identical to production:

```bash
docker build -f Dockerfile.app -t wapp-simulator .
docker run -d --name wapp -p 8000:8000 -v wapp-data:/app/data wapp-simulator
```

## 7. On a training network (classroom, hotspot)

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Participants open `http://<trainer-IP-address>:8000/app` and enter the room code. If the venue's firewall blocks the port, a Wi-Fi hotspot from a phone or a tunnel (`ssh -R 80:localhost:8000 nokey@localhost.run`) works around it. With the site online, the simplest is `https://wapp-dam-simulator.org/app`.

## 8. Checking that everything works

```bash
pytest -q                                   # engine, database, API, command line, random cases
curl http://localhost:8000/api/v1/health    # {"status":"ok", ...}
curl http://localhost:8000/api/v1/demo      # demonstration clearing of the landing page (cached)
```
