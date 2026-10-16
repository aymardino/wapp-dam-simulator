// Builds assets/data.js, the data the video draws: the network map (same projection and node offsets as the website's
// NetworkMap, at twice its size), the engine's demonstration day (assets/demo.json, from scripts/export_demo.py) and
// three worked examples picked from that day: a supply / demand cross in one country, a line that fills up between two
// countries, and the figures of the day. Deterministic: same demo.json, same data.js.
import { readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { geoMercator, geoPath } from 'd3-geo'

const here = dirname(fileURLToPath(import.meta.url))
const root = join(here, '..')
const geo = JSON.parse(readFileSync(join(root, '..', 'web', 'src', 'data', 'west_africa.geo.json'), 'utf8'))
const demo = JSON.parse(readFileSync(join(root, 'assets', 'demo.json'), 'utf8'))

/* ── Map (web/src/components/NetworkMap.tsx, scaled ×2) ─────────────────────── */
const K = 2, W = 560 * K, H = 340 * K
const NODES = { SEN: [-14.9, 14.7], GMB: [-15.6, 13.45], GNB: [-15.1, 12.0], GIN: [-11.4, 10.5], SLE: [-11.8, 8.5], LBR: [-9.5, 6.6], MLI: [-4.6, 14.5], BFA: [-1.6, 12.3], NER: [6.0, 15.6], CIV: [-5.6, 7.4], GHA: [-1.2, 7.9], TGO: [1.0, 8.6], BEN: [2.3, 9.5], NGA: [8.0, 9.1] }
const LINES = [['NGA', 'BEN'], ['NGA', 'NER'], ['BEN', 'TGO'], ['TGO', 'GHA'], ['GHA', 'CIV'], ['GHA', 'BFA'], ['CIV', 'BFA'], ['CIV', 'MLI'], ['CIV', 'LBR'], ['LBR', 'SLE'], ['SLE', 'GIN'], ['GIN', 'GNB'], ['GNB', 'GMB'], ['GMB', 'SEN'], ['SEN', 'MLI']]
const OFFSET = { GMB: [-30, 2], GNB: [-24, 24], TGO: [-4, 34], BEN: [14, 40], SLE: [-16, 8], LBR: [-8, 18] }
const EXTENT = { type: 'Polygon', coordinates: [[[-18.5, 3.5], [-18.5, 24.5], [16.5, 24.5], [16.5, 3.5], [-18.5, 3.5]]] }
const projection = geoMercator().fitExtent([[6 * K, 6 * K], [W - 6 * K, H - 30 * K]], EXTENT)
const path = geoPath(projection)
const r1 = v => Math.round(v * 10) / 10
const countries = geo.features.map(f => ({ id: String(f.id), member: !!f.properties.member, d: (path(f) || '').replace(/\d+\.\d+/g, m => String(r1(+m))) }))
const nodes = {}, anchors = {}
for (const [z, ll] of Object.entries(NODES)) {
  const [x, y] = projection(ll); anchors[z] = [r1(x), r1(y)]
  const o = OFFSET[z] || [0, 0]; nodes[z] = [r1(x + o[0] * K), r1(y + o[1] * K)]
}
const map = { width: W, height: H, nodeRadius: 14 * K, countries, nodes, anchors, lines: LINES.map(([u, v]) => `${u}->${v}`) }

/* ── Supply / demand in one country (web/src/pages/Landing.tsx, zoneCurves) ─── */
const pyRound = x => { const r = Math.round(x); return Math.abs(x - Math.trunc(x)) === 0.5 && r % 2 !== 0 ? r - 1 : r }
function zoneCurves(zone, h) {
  const prof = name => demo.profiles[name || 'baseload'] || demo.profiles.flat || Array(24).fill(1)
  const sup = demo.supply.filter(r => r.zone === zone).map(r => ({ actor: r.actor, price: r.price, qty: pyRound(r.quantity * prof(r.profile)[h]) })).filter(r => r.qty > 0).sort((a, b) => a.price - b.price)
  const dem = demo.demand.filter(r => r.zone === zone).map(r => ({ actor: r.actor, price: r.price, qty: pyRound(r.quantity * demo.load[h]) })).filter(r => r.qty > 0).sort((a, b) => b.price - a.price)
  const price = demo.prices[zone][String(h)]
  let net = 0
  for (const key of Object.keys(demo.ntc)) {
    const [u, v] = key.split('->'); if (u !== zone && v !== zone) continue
    const f = demo.flows[key]?.[String(h)] ?? 0; net += u === zone ? f : -f
  }
  const sum = (rows, keep) => rows.filter(keep).reduce((a, r) => a + r.qty, 0)
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v))
  const sLt = sum(sup, r => r.price < price - 0.5), sEq = sum(sup, r => Math.abs(r.price - price) <= 0.5)
  const dGt = sum(dem, r => r.price > price + 0.5), dEq = sum(dem, r => Math.abs(r.price - price) <= 0.5)
  let prod, cons
  if (sEq > 0 && dEq === 0) { cons = dGt; prod = clamp(cons + net, sLt, sLt + sEq) }
  else if (dEq > 0 && sEq === 0) { prod = sLt; cons = clamp(prod - net, dGt, dGt + dEq) }
  else if (sEq === 0) { prod = sLt; cons = dGt }
  else { cons = clamp(sLt + sEq - net, dGt, dGt + dEq); prod = clamp(cons + net, sLt, sLt + sEq) }
  const marginal = sup.find(r => Math.abs(r.price - price) <= 0.5)
  return { zone, hour: h, price, net: Math.round(net), prod: Math.round(prod), cons: Math.round(cons), marginal: marginal ? marginal.actor : null, supply: sup, demand: dem }
}
// A country and an hour where a local plant sets the price, the country trades little and the curves have a readable
// number of steps: the cleanest picture of "the price is where supply meets demand".
const candidates = []
for (const zone of Object.keys(NODES)) for (const h of demo.hours) {
  const c = zoneCurves(zone, h)
  if (!c.marginal || c.supply.length < 5 || c.supply.length > 12 || c.demand.length < 2 || c.price < 20) continue
  candidates.push({ c, score: Math.abs(c.net) / Math.max(1, c.cons) + (zone === 'SEN' ? -0.2 : 0) + (h >= 18 && h <= 21 ? -0.1 : 0) })
}
candidates.sort((a, b) => a.score - b.score)
const cross = candidates[0].c

/* ── A line that fills up (same two countries, two hours) ───────────────────── */
let congestion = null
for (const key of map.lines) {
  const [u, v] = key.split('->'); const cap = demo.ntc[key]
  const hrs = demo.hours.map(h => ({ h, f: demo.flows[key][String(h)], pu: demo.prices[u][String(h)], pv: demo.prices[v][String(h)] }))
  // free: the line carries a good share of its capacity but is not full, and both sides have the same price
  const free = hrs.filter(x => Math.abs(x.f) > 0.3 * cap && Math.abs(x.f) < 0.85 * cap && Math.abs(x.pu - x.pv) <= 0.5)
  const full = hrs.filter(x => Math.abs(x.f) >= cap - 1 && Math.abs(x.pu - x.pv) >= 40)
  if (!free.length || !full.length) continue
  const a = free.sort((p, q) => Math.abs(q.f) - Math.abs(p.f))[0], b = full.sort((p, q) => Math.abs(q.pu - q.pv) - Math.abs(p.pu - p.pv))[0]
  const cand = { line: key, from: u, to: v, cap, free: a, full: b }
  const pref = ['NGA->BEN', 'SEN->MLI']   // a cheap exporter behind a line that fills up
  if (!congestion || pref.indexOf(key) !== -1 && (pref.indexOf(congestion.line) === -1 || pref.indexOf(key) < pref.indexOf(congestion.line))) congestion = cand
}

/* ── The day ─────────────────────────────────────────────────────────────── */
const zones = Object.keys(NODES)
const mean = zones.reduce((a, z) => a + demo.hours.reduce((b, h) => b + demo.prices[z][String(h)], 0) / demo.hours.length, 0) / zones.length
const day = { welfare: demo.welfare, volume: demo.volume, saturatedLines: demo.saturated_lines, lines: map.lines.length, zones: zones.length, meanPrice: Math.round(mean), solver: demo.solver, scenario: demo.scenario }

const out = { map, prices: demo.prices, flows: demo.flows, ntc: demo.ntc, hours: demo.hours, linesSaturatedHours: Object.fromEntries(Object.entries(demo.lines).map(([k, v]) => [k, v.saturated_hours])), cross, congestion, day }
writeFileSync(join(root, 'assets', 'data.js'), `/* Generated by scripts/build-data.mjs from assets/demo.json: do not edit by hand (npm run data). */\nwindow.WAPP_DATA = ${JSON.stringify(out)};\n`)
console.log('cross:', cross.zone, `H${cross.hour}`, cross.price, '$/MWh, marginal', cross.marginal, 'supply', cross.supply.length, 'demand', cross.demand.length, 'net', cross.net, 'prod', cross.prod, 'cons', cross.cons)
console.log('congestion:', JSON.stringify(congestion))
console.log('day:', JSON.stringify(day))
console.log(`data.js: ${(JSON.stringify(out).length / 1024).toFixed(0)} KB`)
