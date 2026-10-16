# WAPP DAM Simulator — motion design video

A silent explainer of about 78 seconds for the home page of the website (wapp-dam-simulator.mastereose.fr), in French
and English, 1920 × 1080, 30 fps. It tells, in nine scenes, what the simulator computes: fourteen countries, one
market, the price where supply meets demand, the lines that split prices when they are full, the three questions the
engine answers, a whole simulated day, what the tool is for.

The video is written in HTML and rendered with [HyperFrames](https://github.com/heygen-com/hyperframes) (Apache 2.0).
Every figure comes from the engine (`npm run data` reruns the website's demonstration day). The text lives in
`assets/strings.js`, the look in `assets/theme.css`, the shared helpers in `assets/wapp.js`.

## Video direction

- **Tone.** Institutional, calm, precise: the website in motion, not an advert. One idea per scene, short copy.
- **Look.** The website's design system (`assets/theme.css`): deep green grounds with the topographic "power lines",
  the brand green with its mesh, the light page colour; Roboto bold titles with the short amber rule; JetBrains Mono
  for figures, hours and codes; amber for the price and the current hour, mint for flows, coral for a full line.
- **Signature motif: lines of current.** Strokes that draw themselves, flows as dashes running along a line, the
  amber rule under each title, the amber line that sweeps across the screen between scenes (WAPP.wipeIn).
- **Motion.** Confident ease-out entrances (`power3.out`, 0.6–0.9 s), staggers of 0.06–0.15 s, small `back.out(1.6)`
  only on dots and nodes. No bounce, no elastic, no glitch, no 3D flip, no blur, no shake. A slow camera drift runs
  underneath every scene (a content group scaling 1 → 1.03 or drifting 20–30 px, `sine.inOut`), so no frame is frozen.
- **Pacing.** Every line must be readable: on screen at least 2.5 s plus 0.3 s per word before the scene ends. Reveal
  across the whole scene, on the beat, never everything at once. Each scene must be complete at `duration − 1.0 s`:
  the next scene wipes over its last 0.7 s.
- **Transitions.** Every scene but the first starts with `WAPP.wipeIn(tl, "#sNN-frame", "#sNN-sweep", 0)` (0.7 s);
  its own entrances start from 0.35 s. No exit animation in any scene: the next wipe is the exit. The last scene
  holds its final lockup to the end (the player shows the last frame when the video stops).
- **Layout.** Safe area 128 px left/right, 96 px top/bottom; nothing important under y = 980 (the player's
  controls). As on the website: text column on the left, visual on the right, unless the scene says otherwise. No text
  under 26 px. Both languages must fit: test French and English.
- **Truth.** Prices are simulated: scenes 04, 05 and 07 show the badge `t("badge")` ("Simulation · données 2024
  reconstituées"). No claim beyond the strings file. Real figures only, from `WAPP.data`.

## Technical contract for a scene

- File `compositions/<id>.html`: one bare `<template>…</template>` fragment, everything inside it (`<style>`,
  markup, `<script>`). Root `<div id="root" data-composition-id="<id>" data-width="1920" data-height="1080"
  data-duration="<duration>">`, styled only through `#root`. Duration fixed below: never change it.
- Skeleton (see `assets/theme.css`): a timed layer `<div id="sNN-stage" class="clip wapp-stage" data-start="0"
  data-duration="<duration>" data-track-index="0">` holding `<div id="sNN-frame" class="wapp-frame wapp-bg-…">` (the
  ground and all content) and `<div id="sNN-sweep" class="wapp-sweep"></div>`. Never animate the `.clip` element;
  animate its children.
- One `gsap.timeline({ paused: true })`, built synchronously inside an IIFE, registered last:
  `window.__timelines["<id>"] = tl`. `fromTo` for every entrance (never CSS-hidden start states, never `from`). No CSS
  transitions or animations, no `Date.now`, no `Math.random`, no network. `repeat: -1` is allowed only for a
  continuous loop such as flow dashes; prefer a finite tween over the scene.
- Never put a CSS `transform` on an element that GSAP moves (`x`, `y`, `scale`, `rotation`): centre with flex or
  margins. Transformed elements must be block-level and sized.
- Prefix every id and every scene-specific class with `sNN-` (`s04-axis`, `.s04-step`): the nine scenes share one page.
- No font-family in the scene: use `var(--font)` / `var(--mono)` or the classes `wapp-mono`, `wapp-figure`. Only the
  latin subset of Roboto and JetBrains Mono is shipped: no →, ≈, ≤ or emoji in text; draw arrows in SVG.
- Text only through `WAPP.t("key", values)` from `assets/strings.js` (fill elements from the script with
  `textContent`). A scene may add a few labels of its own (axis units, codes) in a local `{ fr, en }` object, chosen
  with `WAPP.lang`; no sentence of its own.
- Helpers (`assets/wapp.js`): `WAPP.wipeIn`, `WAPP.rise(tl, sel, at, {y, duration, stagger})`,
  `WAPP.rule(tl, sel, at)`, `WAPP.draw(tl, sel, at, {duration, stagger})` (DrawSVG), `WAPP.countUp(tl, el, to, at,
  {format, duration, from})`, `WAPP.buildMap(svg, prefix, {hour, neutral, showPrices})` → `{ setHour(h), dash(tl,
  from, to), nodeEls, lineEls }`, `WAPP.num`, `WAPP.money`, `WAPP.hour`, `WAPP.hh`, `WAPP.zoneName`,
  `WAPP.priceColor`. GSAP plugins loaded: SplitText, DrawSVGPlugin, MotionPathPlugin, CustomEase.
- Test alone, in both languages: `node scripts/scene-test.mjs <id> --lang fr --at 0.5,2,4,… --check` then
  `--lang en`, and look at every still.

## Scenes

Times are scene-local seconds. Start → end in the film: see `index.html`.

### 01-intro · 6.0 s · ground deep · the logo assembles

Purpose: open on the brand, with the idea of the market already inside it: the website's logo is a supply curve
(a staircase), a dashed price line and an amber dot where they meet.

Mark geometry (viewBox 0 0 64 64, from `assets/site/mark-light.svg`): white tile `rect 64×64 rx 14`; staircase
`M12 46 H22 V36 H32 V26 H42 V16 H52` (stroke #0B3D30, width 4, round caps and joins); dashed line `M12 31 H52`
(stroke #0F6E56, width 2, dash 3 3); dot `circle cx 37 cy 31 r 5` (fill #F2B134, stroke #0B3D30, width 2).

- 0.0–0.3: the deep ground alone; the ground (or a pattern layer) settles slowly from scale 1.06 to 1 over the scene.
- 0.2–1.6: the staircase draws itself, very large (about 520 px wide) and centred, white stroke on the dark ground.
- 1.2–1.9: the dashed price line draws across it, mint.
- 1.7–2.2: the amber dot pops where they cross (`back.out(1.6)`), with one soft glow ring that expands and fades.
- 2.4–3.3: the mark shrinks and travels left into the lockup position while the white rounded tile grows behind it;
  the strokes turn to the logo colours (#0B3D30, #0F6E56) as the tile appears. The lockup sits centred as a whole
  (tile about 150 px, wordmark to its right).
- 2.9–3.6: `s01.kicker` above the wordmark, then `s01.wordmark` (display size) revealed letter by letter or by a
  left-to-right mask.
- 3.6–4.4: `s01.tagline` (lead) rises under the wordmark; the amber rule draws under it.
- 4.4–6.0: hold, the camera drift only.

### 02-region · 9.0 s · ground deep · fourteen countries, fifteen lines

Purpose: place the market on the map: who is in it, how they are connected, when it is due.

Data: `WAPP.buildMap(svg, "s02m", { neutral: true })` (no price, uniform nodes); the map large on the right
(about 1250–1350 px wide, class `wapp-map-fade`), the text column on the left.

- 0.35: `s02.kicker` rises.
- 0.6–2.6: the land appears: member countries' borders draw themselves (stagger) while their fill fades in; the other
  countries fade in faintly.
- 1.6–3.2: a big mono figure counts 0 → 14 with the label `s02.countries`, while the fourteen nodes pop in one by one.
- 3.4–5.0: a second figure counts 0 → 15 with `s02.lines`, while the fifteen lines draw themselves between nodes.
- 5.4–6.2: `s02.title` (h2 size) rises under the figures, then its rule draws.
- 5.8–9.0: the flow dashes start running along the lines (`dash`); a slow push-in on the map (scale 1 → 1.04).

### 03-question · 7.0 s · ground brand · the question of every day

Purpose: the day-ahead market in one sentence and three questions.

- 0.4: `s03.line1` (h2 size, brand-ink) rises.
- 1.0: `s03.line2` rises; under it, a strip of 24 thin bars (the 24 hours, like the website's hour strip, mint, same
  height) draws in from left to right (stagger 0.03).
- 2.3: `s03.q1` (display size, white) rises word by word.
- 3.2: `s03.q2`, same.
- 4.1: `s03.q3`, same, in amber, with the rule drawing under it.
- 4.8–7.0: hold; one bar of the strip lights amber and the highlight travels slowly along the 24 bars (the hours of
  tomorrow), the camera drift.

### 04-curves · 12.5 s · ground light · supply meets demand

Purpose: the core idea: plants sorted from cheapest to most expensive, buyers from highest bid to lowest, the price
where they meet. Real case: `WAPP.data.cross` — Senegal at 19 h, 155 $/MWh, set by the last plant called.

Data: `cross.supply` (price ascending) and `cross.demand` (price descending) as `{actor, price, qty}` in MW;
`cross.price`, `cross.prod` (MW produced), `cross.cons` (MW consumed), `cross.marginal` (actor name), `cross.zone`,
`cross.hour`. Chart: x in MW from 0 to a round value above the larger total × 1.08; y from 0 to 500 $/MWh (the
market's price bounds, as on the website); supply in `--accent`, demand in `--demand`.

Layout: text column on the left (`s04.kicker` = `t("s04.kicker", { zone: WAPP.zoneName(cross.zone), hour:
WAPP.hour(cross.hour) })`, then the three lines appearing in turn, each with a short colour swatch); a large white
chart card on the right (about 1050 × 760) with its axes, mono ticks, the units `s04.axisQ` / `s04.axisP`, the badge.

- 0.35: kicker; the card rises; its axes draw (0.6–1.3).
- 1.4: `s04.supply` (green swatch) rises in the text column.
- 1.7–4.6: the supply staircase builds step by step: each plant arrives at its price and its quantity (a short green
  segment sliding into place, or the outline drawing step by step), in price order, so that the staircase climbs.
- 5.0: `s04.demand` (red swatch) rises; 5.2–6.6: the demand staircase draws from the top left, descending.
- 7.0: `s04.meet` rises; the amber dot pops where the curves cross (x = `cross.cons`, where the demand riser meets
  the supply step at the price; y = `cross.price`), a dashed
  price line draws across the chart, and the price label `t("s04.price", { p: … })` (large, mono) appears beside it.
- 8.4: under the price label: `s04.marginal` and the actor name (`cross.marginal`); the marginal step of the supply
  curve (the plant at the price) gets an amber outline.
- 9.2–10.0: the parts of both curves beyond the crossing (not served) fade to 30 % opacity, as on the website.
- 10.0–12.5: hold.

### 05-network · 11.5 s · ground deep · a line fills up, prices split

Purpose: why prices differ between countries: a line between two countries carries energy until it is full; then
each side keeps its own price. Real case: `WAPP.data.congestion` — Nigeria → Benin, 200 MW of capacity; at 18 h the
line carries 157 MW and both sides pay 120 $/MWh; at 22 h it is full (200 MW) and the prices split: 42 $/MWh in
Nigeria, 95 in Benin.

Data: `congestion.from` (NGA), `.to` (BEN), `.cap`, `.free = {h, f, pu, pv}`, `.full = {h, f, pu, pv}` (`pu` is
the price of `from`, `pv` of `to`).

Layout: a schematic, not the map: Benin on the left, Nigeria on the right (their geography), two large country nodes
(about 220 px circles, coloured with `WAPP.priceColor`, code and price in them, the country name under each), joined
by a thick line drawn as a capacity gauge: a track for the 200 MW and a fill for the flow, with dashes running inside
from Nigeria to Benin; the flow label `s05.flow` (mono) and `s05.capacity` above the line; an hour pill above
(`WAPP.hour(h)`); the caption line under the schematic; the badge.

- 0.35: `s05.kicker`; 0.6–1.6: the two nodes pop, the names rise, the track draws between them.
- 1.8: the hour pill shows `free.h` (18 h).
- 2.0–3.4: the fill grows to `free.f / cap` with the dashes running; both prices count up to 120; same colour.
- 3.6: `s05.free` rises as the caption.
- 5.6: the hour pill flips to `full.h` (22 h).
- 5.8–7.0: the fill grows to 100 %; the line turns coral; the capacity mark at the end of the track flashes once.
- 7.0–8.0: the prices split: Nigeria counts down to 42, Benin to 95, their colours move apart.
- 8.0: the caption swaps to `s05.full` (the old line slides up and fades, the new one rises: a swap inside the scene,
  not an exit).
- 8.4–11.5: hold with the dashes running.

### 06-engine · 11.5 s · ground brand · three questions, in order

Purpose: what the engine computes, in the order the market rules set: who is served (value), how much (volume),
at what price (the middle of the possible prices).

Layout: as the website's "Le calcul" section: `s06.kicker`, `s06.title` and the rule top left; under them three
cards in a row across the width, each with a large amber numeral (1, 2, 3), a mono tag (P1, P1bis, P2), the question
(`s06.q1`…, h2 size) and the answer (`s06.a1`…, body size), and a small diagram at the bottom of the card;
`s06.foot` (mono, small) under the cards.

- 0.35–1.6: kicker, title, rule.
- 1.8: card 1 rises; its numeral and tag pop; question, then answer; its diagram: a bar of value that fills.
- 4.4: card 2, same; its diagram: a bar of energy that fills, beside a ghost bar of the same value.
- 7.0: card 3, same; its diagram: the price interval of the website — a horizontal segment with end marks labelled
  `s06.low` and `s06.high`; the amber dot travels from the low end and settles in the middle, labelled `s06.mid`.
- 9.2: `s06.foot` fades in.
- 9.6–11.5: hold.

### 07-day · 10.5 s · ground deep · a whole simulated day

Purpose: the payoff: the full network over a day, prices and flows changing hour by hour, and the figures of the day.

Data: `WAPP.buildMap(svg, "s07m", { hour: 0 })`, `setHour(h)` for each hour, `dash(tl, from, to)`; the figures
`WAPP.data.day`: `welfare` (`WAPP.money`), `volume` (MWh), `saturatedLines` / `lines`.

Layout: the map large on the right (about 1250 px wide, class `wapp-map-fade`); the text column on the left:
`s07.kicker`, `s07.title`, the rule, a big mono hour readout (`WAPP.hh(h)`, amber) with a strip of 24 bars under it
(the mean price of each hour, highlight on the current hour), then the three figures stacked (mono, `--fs-h2` or
larger) with their labels (`s07.welfare`, `s07.volume`, `s07.saturated`); the legend (`s07.flow`, `s07.full`) and the
badge under the map.

- 0.35: kicker, title, rule (0.35–1.3).
- 0.6–1.8: the map: land fades in, lines draw, nodes pop (quicker than scene 02: this is the recap).
- 1.8–8.2: the hours run from H00 to H19 (about 0.33 s per hour): nodes, prices, line widths, coral full lines and
  the hour readout and strip update together (an hour counter tweened with `ease: "none"`, `setHour(Math.floor(h))`
  in `onUpdate`); the dashes run throughout.
- 2.4 / 3.4 / 4.4: the three figures count up, one after the other.
- 8.2–10.5: hold on H19 (the evening peak, the hour of scene 04).

### 08-uses · 7.5 s · ground light · what it is for

Purpose: the people: training sessions, study, comparison before the market opens.

Layout: on the right, the photo `assets/site/photos/solar-technicians.jpg` (CC0) in a tall rounded frame (about
720 × 860), settling from a slow zoom (scale 1.08 → 1 over the scene), the credit `s08.credit` small at its bottom
right (white on a dark translucent pill); on the left, `s08.title` with its rule, then the three uses stacked, each
with a mono number (01, 02, 03, accent green), the word (`s08.k1`…, h2 size) and its line (`s08.v1`…, body size), a
thin rule above each.

- 0.35: the photo frame reveals (it grows from the bottom edge, or settles from the zoom); the title rises (0.5),
  its rule draws.
- 1.6 / 2.6 / 3.6: the three uses, one after the other (rule draws, number and word rise, then the line).
- 4.6–7.5: hold, the photo still settling.

### 09-outro · 8.0 s · ground deep · the lockup

Purpose: where to find it, who made it, under what terms.

Layout, centred: the logo tile and `s09.wordmark` (the same lockup as the end of scene 01), `s09.url` in mono amber
under it, a pill `s09.open`; lower: `s09.authors` (white, bold) and `s09.frame` (brand-ink); a white rounded band with
the three partner logos (`assets/site/partners/mines-paris-psl.png`, `ms-ose.png`, `senelec.png`, which are blue and
need the white band); at the bottom, `s09.disclaimer` in small text.

- 0.35–1.4: the mark redraws quickly in its tile (the staircase, the dashed line, the dot), the wordmark reveals.
- 1.6: the URL reveals left to right (mask), 2.4: the pill rises.
- 3.2: authors, then the frame line.
- 4.0: the white band with the logos rises.
- 4.8: the disclaimer fades in.
- 5.4–8.0: hold; no fade-out (the last frame stays on screen).
