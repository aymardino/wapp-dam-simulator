# Changelog

All notable changes to the simulator are recorded here, most recent first. Each entry corresponds to one or more git commits (`git log`). The detailed French history up to step 13 is kept in [docs/fr/CHANGELOG.md](docs/fr/CHANGELOG.md).

## [2.0.0-dev] — October 2026

### Step 14 — English-first repository, French documentation kept

- Code, comments, docstrings, engine error messages, API documentation, tests, scripts and configuration files translated to English. Actor and plant names in the reference data keep their original language.
- Reference documentation in English: `README.md`, `docs/MARKET_RULES.md`, `docs/ARCHITECTURE.md`, `docs/REFERENCE_DATA.md`, `docs/DEPLOYMENT.md`, `NOTICE`, this changelog. French versions kept in `README.fr.md` and `docs/fr/` (rules, architecture, data, deployment, changelog). The trainer and trader guides remain bilingual in `docs/guides/`.
- Internal project notes (audit, valorisation plan) moved out of the public tree (`private/`, ignored by git).
- Landing page: the "simulation" notices are plain captions instead of amber pills; the explorer's import / export annotation is drawn as a white label beside the curves (a single marker when the volume is small) instead of overlapping the crossing.
- The git history was rewritten before publication (3 October 2026) to remove a former default administrator password and two images that were not free of rights.

### Step 13 — Landing page, second version: own identity, zone explorer, fixes

**Added**
- Render deployment: `render.yaml` (Blueprint: Docker service, persistent disk on `/app/data`, health check, variables), procedure in `docs/DEPLOYMENT.md`; the image listens on `PORT` when the platform provides it (8000 otherwise) and runs as root in the container (Render disks are mounted for root), health check in `deploy/healthcheck.py`.
- New landing page (`web/src/pages/Landing.tsx`) with an identity distinct from the application: editorial serif headings (Instrument Serif), scrolling price ticker (14 zonal prices at the current hour, welfare, volume, saturated lines), dark "control room" map driven by a histogram hour selector (bar height = mean price of the hour), a country's position read on click.
- Explorer "Why this price, in this zone, at this hour": the zone's supply and demand curves built from the 2024 reference orders (hourly quantities = quantity × profile, as in the engine), zonal price, imported or exported volume read from the flows, generated explanatory sentence, order table (accepted / marginal / out of market).
- Price heatmap (`web/src/components/PriceHeatmap.tsx`): one row per zone sorted by mean price, one column per hour, colour = price, rule between price groups, clickable zone; replaces the fourteen overlapping curves on the landing page and precedes the curves in the rooms' Prices tab.
- "The engine" section (P1 → P1bis → P2 with the admissible-interval sketch), spec sheet as a table, three uses, terminal block with the real command-line output (welfare 22,317,910, volume 167,900 MWh), disclaimers, authors.
- Transparency on the figures: "Simulation · reconstructed data" badge on the map, the ticker, the explorer and the price heatmap; "Where do these figures come from?" box (sourced / estimated / assumption, link to `docs/REFERENCE_DATA.md`); statement that the market has not started and that no observed prices exist. Public wording without project jargon.
- `GET /api/v1/demo` also returns the reference orders, the hourly profiles, the load curve and the saturated hours per line.
- `NetworkMap`: dark theme, click selection, unique gradient id (several maps per page).
- Fluid layout (`.wrap`, 1,440 px maximum, percentage margins), checked at 375, 1,000, 1,280 and 1,900 px.
- Default scenario of new rooms: "Reference 2024 (public sources)", the same as the landing page. The trainer desk shows the chosen scenario's capacities as defaults (`ntc_default` in the room payload); test `test_default_scenario_is_reference_2024`.
- A single base set: the four teaching variants (hydro drought, Nigeria–Benin line out of service, expensive gas, high demand) now derive from the Reference 2024 scenario; the Deliverable 2 set, renamed "Test set (Livrable 2)", is hidden from the lists offered to trainers (`scenario_list(include_hidden=True)`) and remains the regression test set.
- New mark: stepwise supply curve with the equilibrium point at the market price (`web/public/mark.svg`, `web/public/mark-light.svg` for dark headers, `assets/mark.svg`), horizontal logo with name and tagline for documents and social media (`web/public/logo.svg`).

**Fixed**
- ECharts charts (`Chart`): the instance was destroyed and recreated on every parent render, leaving an empty chart until hover on the landing page (rendered every 1.5 s); one instance per mount, `setOption` on change, memoised options, animation disabled.
- Horizontal overflow on mobile (order table: fixed columns).

### Step 12 — Landing page, hosting kit, pre-publication cleanup

**Added**
- Bilingual public landing page (`web/src/pages/Landing.tsx`, route `/`; the room hall moves to `/app`): presentation, live map of the 2024 reference case computed by the engine, the three programs P1 / P1bis / P2 in plain words, contents, audiences, "open and verifiable" section, disclaimers, authors, links to the guides, the repository and the technical note (`web/src/links.ts`).
- `GET /api/v1/demo`: clearing of the Reference 2024 scenario cached for the website (test `test_demo_endpoint_is_cached`).
- Hosting kit: `.env.example` (domain, CORS, purge, quota), `deploy/setup_server.sh` (Ubuntu server installation: Docker, firewall, clone, start), `deploy/update.sh`, `deploy/backup.sh`; `Caddyfile` parameterised by `DOMAIN` with security headers and www redirect; `Dockerfile.app` with health check and proxy headers; deployment guide rewritten (purchases, GitHub publication, installation, operations, pre-announcement checklist).
- Continuous integration: front-end build (Node 20) in addition to the Python tests.
- Page metadata (title, description, Open Graph).

**Changed**
- Neutral mark instead of the WAPP logo in the front end and in the Streamlit application; network map `assets/network_map.png` generated from Natural Earth (public domain) instead of the Tractebel/ECOWAS map of Deliverable 3. Both original files removed from the repository and its history: the project is not affiliated with the WAPP and those images are not free of rights.
- Streamlit application: no default administrator password any more; the Administration page stays locked until `WAPP_ADMIN_PASSWORD` or `admin_password` (secrets.toml) is set.
- Suite: 65 tests.

### Step 11 — Guides, "background actors" fill mode, domain name

**Added**
- Trainer and trader guides, in French and English (`docs/guides/`), available inside the application (Guides menu, pages `/guide/formateur` and `/guide/trader`): preparing a session, a typical three-round sequence, settings explained, reading the results, frequently asked questions; on the trader side, how to submit each order type and understand the result.
- "Background actors" fill mode (new room default): every actor of the scenario stays in the market, except those of a participant's zone whose name matches the participant's or one of its orders, which are replaced. A free name erases nothing; a name picked from the list takes the real actor's place. The two other modes ("zones without submission", "none") remain available; selector with explanation in the trainer desk, rule described in `docs/MARKET_RULES.md`.
- Domain name chosen: wapp-dam-simulator.org (Caddyfile, docker-compose, deployment guide).
- Suite: 64 tests.

### Step 10 — Simulation campaign, participant names, licence

**Added**
- `engine/checks.py`: independent verification of a result (prices within bounds, flows within NTC, generation-demand balance at every hour, net positions summing to zero, accepted ≤ offered, no paradoxically accepted block, accepted child ⇒ accepted parent, at most one option per exclusive group, every minimum income condition satisfied or withdrawn, welfare identity).
- `tests/test_properties.py`: random cases (segments, simple, linked and exclusive blocks, MIC, pricing, block and sharing rules, scenarios, 24 h or a single hour, reduced NTC) verified by these checks; 25 cases by default, 150 run before publication (`WAPP_PROPERTY_CASES=150 pytest`), plus edge cases.
- Apache 2.0 licence (`LICENSE`), `NOTICE` with attributions and the WAPP non-affiliation statement; data and documentation under CC BY 4.0.
- API: participant name unique per room (case-insensitive, normalised spaces), removal of a participant and its orders by the trainer, organisation suggestions per zone in the hall.

**Fixed (found by the campaign)**
- Paradoxical-block rule `l2`: a block forced to acceptance because paradoxically rejected could remain paradoxically accepted at the new prices; it is now rejected for good (the "no PAB" rule prevails). A forcing that makes the problem infeasible (block impossible to absorb) is released and noted.
- Maximum number of PAB-loop iterations tied to the number of blocks (at most two changes per block).
- Suite: 62 tests.

### Fixes — map legibility and multiple identities

- Map: smaller nodes; The Gambia, Guinea-Bissau, Sierra Leone, Liberia, Togo and Benin are offset towards the sea with a leader line to their real position, so they no longer overlap.
- One browser can remember several trader or observer identities for a room (useful for testing alone): list in "Your rooms" on the hall, switcher in the trading floor header. The trainer / trader switch links only appear on the device holding the corresponding token.

### Step 9 — Sourced reference data and realistic defaults

**Added**
- Scenario `reference_2024` "Reference 2024 (public sources)": available capacities, peak demands, costs by technology and line capacities from public 2023-2025 sources, documented figure by figure in `docs/REFERENCE_DATA.md` with estimates flagged.
- In the trading floor, the quantities and prices proposed for a new order come from the typical plant sizes of the zone (a few tens of MW in Togo or The Gambia, several hundred in Nigeria) instead of 100 MW everywhere.
- Plausibility test of the 2024 set (35 tests in total).

### Step 8 — Scenarios, real time, export and safeguards (API and engine)

**Added**
- `engine/scenarios.py`: teaching scenarios derived from the reference data (reference, hydro drought, Nigeria–Benin line out of service, expensive gas, high demand). The engine accepts `reference_rows` to substitute these data in the demonstration and in zone filling.
- API: `GET /scenarios`, `scenario` setting per room (the scenario's NTC apply under the trainer's), `GET /rooms/{code}/results/{id}/prices.csv`, event stream `GET /rooms/{code}/events` (Server-Sent Events: room state on every change, heartbeat every 15 s, `?once=true` for a single state).
- Safeguards for going online: purge of rooms without activity for `WAPP_ROOM_TTL_DAYS` days (30 by default) at every creation, and at most `WAPP_MAX_ROOMS_PER_IP_PER_DAY` rooms per address and per day (20 by default, 429 beyond).
- Five tests (34 in total).

**Front end**
- ECharts charts (SVG renderer) in the trading floor and the trainer desk: hourly prices per zone (the trader's zone in bold), stacked dispatch per profile with accepted demand, hourly flows of the eight main corridors with the NTC in the legend. Map / Prices / Dispatch / Flows tabs.
- Real time: subscription to the room event stream ("Live" badge), reload on every state change; automatic fallback to polling when the browser does not support server events.
- Scenario selector with its description in the trainer settings; CSV and JSON export links.

### Fix — trainer settings saved immediately

- The "Fill zones without submission" checkbox was only taken into account after a click on "Save"; the announcement under the button reflected the checkbox, the clearing used the saved setting, hence a reference welfare despite an unticked box. Every trainer-desk setting is now saved on change, and the checkbox sits next to the run button.
- Country borders in black on the map.
- Development reminder: the API must be restarted (or started with `--reload`) after a change to the Python code; the compiled front end is re-read on every request.

### Step 7 — Geographic map and legibility of the demonstration mode

**Added**
- West Africa map background under the network, from Natural Earth (public domain, 50 m resolution) extracted at build time by `web/scripts/extract_map.mjs` into an 86 KB GeoJSON; Mercator projection (d3-geo), nodes placed at the countries' real coordinates, member countries highlighted, legend and credit.
- The engine returns `summary.reference_zones`, the list of zones filled with reference data. The trainer desk announces before the run how many zones have orders and what will happen to the others; after the run, a "Demonstration" banner appears when no participant order was used, and a "Reference data · N zones" badge otherwise. Same badge in the trading floor.

**Changed**
- The API refuses (422, message in clear) to run a clearing without any order when reference-data filling is disabled, instead of producing an empty market at 250 per MWh.
- Two tests added (29 in total).

### Step 6 — First design pass of the front end and role navigation

**Added**
- Design system v1: dark header with the mark, room name, code and phase; white panels with thin rules; tabs for the order book (sell, buy, blocks, MIC) with counters; indicators; empty states that explain what to do; 15 px body text, figures in a monospace font.
- WAPP network map (`web/src/components/NetworkMap.tsx`): 14 zones coloured by price at the chosen hour, 15 lines whose width follows the flow, direction arrow, saturated lines in red, legend. Shown in the trading floor and the trainer desk.
- Hall: "Your rooms" list with, for each remembered room, access to the trainer desk and the trading floor; switch link between the two in the header; the trainer desk offers to join one's own room as a trader (code prefilled).

**Fixed**
- A trainer joining their room as a trader lost access to the desk: tokens are now kept per room and per role, room name remembered.

### Step 5 — REST API and skeleton of the new application

**Added**
- `api/`: FastAPI API of multi-participant trading rooms (room creation by the trainer, code to share, traders and observers with a token, order book per trader replaced on each submission, settings and rules per room, NTC overrides, clearing run, result history, individual result). Separate SQLAlchemy database (`data/rooms.db`, or Postgres through `WAPP_API_DATABASE_URL`). Interactive documentation on `/docs`. The engine is untouched: the API hands it the same rows as Streamlit.
- `engine/cli.py`: command line of the engine (CSV in, JSON and prices CSV out).
- `web/`: skeleton of the new React front end (Vite, TypeScript, Tailwind) with the sober design system (neutral palette, one accent, two weights), bilingualism, the typed API client and the three screens: hall, trader's trading floor, trainer desk.
- `docs/ARCHITECTURE.md`: data model, routes, front-end structure, startup.
- `Dockerfile.app`: single image API + compiled front end.
- Tests `tests/test_api.py` (full flow, permissions, validations) and `tests/test_cli.py`.
- Front end compiled with Node 24 and checked in the browser on the full flow: room creation, trader joining and submitting orders, clearing run by the trainer, market and individual result displayed. One token per room and per role, so that a trainer can also test as a trader from the same browser.
- Deployment guide (workstation, training network, Internet), `docker-compose.yml` and `Caddyfile` (automatic HTTPS behind a domain name).

### Step 4 — Remaining Deliverable 2 rules: equal-price sharing and Minimum Income Condition

**Added**
- Explicit sharing rule between orders of the same zone, side, hour and price, applied after P1bis: `prorata` (default), `order` (submission order) or `solver`. The group's accepted total, welfare, volume and the set of admissible prices are unchanged. Adjustable in Administration.
- Minimum Income Condition (Deliverable 2 §6.3): per selling actor, a fixed term and a variable term per MWh; when the income at final prices is insufficient, all its orders (and the child blocks that depend on them) are withdrawn and the full sequence is rerun until satisfaction. `mic_conditions` table, entry in the Submission page, state of each condition in the results and diagnostics.
- Results per actor: `withdrawn_mic` status for withdrawn orders.
- Four tests: pro rata and submission order (same welfare, same volume), MIC withdrawal with rerun and new price, satisfied condition, withdrawal of child blocks.
- Market rules updated (§3 P1bis, new §5 MIC, MIC_TOL tolerance, list of what remains outside the model).

### Fix — legacy database (2 October 2026, evening)

- A database created by an earlier version of the code already had an `ntc` table with the columns `zone_from, zone_to, value_mw`; `CREATE TABLE IF NOT EXISTS` left it in place and the Administration page crashed (`no such column: u`). `init_db()` now compares each table's columns with the expected ones: the legacy `ntc` table is converted, any other incompatible table is renamed `<table>_legacy_<timestamp>` without data loss, then the expected table is created.
- NTC read from the database are only reported as "modified" (engine note, administration banner) when they really differ from the defaults.
- Tests `tests/test_db.py`: migration of a legacy database (participants, NTC, incompatible table), idempotence.

### Step 3 — Documentation and publication

**Added**
- Market rules document: every rule applied by the engine, spelled out (set of admissible prices, reference price, tie-break, paradoxical blocks, tolerances, what is not modelled). Basis of the technical note.
- `Dockerfile` and `.dockerignore`; administrator password read from `WAPP_ADMIN_PASSWORD` or `.streamlit/secrets.toml`, never displayed in the interface again.
- GitHub Actions continuous integration (`.github/workflows/tests.yml`): the test suite runs on every push.
- README rewritten: installation without a Gurobi licence, session walkthrough, architecture, model, tests, data and privacy, authors.

### Step 2 — Interface (`app.py`, `ui_common.py`, `pages/`)

**Added**
- Bilingual French / English interface: dictionary of 265 strings in `ui_common.py`, language selector in the sidebar of every page, default language set by the administrator.
- Configurable currency (label, USD by default) used in every display.
- Results page: **My result** tab (offered and accepted volume, acceptance rate, income or payment, surplus, rejected orders with explanation, zone prices), **Block orders** tab (decision, average price, surplus, explained OK / PAB / PRB status, schedule), **Analysis** tab (surplus per zone, congestion rent per line, welfare identity, consistency checks, applied rules), CSV export of prices.
- Administration page: NTC editor (editable table, reset to defaults), choice of the simulated hour in 1-hour mode, choice of the pricing rule and of the paradoxical-block rule, overview of block orders, diagnostics of the last clearing.
- Submission page: structured block-order editor (side, hour range, parent, exclusive group) next to the stepwise orders, without one erasing the other; summary of the zone's blocks.
- Visible warning on the illustrative nature of NTC and profiles.

**Fixed**
- The "fill with reference data" option really fills zones without submission; the "ignore" option gives a partial market; the demonstration mode ignores submissions.
- The Results page no longer depends on matplotlib (native saturation bars) and no longer crashes on a clean installation; the accepted-demand curve is visible (dark line); displayed hours are those actually simulated; automatic refresh uses `st.fragment` instead of blocking the page.
- Clearing errors are displayed in clear (`ClearingError` message) instead of a Python traceback.
- Several traders of the same country all appear in the participant list.
- The administrator password is no longer displayed in the page.

### Step 1 — Clearing engine (`engine/clearing.py`, `engine/db.py`, `tests/`)

**Added**
- Block, linked and exclusive orders actually modelled (MILP, one binary variable per block, parent-child and exclusive-group constraints), ported from the notebook `wapp_market_clearing_final1.ipynb` (steps 4 and 5). Blocks are stored in a new `block_orders` table (zone, trader, name, side, MW, price, start hour, end hour, parent, group) instead of a text in the "profile" column.
- Paradoxical-block loop (Deliverable 2 §3.3). Default rule `euphemia`: paradoxically accepted blocks (PAB) are fixed to 0 and the clearing rerun; paradoxically rejected blocks (PRB) are tolerated and reported. Rule `l2`: PAB fixed to 0 and PRB fixed to 1 (deliverable text). Rule `none`: detection only.
- Editable NTC: `ntc` table, `get_ntc` / `set_ntc` / `reset_ntc` functions, `ntc_override` parameter actually applied to the flow bounds and the α constraint.
- Configurable simulated hours (`hours=[19]` for a peak hour, `range(24)` for the day).
- `fill_missing_zones` option: zones without any submission are filled with reference data.
- Input validation with explicit messages (`ClearingError`): unknown zone, price out of [0, 500], negative quantity, invalid hour range, unknown profile.
- Solver status checked at every step; no more Python traceback on infeasibility.
- Richer `summary`: results per actor (offered and accepted volume, average price, income or payment, surplus, rejected orders), breakdown per zone (consumer surplus, producer surplus, net position, hours without trade), congestion rent and saturated hours per line, block status (OK, PAB, PRB), rules used, consistency diagnostics.
- Test suite `tests/test_engine.py` (15 tests) pinned to the Deliverable 2 values: welfare 22,317,910 and volume 167,900 MWh (step 3), welfare 23,082,419 and 5 blocks accepted out of 6 (step 4), welfare 23,775,223 (step 5).

**Changed**
- **"Complete" P2** (mode `pricing='complete'`, default). The objective and the reference price of Deliverable 2 §2.4 are kept (price closest to the midpoint of the admissible interval), but the set of admissible prices is now described by the full KKT conditions: rejected sell ⇒ price ≤ offer, rejected buy ⇒ price ≥ bid, unsaturated line ⇒ equal prices on both sides, explicit multiplier for the interdependence constraint α. On the reference data set, this removes 30 paradoxically rejected simple orders and 74 price gaps without congestion. Mode `pricing='l2'` keeps constraints (8)-(12) of Deliverable 2 exactly, for comparison.
- Reference price: rejected orders tighten the interval (rejected sell = upper bound, rejected buy = lower bound), which gives a consistent price in zones without trade instead of 250.
- **Exact P1bis**: the welfare constraint goes from `W ≥ W* − 0.01` to `W ≥ W*`. The absolute tolerance was entirely consumed by the volume maximisation and produced a solution that no price supported any more. If the solver finds no solution to P1bis, the P1 solution is kept and flagged in the diagnostics (`tie_break`).
- Order classification thresholds: `X_TOL = 1e-4` (instead of 0.01 / 0.99) and `F_TOL = 1e-3 MW`.
- Dispatch: the profile is read from the name stored in the database (no more `flat` / `peaker` confusion), and accepted sell blocks appear in a `block` category.
- Participants: primary key `(zone, trader)`; two organisations of the same country can be connected simultaneously. Automatic migration of the old table.
- SQLite in WAL mode; database path configurable through the `WAPP_DB_PATH` environment variable (used by the tests so that `data/market.db` is never touched).
- Session settings added: `hour`, `currency`, `lang`, `pricing`, `pab_rule`, `fill_missing`.

**Removed**
- The dead import `from engine.db import get_ntc` in a silent `try/except` (the function now exists).

### Step 0 — Starting point
- Git repository initialised on the state delivered on 10 April 2026; `data/` excluded from tracking.
- Audit of anomalies and valorisation plan (internal notes, not published).
