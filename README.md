# WAPP Day-Ahead Market Simulator

**Open reference implementation of day-ahead zonal market coupling for the West African Power Pool, built as a multi-user training tool.**
MS OSE 2025 project — Mines Paris-PSL, with SENELEC and EPEX SPOT · version 2 (October 2026) · public site: https://wapp-dam-simulator.mastereose.fr

*Version française : [README.fr.md](README.fr.md). Guides, market rules and reference data are also available in French under [docs/fr/](docs/fr/).*

---

## What it does

Each participant joins a trading room as a country's organisation, submits sell and buy orders for every hour of the next day, and the trainer runs the clearing. The engine answers three questions, in order: **who trades** (the set of trades that creates the most value within line capacities), **how to break ties** (the most energy traded), **at what price** (one price per country and per hour, chosen within the set of prices consistent with the quantities). Every rule is written down in [docs/MARKET_RULES.md](docs/MARKET_RULES.md) and checked by tests.

Highlights of version 2 (details in [CHANGELOG.md](CHANGELOG.md)):

- block, linked and exclusive orders actually modelled (MILP), paradoxical blocks handled with the EUPHEMIA rule;
- minimum income condition (MIC) with iterative withdrawal, explicit sharing rule for equal-price orders;
- zonal prices chosen within the complete admissible set (no paradoxically rejected simple order, no price gap without congestion);
- training rooms over a REST API (one code per room, trainer and trader tokens, live updates), a React front end with a public landing page, the historical Streamlit application kept for local training;
- a sourced "Reference 2024" data set and four teaching variants, editable NTC, any subset of hours;
- bilingual interface (French / English), configurable currency, Apache 2.0 licence.

## Quick start

Requirements: Python 3.10 or newer; Node 20 or newer to build the web front end.

```bash
pip install -r requirements.txt
cd web && npm install && npm run build && cd ..     # compiles the front end into web/dist
uvicorn api.main:app --reload --port 8000
```

Open `http://localhost:8000` (public page), `http://localhost:8000/app` (training rooms) and `http://localhost:8000/docs` (interactive API documentation). The HiGHS solver (`highspy`) is installed with the dependencies and handles every case, blocks included, in under a second; Gurobi is used automatically when present.

Command line, without the API:

```bash
python -m engine.cli --reference --hours 19 --out result.json --prices-csv prices.csv
```

The historical Streamlit application is still available: `streamlit run app.py` (administrator password through `WAPP_ADMIN_PASSWORD` or `.streamlit/secrets.toml`; there is no default).

## Running a session

1. **Create a room** (trainer): a six-character code to share; settings, rules and NTC are per room.
2. **Join** (traders): organisation name and country; stepwise orders (rising prices, hourly profile), block orders (simple, linked to a parent, or in an exclusive group), minimum income conditions.
3. **Clear**: the trainer chooses the hours (24 h or a single hour), the scenario, the pricing, paradoxical-block and sharing rules, the fill mode for actors not played, then runs the engine.
4. **Results**: prices, flows, dispatch, block orders, each trader's own result, analysis (surpluses, congestion rent, consistency checks), tables and exports.

[Trainer guide](docs/guides/formateur.en.md) and [trader guide](docs/guides/trader.en.md), also served inside the application.

## Model

| Step | Question | Problem | Type |
|------|----------|---------|------|
| P1 | Who trades? | welfare maximisation under zonal balance, NTC, α constraint, block links | LP, MILP with blocks |
| P1bis | How to break ties? | volume maximisation at the exact optimal welfare | LP |
| P2 | At what price? | admissible prices (full equilibrium conditions) closest to the midpoint of the interval | LP |

Zones: NGA, BEN, TGO, GHA, CIV, BFA, MLI, SEN, GIN, SLE, LBR, GNB, GMB, NER. Interconnections: 15 pairs, signed flows. CIV/GHA/BFA interdependence constraint with α = 0.7.

| Order type | Model |
|------------|-------|
| Price / quantity segments (4 per actor) | continuous variables, partial acceptance |
| Simple block | binary, fill-or-kill over its hours |
| Linked block | child ≤ parent |
| Exclusive group | at most one option |
| Minimum income condition (MIC) | income ≥ fixed term + variable term × volume, otherwise withdrawal and rerun |

Paradoxically accepted blocks are rejected iteratively (EUPHEMIA rule, default). Paradoxically rejected blocks are tolerated and reported. Equal-price orders are shared pro rata (or by submission order).

## Scenarios and data

The trainer picks a base set, "Reference 2024 (public sources)", and four teaching variants that change one thing only (hydro drought, Nigeria–Benin line out of service, expensive gas, high demand). The 2024 set rebuilds available capacities, peak demands, costs by technology and exchange capacities from public sources; every figure and every estimate is documented in [docs/REFERENCE_DATA.md](docs/REFERENCE_DATA.md). Prices produced on these data are simulation results, not observed market prices: the WAPP day-ahead market has not started yet.

## Tests

```bash
pip install pytest
pytest -q
```

Sixty-six tests cover the engine (reference values of Deliverable 2: welfare 22,317,910 and volume 167,900 MWh on the test set, 23,082,419 with blocks, 23,775,223 with linked and exclusive blocks), the database migration, the API, the command line and a campaign of random cases checked by `engine/checks.py`. Tests use a temporary database (`WAPP_DB_PATH`) and never touch `data/`.

## Architecture

```
wapp_simulator/
├── engine/                 clearing engine (Pyomo + HiGHS): clearing.py, scenarios.py, checks.py, cli.py, db.py
├── api/                    FastAPI trading rooms: main.py (routes), service.py, storage.py, schemas.py, auth.py
├── web/                    React front end (Vite, TypeScript, Tailwind): landing page, hall, trading floor, trainer desk
├── app.py, pages/, ui_common.py   historical Streamlit application
├── tests/                  engine, database, API, CLI and property tests
├── docs/                   MARKET_RULES.md, ARCHITECTURE.md, REFERENCE_DATA.md, DEPLOYMENT.md, guides/, fr/
├── deploy/, render.yaml, docker-compose.yml, Caddyfile, Dockerfile.app   hosting
└── data/                   local SQLite databases (created at first run, never published)
```

Two-page overview in [docs/TECHNICAL_SHEET.md](docs/TECHNICAL_SHEET.md) (Word and PDF versions: `scripts/export_docs.sh`, needs pandoc and Chrome). Details in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); hosting (domain, Render, virtual server, Docker, HTTPS) in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Data and privacy

- NTC values and hourly profiles are estimates documented for training and research, not WAPP operational data. They can be replaced per room (NTC editor) and by participants' orders.
- Everything runs locally by default; the SQLite databases stay on the host. Never publish the `data/` folder.
- The repository contains neither the WAPP logo nor the Tractebel/ECOWAS network map: the interface uses a neutral mark (`assets/mark.svg`) and a map generated from Natural Earth (`assets/network_map.png`, public domain).

## Authors

Kodjovi Plakoo and Enrico Patanè (Mines Paris-PSL, MS OSE 2025). The simulator grew out of a group project of the Advanced Master OSE that also included Lucien Kouakou, Mouhamadou Sow and Wissem Hmila. Supervision: El Hadji Tamsir Diop (SENELEC) and Adrien Atayi (EPEX SPOT).

## Licence

Code under the [Apache 2.0](LICENSE) licence. Reference data and documentation under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attributions in [NOTICE](NOTICE). Independent educational simulator, not affiliated with the West African Power Pool.

---

## Résumé en français

Implémentation ouverte, documentée et testée du couplage de marché day-ahead zonal appliqué au West African Power Pool, conçue comme outil de formation multi-utilisateurs : salles de marché, ordres par segments et blocs, conditions de revenu minimum, clearing P1 → P1bis → P2 avec prix choisis dans l'ensemble admissible complet, données de référence 2024 sourcées. Documentation complète en français dans [README.fr.md](README.fr.md) et [docs/fr/](docs/fr/).
