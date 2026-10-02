// Extracts the West African countries from Natural Earth (world-atlas, public domain) as a light GeoJSON.
import { readFileSync, writeFileSync } from 'node:fs'
import { feature } from 'topojson-client'
const topo = JSON.parse(readFileSync(new URL('../node_modules/world-atlas/countries-50m.json', import.meta.url)))
const fc = feature(topo, topo.objects.countries)
const MEMBERS = { '566': 'NGA', '204': 'BEN', '768': 'TGO', '288': 'GHA', '384': 'CIV', '854': 'BFA', '466': 'MLI', '686': 'SEN', '324': 'GIN', '694': 'SLE', '430': 'LBR', '624': 'GNB', '270': 'GMB', '562': 'NER' }
const CONTEXT = { '478': 'MRT', '012': 'DZA', '434': 'LBY', '148': 'TCD', '120': 'CMR', '732': 'ESH', '504': 'MAR', '140': 'CAF', '226': 'GNQ', '266': 'GAB', '178': 'COG' }
const round = (n) => Math.round(n * 100) / 100
const simplify = (coords) => Array.isArray(coords[0]) ? coords.map(simplify) : [round(coords[0]), round(coords[1])]
const out = { type: 'FeatureCollection', features: [] }
for (const f of fc.features) {
  const id = String(f.id).padStart(3, '0')
  const code = MEMBERS[id] || CONTEXT[id]
  if (!code) continue
  out.features.push({ type: 'Feature', id: code, properties: { member: id in MEMBERS }, geometry: { type: f.geometry.type, coordinates: simplify(f.geometry.coordinates) } })
}
writeFileSync(new URL('../src/data/west_africa.geo.json', import.meta.url), JSON.stringify(out))
console.log(`${out.features.length} pays écrits, ${Math.round(JSON.stringify(out).length / 1024)} Ko`)
