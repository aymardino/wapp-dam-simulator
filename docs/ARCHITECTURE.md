# Architecture v2: engine, API, trading rooms

*October 2026. Complements `docs/MARKET_RULES.md` (rules) and `CHANGELOG.md` (history). Version française : [fr/ARCHITECTURE.md](fr/ARCHITECTURE.md).*

## Overview

```
engine/            clearing engine (Pyomo + HiGHS), explicit rules, tests           → untouched by the API
   clearing.py     run_clearing(...)  →  prices, flows, dispatch, summary
   scenarios.py    Reference 2024 set and teaching variants
   checks.py       solver-independent verification of a result
   cli.py          python -m engine.cli: CSV in, JSON out
api/               FastAPI: multi-participant trading rooms, orders, clearings       → uvicorn api.main:app
   storage.py      SQLAlchemy (SQLite by default, Postgres through WAPP_API_DATABASE_URL)
   schemas.py      input/output contracts (pydantic), order validation
   service.py      room → engine rows adapter, execution, trader result
   auth.py         participant token (Authorization: Bearer)
   main.py         /api/v1 routes, serves web/dist when present
web/               React front end (Vite, Tailwind): landing page, hall, trading floor, trainer desk
app.py, pages/     historical Streamlit application (local training), still functional
```

The engine knows nothing about rooms or participants: the API hands it rows (zone, trader, actor, …) exactly as the Streamlit application does. Both interfaces therefore share the same rules and the same tests.

## API data model

| Object | Fields | Role |
|--------|--------|------|
| Room (`rooms`) | 6-character code, name, phase (`submission` / `cleared`), settings (hours, rules, currency, language, date, scenario, fill mode), NTC overrides | a training session or a demonstration |
| Participant (`participants`) | name (organisation), zone, role (`trainer` / `trader` / `observer`), token | a connected person; several traders per zone are possible |
| Order (`orders`) | participant, kind (`supply` / `demand` / `block` / `mic`), JSON content | a trader's order book, replaced as a whole on each submission |
| Clearing (`clearing_runs`) | date, frozen settings, welfare, volume, full JSON result | history of a room's runs |

The trainer receives a token when creating the room; traders receive one when joining. The token travels in the `Authorization: Bearer …` header. There are no accounts and no passwords: a room is a closed space whose code is the key, which matches training usage. For a durable public exposure, rooms expire and creation is rate-limited (see below).

## Routes

| Method and route | Who | Effect |
|------------------|-----|--------|
| `GET /api/v1/reference` | all | zones, lines and default NTC, profiles, price bounds, available rules, reference data |
| `GET /api/v1/demo` | all | clearing of the Reference 2024 scenario (prices, flows, NTC, welfare, volume, saturated lines, reference orders, profiles, load), computed on first call and cached in the process |
| `GET /api/v1/scenarios` | all | teaching scenarios (Reference 2024 and its four variants) |
| `POST /api/v1/rooms` | trainer | creates a room, returns the code and the trainer token |
| `GET /api/v1/rooms/{code}` | all | full state (settings, effective NTC and scenario NTC, participants, counts, last clearing) |
| `GET /api/v1/rooms/{code}/state` | all | light state for periodic refresh |
| `POST /api/v1/rooms/{code}/join` | trader, observer | joins the room, returns a token |
| `GET /api/v1/rooms/{code}/me` | participant | identity bound to the token |
| `DELETE /api/v1/rooms/{code}/participants/{id}` | trainer | removes a participant and its orders |
| `PUT /api/v1/rooms/{code}/settings` | trainer | simulated hours, scenario, pricing, paradoxical-block and sharing rules, fill mode (`actors`, `zones`, `none`), currency, language, date |
| `PUT /api/v1/rooms/{code}/phase` | trainer | opens or closes submission |
| `PUT` / `DELETE /api/v1/rooms/{code}/ntc` | trainer | overrides or restores the NTC |
| `GET` / `PUT /api/v1/rooms/{code}/orders/me` | trader | reads or replaces the trader's order book (refused when submission is closed) |
| `GET` / `DELETE /api/v1/rooms/{code}/orders` | trainer | all order books; general deletion |
| `POST /api/v1/rooms/{code}/clearing` | trainer | runs the engine on the room's orders, stores the result, closes submission |
| `GET /api/v1/rooms/{code}/results` | all | clearing history |
| `GET /api/v1/rooms/{code}/results/{id|latest}` | all | full result (prices, flows, dispatch, summary, diagnostics) |
| `GET /api/v1/rooms/{code}/results/{id|latest}/me` | participant | the trader's result: its actors, blocks, MIC, the prices of its zone |
| `GET /api/v1/rooms/{code}/results/{id}/prices.csv` | all | zonal prices as CSV |
| `GET /api/v1/rooms/{code}/events` | all | Server-Sent Events stream of the room state |

Engine errors (`ClearingError`) come back as 422 with the message in clear. The interactive documentation is served on `/docs`.

## Front end

Four screens, one design system:

- **Landing page** (`/`): public presentation, live map of the Reference 2024 case driven by `GET /api/v1/demo`, per-zone supply / demand explorer, price heatmap, engine description, spec sheet, disclaimers. Public links (repository, technical note, documentation) are in `web/src/links.ts`.
- **Hall** (`/app`): create a room or join one; links to the trainer and trader guides (`/guide/formateur`, `/guide/trader`, served from `docs/guides/` as Markdown).
- **Trading floor** (`/room/:code`): on the left the trader's order book (segments, blocks, MIC), in the middle the market (map, price heatmap and curves, dispatch, flows, last clearing), on the right the trader's result (volumes, surplus, rejected orders, zone prices).
- **Trainer desk** (`/desk/:code`): indicators, clearing run, phase, settings and rules, NTC, participants and orders, consistency checks, per-zone summary.

Design system: neutral palette (`page`, `surface`, `panel`, `ink`, `line`) and a single accent (deep green), two font weights (400, 500), figures in a monospace font, thin rules rather than bordered cards, colour reserved for meaning (net position, block status). The landing page adds an editorial serif (Instrument Serif), a dark map theme and amber highlights. Everything is defined in `web/tailwind.config.js` and `web/src/styles.css`.

The front end subscribes to the room event stream (`/rooms/{code}/events`, Server-Sent Events) and reloads the state on every change; without the stream it falls back to polling every ten seconds. Charts (prices, dispatch, flows) are rendered by ECharts in SVG; the price heatmap is plain HTML; the map relies on Natural Earth outlines (public domain) extracted at build time.

## Running everything in development

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000        # API + documentation on /docs
cd web && npm install && npm run dev             # front end on http://localhost:5173 (proxy /api → 8000)
```

In production, `npm run build` produces `web/dist`, which the API serves at the root; a single Docker image is enough (`Dockerfile.app`). Hosting options are in `docs/DEPLOYMENT.md`.

## Safeguards for public exposure

Rooms without activity for `WAPP_ROOM_TTL_DAYS` days (30) are purged, at most `WAPP_MAX_ROOMS_PER_IP_PER_DAY` rooms per address and per day (20), allowed origins through `WAPP_CORS_ORIGINS`.

## What remains

End-to-end tests of the front end, lazy loading of ECharts to lighten the first paint, a two-country teaching sandbox.
