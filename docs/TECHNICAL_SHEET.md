# Technical sheet — WAPP DAM Simulator

*Version 2.0, October 2026. Version française : [fr/FICHE_TECHNIQUE.md](fr/FICHE_TECHNIQUE.md).*

| | |
|---|---|
| **Name** | WAPP DAM Simulator — day-ahead market simulator of the West African Power Pool |
| **Nature** | open reference implementation of zonal market coupling, with multi-participant training rooms |
| **Site** | https://wapp-dam-simulator.org |
| **Source code** | https://github.com/aymardino/wapp-dam-simulator |
| **Licence** | Apache 2.0 (code); CC BY 4.0 (reference data and documentation) |
| **Authors** | Kodjovi Plakoo, Enrico Patanè (Mines Paris-PSL, Advanced Master OSE 2025); supervised by El Hadji Tamsir Diop (SENELEC) and Adrien Atayi (EPEX SPOT) |
| **Status** | independent educational simulator, not affiliated with the WAPP or with any platform vendor |

## 1. What the tool does

Each participant represents a market actor of a WAPP country (a utility, a producer, a distributor; several can share a country), submits sell and buy orders for every hour of the next day, and the trainer runs the clearing. The engine answers three questions, in order: **who trades** (the set of trades that creates the most value within line capacities), **how to break ties** between equivalent solutions (the most energy traded), **at what price** (one price per country and per hour, chosen within the complete set of prices consistent with the quantities). Every rule is written in a public document and checked by automated tests.

Three uses: **train** (a three-round market session, one country per participant), **study** (a public test case, written rules, an open engine), **compare** (replay a case, confront the results with another platform's, discuss tie-break rules before the market opens).

## 2. Functional scope

| Item | Content |
|---|---|
| Zones | 14 (NGA, BEN, TGO, GHA, CIV, BFA, MLI, SEN, GIN, SLE, LBR, GNB, GMB, NER) |
| Network | 15 interconnections, net transfer capacities (NTC) per direction, signed flows, zonal approach without flow-based constraints; interdependence constraint on the two lines into Burkina Faso (α = 0.7) |
| Horizon | day D+1 in 24 hourly steps, or any subset of hours (one-hour mode for training) |
| Orders | price-quantity segments (at most 4 per actor) with hourly profiles (solar, hydro, baseload, peaking, flat, custom); fill-or-kill blocks; linked blocks (child ⇒ parent); exclusive groups (at most one option); minimum income conditions (fixed term + variable term × volume) |
| Price bounds | 0 to 500 per MWh (model parameter); configurable currency label, no effect on the computation |
| Actors not played | three fill modes: background actors of the scenario (default), zones without submission, no filling |

## 3. Clearing rules

| Step | Question | Rule |
|---|---|---|
| P1 | Who trades? | welfare maximisation under the balance of each zone, flow bounds, the α constraint and block links; linear program, mixed-integer with blocks (gap 10⁻⁶) |
| P1bis | How to break ties? | maximum volume at the **exact** optimal welfare; then explicit sharing of equal-price orders: pro rata (default), submission order, or solver |
| P2 | At what price? | **complete** set of admissible prices (equilibrium conditions on accepted, partial and rejected orders, equal prices across unsaturated lines, inequality in the direction of saturation, α constraint, bounds); the price closest to the midpoint of the local admissible interval is chosen |
| Paradoxical blocks | | block accepted at a loss: rejected and the run repeated (EUPHEMIA rule, default); rejected block that would have been profitable: tolerated and reported; alternative rules available for comparison |
| Minimum income condition | | insufficient income: all the actor's orders withdrawn and the full sequence rerun |

Diagnostics published with every clearing: paradoxically rejected or accepted simple orders (expected 0), price gaps across unsaturated lines (expected 0), maximum deviation from the equilibrium conditions, tie-break mode, iterations, identity welfare = consumer surplus + producer surplus + congestion rent.

## 4. Inputs and outputs

| | |
|---|---|
| **Inputs** | order books per participant (web interface, REST API or CSV files); background scenario; exchange capacities editable per room; simulated hours; rules |
| **Outputs** | prices per zone and per hour; signed flows per line; dispatch per profile; result per actor (offered and accepted volume, average price, income or payment, surplus, rejected orders); breakdown per zone (surplus, net position, hours without trade); congestion rent and saturated hours per line; block and condition statuses; diagnostics; CSV and JSON exports |

## 5. Data provided

| Set | Content | Reliability |
|---|---|---|
| Reference 2024 (default) | available capacities, main plants and peak demands per country, line capacities, costs by technology, from public 2023-2025 sources | sourced for the capacities and several lines; **estimated** for several peaks and capacities (flagged); **assumed** for the order prices (typical variable cost) |
| Four teaching variants | hydro drought, Nigeria–Benin line out of service, expensive gas, high demand: one thing changes with respect to the base set | derived from the 2024 set |
| Test set | synthetic project data, regression values (welfare 22,317,910, volume 167,900 MWh) | tests only |

Prices produced on these data are simulation results, not observed prices: the WAPP day-ahead market has not started yet. Details and sources: `docs/REFERENCE_DATA.md`.

## 6. Technical architecture

| Layer | Technology |
|---|---|
| Engine | Python 3.10+, Pyomo models, open-source HiGHS solver included; Gurobi used automatically when installed |
| API | FastAPI, SQLAlchemy (SQLite by default, PostgreSQL possible), interactive documentation on `/docs`, real-time event stream (Server-Sent Events) |
| Interface | React, Vite, TypeScript, Tailwind; public page, hall, trading floor, trainer desk; bilingual FR/EN; Natural Earth maps (public domain) |
| Command line | `python -m engine.cli`: CSV in, JSON and prices CSV out |
| Historical application | Streamlit, kept for local training |

## 7. Performance

| Case | Time |
|---|---|
| Reference 2024, 24 h, 14 zones, 80 segments (3,000 continuous variables) | 0.4 s |
| 150 block orders with the paradoxical-block loop | ≈ 11 s |
| Training room of 20 participants | 2 vCPU and 4 GB are enough |

## 8. Quality and verification

- 66 automated tests run on every change (continuous integration): regression values, block and condition rules, API, command line.
- Random-case campaign (segments, simple, linked and exclusive blocks, conditions, every rule, 24 hours or one hour, reduced capacities) checked by a solver-independent verifier: prices within bounds, flows within capacities, hourly balance, net positions summing to zero, accepted ≤ offered, block rules, conditions satisfied or withdrawn, welfare identity.
- Reproduction in three commands (see `README.md`).

## 9. Deployment and operations

| | |
|---|---|
| **Image** | one Docker image (API + compiled interface), `Dockerfile.app` |
| **Hosting** | one-click Render deployment (`render.yaml`, persistent disk) or a virtual server with `docker-compose.yml` and automatic HTTPS (Caddy); a local workstation or an offline training network also work |
| **Access** | no accounts: a room has a six-character code, each participant a token; no personal data beyond the organisation name entered |
| **Safeguards** | purge of inactive rooms (30 days), creation quota per address (20 per day), configurable allowed origins |
| **Data** | local SQLite database or persistent volume; scripted backups; no WAPP operational data |

## 10. Limitations

Not modelled: losses, reserves, ramps and minimum running times, flow-based constraints, intraday auctions, financial settlement, rounding of published prices, buy-side minimum income conditions. 2024 data to be validated with the WAPP coordination centre and the utilities (peaks, exchange capacities, costs).

## 11. Roadmap

| Date | Step |
|---|---|
| October 2026 | online under a domain name, GitHub organisation, data validation with SENELEC |
| Mid-November 2026 | technical note (working paper) and public test cases; comparison campaign proposed to the coordination centre |
| December 2026 | first training session on the online site |
| 1 January 2027 | planned launch of the WAPP day-ahead market |

## 12. Suggested citation

Plakoo K., Patanè E. (2026). *WAPP DAM Simulator: an open reference implementation of day-ahead zonal market coupling for the West African Power Pool*, version 2.0. https://github.com/aymardino/wapp-dam-simulator
