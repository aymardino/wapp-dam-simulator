// Lists the team photos and partner logos present in public/, so that the page only requests files that exist.
// Run before every build and dev start (see package.json). Output: src/data/media.json.
import { existsSync, mkdirSync, readdirSync, writeFileSync } from 'node:fs'
const list = dir => {
  const url = new URL(`../public/${dir}/`, import.meta.url)
  return existsSync(url) ? readdirSync(url).filter(f => /\.(jpe?g|png|webp|svg)$/i.test(f)).sort() : []
}
mkdirSync(new URL('../src/data/', import.meta.url), { recursive: true })
const manifest = { team: list('team'), partners: list('partners') }
writeFileSync(new URL('../src/data/media.json', import.meta.url), JSON.stringify(manifest, null, 2) + '\n')
console.log(`media manifest: ${manifest.team.length} photo(s), ${manifest.partners.length} logo(s)`)
