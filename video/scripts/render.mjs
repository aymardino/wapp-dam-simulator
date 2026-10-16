// Renders the video in French and English and publishes it on the website:
//   renders/wapp-dam-simulator-<lang>.mp4      the HyperFrames render (H.264, 1920 × 1080, 30 fps)
//   ../web/public/video/wapp-dam-simulator-<lang>.mp4   re-encoded for the web (about 5 MB), moov atom first
//   ../web/public/video/poster-<lang>.jpg      the still the page shows before playing (the simulated day, scene 07)
//
//   node scripts/render.mjs [--lang fr|en] [--crf 22] [--no-publish]
// HyperFrames needs Chrome Headless Shell (`npx hyperframes browser ensure` downloads it; HYPERFRAMES_BROWSER_PATH
// points to another copy) and FFmpeg on the PATH.
import { execFileSync } from 'node:child_process'
import { mkdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const root = join(here, '..')
const args = process.argv.slice(2)
const opt = (name, fallback) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args[i + 1] : fallback }
const langs = opt('lang', null) ? [opt('lang')] : ['fr', 'en']
const crf = opt('crf', '22')
const publish = !args.includes('--no-publish')
const env = { ...process.env, DO_NOT_TRACK: '1', HYPERFRAMES_SKIP_SKILLS: '1' }
const scenes = JSON.parse(readFileSync(join(root, 'scenes.json'), 'utf8'))
// poster: two seconds before the end of scene 07, when the whole day is on the map
let t = 0, poster = 0
for (const s of scenes.scenes) { if (s.id === '07-day') poster = t + s.duration - 2; t += s.duration - scenes.overlap }

const out = join(root, 'renders'), site = join(root, '..', 'web', 'public', 'video')
mkdirSync(out, { recursive: true })
if (publish) mkdirSync(site, { recursive: true })
const mb = f => `${(statSync(f).size / 1e6).toFixed(1)} MB`
for (const lang of langs) {
  const mp4 = join(out, `wapp-dam-simulator-${lang}.mp4`)
  console.log(`\n▶ ${lang}: rendering…`)
  execFileSync(join(root, 'node_modules', '.bin', 'hyperframes'), ['render', '--output', mp4, '--fps', '30', '--crf', crf, '--quiet', '--strict', '--variables', JSON.stringify({ lang })], { cwd: root, env, stdio: 'inherit' })
  console.log(`  ${mp4} (${mb(mp4)})`)
  if (!publish) continue
  const web = join(site, `wapp-dam-simulator-${lang}.mp4`), jpg = join(site, `poster-${lang}.jpg`)
  // re-encoded for the web: flat colours compress well, about 5 MB for 78 s; moov atom first, no audio track
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', mp4, '-c:v', 'libx264', '-preset', 'slow', '-crf', '26', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', web])
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-ss', poster.toFixed(2), '-i', mp4, '-frames:v', '1', '-q:v', '3', jpg])
  console.log(`  published: ${web} (${mb(web)}), ${jpg}`)
}
