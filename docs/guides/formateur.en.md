# Trainer guide

This guide walks through a training session and explains every setting. The trainer desk opens when you create a room from the hall; the six-character code in the header is what participants need.

## 1. Before the session

1. **Create the room** (training name, your name). The browser that creates the room becomes the trainer desk: do not lend it during the session.
2. **Pick the horizon**: 24 hours for a full day, or a single hour (for instance 19:00, the peak) for a quick round.
3. **Pick the scenario**: it provides the background data (plants, demands, line capacities). "Reference (Livrable 2)" and "Reference 2024 (public sources)" describe a normal network; "Hydro drought", "Nigeria–Benin line out of service", "Expensive gas" and "High demand" are for later rounds.
4. **Pick the fill mode**, which decides what happens to actors nobody plays (see §4).
5. **Check line capacities (NTC)** if you want to create or remove a congestion.
6. **Share the code** and let participants in.

## 2. A typical two-hour session

| Time | Round | Teaching goal |
|-----:|-------|---------------|
| 0:00 | Participants join, map and rules presented | vocabulary: offer, bid, zonal price, NTC |
| 0:15 | Round 1: stepwise orders, reference scenario, 24 h | merit order, uniform price, partial acceptance |
| 0:45 | Round 2: same actors plus fill-or-kill blocks | blocks accepted or rejected as a whole, paradoxical rejections |
| 1:15 | Round 3: "Hydro drought" or "Nigeria–Benin line out of service" | congestion, price divergence, congestion rent |
| 1:45 | Debrief on the results page and individual results | reading the checks, discussing strategies |

Between rounds: "Reopen submission", change the scenario or NTC, and ask participants to revise their orders. Every clearing is kept in the history.

## 3. During a round

- The **Participants** panel shows who is in and how many orders each has submitted. The header shows "Live": everything updates without reloading.
- **Close submission** once everyone has submitted, then **Run clearing**. It takes under a second; a few seconds with many blocks.
- **Results** open on the map (price per country at the chosen hour, flow per line, congested lines in red), then the Prices, Dispatch and Flows tabs and the table by zone.
- Green badges are the **checks**: no paradoxically rejected order, no price gap without congestion, exact tie-break. An orange badge flags a tolerated paradoxically rejected block or a minimum income condition that withdrew an actor.
- A participant can be **removed** through the API (inappropriate name, duplicate); their orders are deleted.

## 4. Settings explained

**Fill mode.** Participants never play all actors of fourteen countries. Three behaviours:
- *Background actors* (recommended): every actor of the scenario stays in the market except those a participant replaces. A participant replaces the actors of **their zone** whose name matches theirs ("SENELEC" replaces "SENELEC Thermal" and "SENELEC Demand") or the name of one of their orders (an order named "Egbin Gas" replaces the reference Egbin Gas plant). A free name such as "Team 1" replaces nothing: its orders are added to the market. Pick a suggested name to step into a real actor's shoes.
- *Zones without submission*: a zone where at least one participant submitted contains **only** participants' orders; other zones are filled from the scenario. Useful when a country is played entirely by its traders.
- *None*: only participants' orders count; the clearing is refused if there are none.

**Pricing rule.** *Complete P2* (recommended) selects, among all prices consistent with accepted quantities (accepted and rejected orders, congested or free lines), the one closest to the middle of the admissible interval. *Livrable 2 P2* reproduces the project's initial rule, which ignored rejected orders and price equality on uncongested lines; use it only to show the difference.

**Paradoxical blocks.** *EUPHEMIA* (recommended) iteratively rejects blocks accepted at a loss and tolerates blocks rejected although profitable. *Livrable 2* additionally forces the latter's acceptance when feasible. *Detection only* applies no correction.

**Equal-price sharing.** When several orders at the same price cannot all be served: *pro rata* of quantities (recommended), *submission order*, or *left to the solver*.

**Currency.** A display label only.

**Capacities (NTC).** Scenario values, editable line by line; "Reset" restores the scenario values.

## 5. Reading results

- **Welfare**: value created by trade, the sum of buyers' surplus, sellers' surplus and congestion rent.
- **Volume**: energy traded over the period.
- **Zonal prices**: an importing country behind saturated lines is priced above its neighbours; without congestion prices are equal.
- **Net position**: positive for an exporter, negative for an importer.
- **Surplus by zone**: what the country's actors gain relative to their offer prices.
- **Exports**: prices as CSV, full result as JSON.

## 6. Frequently asked

- *Welfare is 22 million although nobody submitted.* That is the fill mode: the market ran on scenario data. The "Demonstration" banner says so.
- *A trader can no longer edit orders.* Submission is closed; reopen it.
- *I want to test as a trader from my desk.* Use "Enter the floor as a trader"; both identities stay reachable from the hall.
- *The run is refused.* The message gives the reason: order out of bounds, no order with fill disabled.
