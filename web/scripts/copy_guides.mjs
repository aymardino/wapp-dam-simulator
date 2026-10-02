// Copie les guides (docs/guides) dans web/public/guides pour qu'ils soient servis avec l'application.
import { mkdirSync, readdirSync, copyFileSync } from 'node:fs'
const src = new URL('../../docs/guides/', import.meta.url), dst = new URL('../public/guides/', import.meta.url)
mkdirSync(dst, { recursive: true })
for (const f of readdirSync(src)) if (f.endsWith('.md')) copyFileSync(new URL(f, src), new URL(f, dst))
console.log('guides copiés')
