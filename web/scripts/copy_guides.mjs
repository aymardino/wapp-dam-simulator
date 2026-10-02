// Copies the guides (docs/guides) into web/public/guides so they are served with the application.
import { mkdirSync, readdirSync, copyFileSync } from 'node:fs'
const src = new URL('../../docs/guides/', import.meta.url), dst = new URL('../public/guides/', import.meta.url)
mkdirSync(dst, { recursive: true })
for (const f of readdirSync(src)) if (f.endsWith('.md')) copyFileSync(new URL(f, src), new URL(f, dst))
console.log('guides copied')
