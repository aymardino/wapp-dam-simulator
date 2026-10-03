/** Content of the About section: people, institutions, timeline.
 *  Photos go in web/public/team/ (square, 400 px or more); official logos in web/public/partners/.
 *  Add a logo only with the institution's written consent. A missing file falls back to initials or to the name. */
import media from './data/media.json'

export type Person = { name: string; role: [string, string]; org: string; photo?: string; linkedin?: string }
export type Partner = { name: string; logo?: string; url: string }

/** URL of a file present in public/<kind>/ whose name (without extension) is `stem`; undefined when absent.
 *  The list comes from src/data/media.json, generated at build time by scripts/media_manifest.mjs. */
const file = (kind: 'team' | 'partners', stem: string) => {
  const f = (media as Record<string, string[]>)[kind].find(x => x.replace(/\.[^.]+$/, '') === stem)
  return f ? `/${kind}/${f}` : undefined
}

export const AUTHORS: Person[] = [
  { name: 'Kodjovi Plakoo', role: ['Co-auteur du simulateur', 'Co-author of the simulator'], org: 'Mines Paris – PSL · MS OSE 2025', photo: file('team', 'kodjovi-plakoo'), linkedin: 'https://www.linkedin.com/in/kodjovi-aymard-plakoo-a95a74183' },
  { name: 'Enrico Patanè', role: ['Co-auteur du simulateur', 'Co-author of the simulator'], org: 'Mines Paris – PSL · MS OSE 2025', photo: file('team', 'enrico-patane'), linkedin: 'https://www.linkedin.com/in/enricopatane98/' },
]
export const CONTRIBUTORS: Person[] = ['Lucien Kouakou', 'Mouhamadou Sow', 'Wissem Hmila'].map(name => ({
  name, role: ['Groupe projet', 'Project group'] as [string, string], org: 'Mines Paris – PSL · MS OSE 2025',
  photo: file('team', name.toLowerCase().replace(/\s+/g, '-')),
}))
export const SUPERVISORS: Person[] = [
  { name: 'El Hadji Tamsir Diop', role: ['Encadrant du projet', 'Project supervisor'], org: 'SENELEC', photo: file('team', 'tamsir-diop') },
  { name: 'Adrien Atayi', role: ['Encadrant du projet', 'Project supervisor'], org: 'EPEX SPOT', photo: file('team', 'adrien-atayi') },
]
export const PARTNERS: Partner[] = [
  { name: 'Mines Paris – PSL', logo: file('partners', 'mines-paris-psl'), url: 'https://www.minesparis.psl.eu' },
  { name: 'Mastère Spécialisé OSE', logo: file('partners', 'ms-ose'), url: 'https://www.cma.mines-paristech.fr/formation/the-ose-specialised-master/' },
  { name: 'SENELEC', logo: file('partners', 'senelec'), url: 'https://www.senelec.sn' },
]
/** [date, French, English] */
export const TIMELINE: [string, string, string][] = [
  ['03 · 2026', 'Formulation du clearing en trois problèmes', 'Clearing formulated as three problems'],
  ['04 · 2026', 'Premier simulateur livré', 'First simulator delivered'],
  ['10 · 2026', 'Version ouverte : code, données, site', 'Open version: code, data, website'],
  ['01 · 2027', 'Lancement prévu du marché day-ahead du WAPP', 'Planned launch of the WAPP day-ahead market'],
]
