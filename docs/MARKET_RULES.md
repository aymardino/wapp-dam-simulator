# Market rules applied by the engine

*Reference document for the technical note and for any comparison with another clearing platform. Every rule below is implemented in `engine/clearing.py` and checked by `tests/test_engine.py`. Version of 3 October 2026. Version française : [fr/REGLES_DE_MARCHE.md](fr/REGLES_DE_MARCHE.md).*

This document states every rule the clearing engine applies: inputs, order types, the three sequential problems (welfare maximisation, volume tie-break, pricing), the complete characterisation of admissible prices, the treatment of paradoxical blocks, the minimum income condition, tolerances, and what is deliberately not modelled. It is the counterpart of the formulation in Deliverable 2 of the project and is meant to be testable: the public test cases in `tests/` give expected outcomes for each rule.

---

## 1. Scope

- 14 market zones (WAPP countries), 15 interconnections, zonal approach with net transfer capacities (NTC), no flow-based.
- Horizon: day D+1, 24 hourly steps, or any subset of hours (1-hour mode for training).
- An order applies to every simulated hour; the effective quantity of an hour is the submitted quantity multiplied by the hourly profile (generation) or by the West African load profile (demand), rounded to the MW.
- Bounded prices: 0 and 500 per MWh (configurable currency label, no effect on the computation).
- Actors not played: three fill modes. `actors` (room default) keeps every actor of the scenario except those of a participant's zone whose normalised name matches the participant's name or one of its orders (same first word, or one name contained in the other; the words "demand", "gen", "réseau", "distribution", "thermal", "hydro", "solar" are ignored); `zones` fills only zones without any order; `none` fills nothing.
- Interdependence constraint: flow GHA→BFA + flow CIV→BFA ≤ α × (NTC GHA-BFA + NTC CIV-BFA), α = 0.7.

## 2. Order types

| Type | Variable | Acceptance | Effect on the price |
|------|----------|------------|---------------------|
| Sell or buy segment (stepwise, at most 4 segments per actor) | x ∈ [0, 1] | partial acceptance possible | can be marginal (sets the price) |
| Simple block (fill-or-kill) | y ∈ {0, 1} | in full over all its hours, or not at all | never sets the price |
| Linked block | y_child ≤ y_parent | the child requires the parent | idem |
| Exclusive group | Σ y ≤ 1 | at most one option | idem |

A block's parent and its exclusive group are identified by name within the same trader and the same zone.

## 3. The three problems, in order

### P1 — Who trades? (welfare)

Maximise the value created: sum over hours of (prices of accepted buys × quantities) minus (prices of accepted sells × quantities), blocks included, under the balance of each zone at each hour (generation + net imports = consumption), the flow bounds, the α constraint and the block linking constraints. Linear program without blocks, mixed-integer linear program with blocks (relative gap 10⁻⁶).

### P1bis — How to break ties? (volume)

Among the welfare-optimal solutions, maximise the accepted volume (sells + buys). Block decisions are fixed to those of P1. **Welfare is constrained to its exact optimal value** (W ≥ W*), not to W* − 0.01 as in Deliverable 2: an absolute tolerance was entirely consumed by the volume maximisation and produced a solution that no price supported any more. If the solver finds no solution (numerical case), the P1 solution is kept and the `tie_break` diagnostic says so.

This tie-break does not settle every tie: two orders at the same price in the same zone can still be shared in several ways without changing welfare or volume. An **explicit sharing rule** is therefore applied next, per partially accepted (zone, hour, side, price) group: `prorata` (default, each order of the group is accepted in the same proportion of its quantity), `order` (submission order, first come first served) or `solver` (allocation left to the solver). The group's accepted total is unchanged: neither welfare, nor volume, nor the set of admissible prices moves.

### P2 — At what price? (zonal prices)

**Set of admissible prices** (Karush-Kuhn-Tucker conditions of P1, with block decisions fixed), for each zone z and each hour h:

1. sell accepted in full ⇒ π ≥ order price;
2. sell partially accepted ⇒ π = order price;
3. sell rejected ⇒ π ≤ order price;
4. buy accepted in full ⇒ π ≤ order price;
5. buy partially accepted ⇒ π = order price;
6. buy rejected ⇒ π ≥ order price;
7. line u→v not saturated ⇒ π_v = π_u;
8. line saturated in direction u→v ⇒ π_v ≥ π_u, and conversely;
9. when the α constraint is active, the two lines towards BFA share the same price supplement λ ≥ 0;
10. regulatory bounds 0 ≤ π ≤ 500.

Rules 3, 6, 7 and 9 are the v2 additions to constraints (8)-(12) of Deliverable 2; without them, the engine produced paradoxically rejected simple orders and price gaps between uncongested zones.

**Selection within the admissible set**: the chosen price minimises the sum of absolute deviations from the reference price, where the reference price is the midpoint of the local admissible interval [lower bound, upper bound], with lower bound = max(prices of accepted sells, prices of rejected buys, 0) and upper bound = min(prices of accepted buys, prices of rejected sells, 500). When the price is unique (the general case), the rule has no effect; it only settles indeterminate cases, and in a zone without trade it places the price halfway between the best rejected bid and the best rejected offer.

Mode `pricing = 'l2'` reproduces the Deliverable 2 rule exactly, for comparison purposes.

## 4. Paradoxical blocks

After P2, the surplus of each block is computed at final prices: Σ_h (π_h − p) × q for a sell, Σ_h (p − π_h) × q for a buy.

- **PAB** (block accepted at a loss, surplus < 0): forbidden. Rule `euphemia` (default): the block is fixed to "rejected" and the P1 → P1bis → P2 sequence is rerun until no PAB remains (at most one block fixed per iteration, hence at most as many iterations as blocks; configurable cap).
- **PRB** (rejected block that would have a surplus > 0): tolerated and reported, as in EUPHEMIA. Rejecting it was optimal for total welfare: accepting it would have moved the prices.
- Rule `l2`: in addition, PRBs are fixed to "accepted" (Deliverable 2 §3.3). A block forced this way that becomes a PAB at the new prices is finally rejected: the "no PAB" rule prevails, and each block changes state at most twice, which guarantees termination. Rule `none`: detection only.

## 5. Minimum Income Condition (MIC)

A selling actor can attach a minimum income condition to its orders: a fixed term F and a variable term V per MWh. After P2, its income at final prices (segments and blocks bearing its name) is compared with F + V × accepted volume. If it is lower (within MIC_TOL) and some volume was accepted, **all its orders are withdrawn** (its blocks, and the child blocks that depend on them) and the P1 → P1bis → P2 sequence, PAB loop included, is rerun without it. An actor with nothing accepted trivially satisfies its condition. The loop stops when every remaining condition is satisfied; at most one iteration per condition. Published prices are those of the last run. The "income − cost ≥ F" formulation of Deliverable 2 §6.3 is obtained by setting V equal to the actor's variable cost.

## 6. Tolerances

| Quantity | Value | Role |
|----------|-------|------|
| X_TOL | 10⁻⁴ | a ratio x < X_TOL is "rejected", x > 1 − X_TOL "accepted in full", in between "partial" |
| F_TOL | 10⁻³ MW | a line is saturated when the flow is within F_TOL of its bound |
| PRICE_TOL | 0.5 per MWh | tolerance of the diagnostics (paradoxical orders, price gaps) |
| MIC_TOL | 0.5 (currency) | tolerance of the minimum income condition |
| MILP gap | 10⁻⁶ relative | optimality of the problems with blocks |
| rounding of hourly quantities | 1 MW | effective quantity = round(q × profile) |

## 7. Outputs and checks

For each clearing, the engine publishes: prices per zone and per hour, signed flows per line, dispatch per profile, results per actor (offered and accepted volume, average price, income or payment, surplus, rejected orders), breakdown per zone (consumer surplus, producer surplus, net position, hours without trade), congestion rent and saturated hours per line, status of each block, state of each MIC (income, required income, satisfied or withdrawn), and **diagnostics**: number of paradoxically rejected or accepted simple orders (expected: 0), number of unsaturated lines with different prices (expected: 0), maximum deviation from the equilibrium conditions, tie-break mode, PAB iterations, and the identity welfare = consumer surplus + producer surplus + congestion rent. `engine/checks.py` verifies these properties independently of the solver and is used by the random-case campaign (`tests/test_properties.py`).

## 8. What is not modelled

Losses, reserves, ramps, minimum running times, intraday auctions, financial settlement, flow-based, interpolated supply curves (segments are steps), final rounding of published prices, buy-side MIC.
