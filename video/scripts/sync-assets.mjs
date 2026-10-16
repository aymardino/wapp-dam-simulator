// Copies the website assets the video uses (logo, background patterns, partner logos, photo) from web/public into
// assets/site/, so that the website stays their single source. Run automatically after `npm install`.
import { cpSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const pub = join(here, '..', '..', 'web', 'public')
const out = join(here, '..', 'assets', 'site')
const files = ['mark-light.svg', 'mark.svg', 'patterns/topo-dark.svg', 'patterns/mesh-dark.svg', 'patterns/topo-light.svg', 'patterns/mesh-light.svg',
  'partners/mines-paris-psl.png', 'partners/ms-ose.png', 'partners/senelec.png', 'photos/solar-technicians.jpg']
for (const f of files) {
  mkdirSync(dirname(join(out, f)), { recursive: true })
  cpSync(join(pub, f), join(out, f))
}
console.log(`video assets: ${files.length} file(s) copied from web/public`)
