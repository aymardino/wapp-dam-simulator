// Renders the video in French and English and publishes it on the website:
//   renders/wapp-dam-simulator-<lang>.mp4      the HyperFrames render (H.264, 1920 × 1080, 30 fps)
//   ../web/public/video/wapp-dam-simulator-<lang>.mp4   re-encoded for the web (about 5 MB), moov atom first
//   ../web/public/video/poster-<lang>.jpg      the still the page shows before playing (the simulated day, scene 07)
//
//   node scripts/render.mjs [--lang fr|en] [--crf 22] [--no-publish]
// Voice-over (NARRATION.md): files assets/voice/<lang>/<scene-id>.(wav|m4a|mp3) are mixed in, each starting 0.5 s into
// its scene, loudness evened out (-16 LUFS). A scene shorter than its take + 1.2 s is lengthened first (scenes.json,
// then index.html), for both languages: a longer scene only holds its last state longer.
// HyperFrames needs Chrome Headless Shell (`npx hyperframes browser ensure` downloads it; HYPERFRAMES_BROWSER_PATH
// points to another copy) and FFmpeg on the PATH.
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
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

// voice-over takes, and the scene lengths they need
const voiceFile = (lang, id) => ['wav', 'm4a', 'mp3'].map(e => join(root, 'assets', 'voice', lang, `${id}.${e}`)).find(existsSync)
const seconds = f => Number(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], { encoding: 'utf8' }))
let lengthened = false
for (const s of scenes.scenes) {
  const need = Math.max(0, ...['fr', 'en'].map(l => voiceFile(l, s.id)).filter(Boolean).map(f => seconds(f) + 1.2))
  if (need > s.duration) { console.log(`  ${s.id}: ${s.duration} s → ${Math.ceil(need * 2) / 2} s for its voice-over`); s.duration = Math.ceil(need * 2) / 2; lengthened = true }
}
if (lengthened) {
  writeFileSync(join(root, 'scenes.json'), JSON.stringify(scenes, null, 1) + '\n')
  execFileSync('node', [join(here, 'build-index.mjs')], { stdio: 'inherit' })
}
const starts = []
{ let t0 = 0; for (const s of scenes.scenes) { starts.push(Math.round(t0 * 100) / 100); t0 = starts[starts.length - 1] + s.duration - scenes.overlap } }
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
  // re-encoded for the web: flat colours compress well (about 5 MB a minute and a half); moov atom first; the
  // voice-over, when there are takes, mixed in at the start of each scene
  const takes = scenes.scenes.map((s, i) => ({ f: voiceFile(lang, s.id), at: starts[i] + 0.5 })).filter(x => x.f)
  const enc = ['-c:v', 'libx264', '-preset', 'slow', '-crf', '26', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
  if (!takes.length) execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', mp4, ...enc, '-an', web])
  else {
    const mix = takes.map((x, i) => `[${i + 1}:a]aresample=48000,adelay=${Math.round(x.at * 1000)}:all=1[v${i}]`).join(';') +
      `;${takes.map((x, i) => `[v${i}]`).join('')}amix=inputs=${takes.length}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]`
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', mp4, ...takes.flatMap(x => ['-i', x.f]), '-filter_complex', mix, '-map', '0:v', '-map', '[a]', ...enc, '-c:a', 'aac', '-b:a', '128k', web])
    console.log(`  voice-over: ${takes.length} take(s) mixed in`)
  }
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-ss', poster.toFixed(2), '-i', mp4, '-frames:v', '1', '-q:v', '3', jpg])
  console.log(`  published: ${web} (${mb(web)}), ${jpg}`)
}
