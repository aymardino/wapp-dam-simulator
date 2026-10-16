// Tests one scene on its own: builds a throw-away project under .scene-tests/<scene>-<lang>/ whose root mounts only that
// scene at t = 0 (assets, node_modules and compositions are linked, not copied), then runs the HyperFrames checks on it.
//
//   node scripts/scene-test.mjs <scene-id> [--lang fr|en] [--at 0.5,2,4.5 | --frames 8] [--lint] [--check] [--out DIR]
//
// --at / --frames  snapshot stills (scene-local seconds), printed as PNG paths, plus a contact sheet
// --lint           hyperframes lint on the one-scene project
// --check          hyperframes check (lint + runtime + layout overflow + contrast) at the same times
// Without any of them: --lint and --frames 6.
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const root = join(here, '..')
const args = process.argv.slice(2)
const id = args[0]
const opt = (name, fallback) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args[i + 1] : fallback }
const flag = name => args.includes(`--${name}`)
const scenes = JSON.parse(readFileSync(join(root, 'scenes.json'), 'utf8')).scenes
const scene = scenes.find(s => s.id === id)
if (!scene) { console.error(`unknown scene "${id}"; one of: ${scenes.map(s => s.id).join(', ')}`); process.exit(2) }
const lang = opt('lang', 'fr') === 'en' ? 'en' : 'fr'
let at = opt('at', null), frames = opt('frames', null)
const doLint = flag('lint'), doCheck = flag('check')
const nothing = !at && !frames && !doLint && !doCheck
if (nothing) frames = '6'

// one-scene root: the real index.html, with only this scene's slot, at t = 0, and the language as default
const dir = join(root, '.scene-tests', `${id}-${lang}`)
rmSync(dir, { recursive: true, force: true }); mkdirSync(dir, { recursive: true })
for (const f of ['assets', 'node_modules', 'compositions', 'hyperframes.json', 'meta.json']) symlinkSync(join(root, f), join(dir, f))
let html = readFileSync(join(root, 'index.html'), 'utf8')
html = html.replace(/\n\s*<div id="el-[^\n]*data-composition-src[^\n]*><\/div>/g, '')
const slot = `\n      <div id="el-${id}" data-composition-id="${id}" data-composition-src="compositions/${id}.html" data-start="0" data-duration="${scene.duration}" data-track-index="1" data-width="1920" data-height="1080"></div>`
html = html.replace(/(<div id="root" data-composition-id="main"[^>]*data-duration=")[\d.]+("[^>]*>)/, `$1${scene.duration}$2${slot}`)
html = html.replace('"default":"fr"', `"default":"${lang}"`)
writeFileSync(join(dir, 'index.html'), html)

const env = { ...process.env, DO_NOT_TRACK: '1', HYPERFRAMES_SKIP_SKILLS: '1' }
const bin = join(root, 'node_modules', '.bin', 'hyperframes')
const clean = s => s.replace(/\x1b\[[0-9;]*m/g, '').split('\n').filter(l => !/^@hf-progress|█|░|\[INFO\]/.test(l)).join('\n')
const runShow = (cmd, extra) => {
  console.log(`\n$ hyperframes ${cmd} ${extra.join(' ')}   (scene ${id}, ${lang})`)
  try { const out = execFileSync(bin, [cmd, ...extra], { cwd: dir, env, stdio: ['ignore', 'pipe', 'pipe'], encoding: 'utf8', maxBuffer: 64 << 20 }); process.stdout.write(clean(out)); return true }
  catch (e) { process.stdout.write(clean(e.stdout || '') + clean(e.stderr || '')); return false }
}
let ok = true
if (doLint || nothing) ok = runShow('lint', []) && ok
if (doCheck) ok = runShow('check', at ? ['--at', at] : ['--samples', '9']) && ok
if (at || frames) {
  const out = opt('out', join(dir, 'snapshots'))
  if (existsSync(out)) rmSync(out, { recursive: true, force: true })
  ok = runShow('snapshot', [...(at ? ['--at', at, '--no-end'] : ['--frames', frames]), '-o', out, '--describe', 'false']) && ok
}
process.exit(ok ? 0 : 1)
