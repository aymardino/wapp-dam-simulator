/** Public home page (wapp-dam-simulator.org). Identity: editorial serif headings, price ticker, dark
 *  "control room" map driven by a histogram hour selector, per-zone supply / demand explorer built on the
 *  reference orders, spec sheet, terminal block. Bilingual FR/EN. */
import { Fragment, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useLang, type Lang } from '../i18n'
import { LangToggle } from '../components/ui'
import NetworkMap from '../components/NetworkMap'
import PriceHeatmap from '../components/PriceHeatmap'
import { LINKS } from '../links'

type SupRow = { zone: string; actor: string; segment: number; quantity: number; price: number; profile?: string }
type DemRow = { zone: string; actor: string; segment: number; quantity: number; price: number }
export type Demo = { scenario: string; hours: number[]; prices: Record<string, Record<string, number>>; flows: Record<string, Record<string, number>>; ntc: Record<string, number>; welfare: number; volume: number; net_pos: Record<string, number>; saturated_lines: number; elapsed: number; solver: string; supply: SupRow[]; demand: DemRow[]; profiles: Record<string, number[]>; load: number[]; lines: Record<string, { saturated_hours: number }> }
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) || '/api/v1'
const ZONES = ['SEN', 'GMB', 'GNB', 'GIN', 'SLE', 'LBR', 'MLI', 'BFA', 'NER', 'CIV', 'GHA', 'TGO', 'BEN', 'NGA']
const ZONE_NAMES: Record<string, [string, string]> = { SEN: ['Sénégal', 'Senegal'], GMB: ['Gambie', 'The Gambia'], GNB: ['Guinée-Bissau', 'Guinea-Bissau'], GIN: ['Guinée', 'Guinea'], SLE: ['Sierra Leone', 'Sierra Leone'], LBR: ['Liberia', 'Liberia'], MLI: ['Mali', 'Mali'], BFA: ['Burkina Faso', 'Burkina Faso'], NER: ['Niger', 'Niger'], CIV: ['Côte d’Ivoire', 'Côte d’Ivoire'], GHA: ['Ghana', 'Ghana'], TGO: ['Togo', 'Togo'], BEN: ['Bénin', 'Benin'], NGA: ['Nigeria', 'Nigeria'] }
const hh = (h: number) => `H${String(h).padStart(2, '0')}`
const nf = (x: number, d = 0) => x.toLocaleString('fr-FR', { maximumFractionDigits: d, minimumFractionDigits: d })
const money = (x: number) => `${nf(x / 1e6, 2)} M USD`

const L = {
  fr: {
    nav: [['#explorer', 'Explorer'], ['#moteur', 'Le moteur'], ['#fiche', 'Fiche technique'], ['#ouvert', 'Code']] as [string, string][],
    nav_guides: 'Guides', nav_app: 'Ouvrir le simulateur',
    kicker: 'Implémentation ouverte de référence · couplage de marché zonal',
    title_1: 'Le marché day-ahead du West African Power Pool,', title_2: 'expliqué par le calcul.',
    lead: 'Les traders déposent leurs offres pour le lendemain ; le moteur fixe les volumes, les prix et les flux entre quatorze pays. Chaque règle est écrite, testée, et vous pouvez la vérifier ici même.',
    cta_app: 'Ouvrir le simulateur', cta_explore: 'Explorer une zone',
    computed: (t: number) => `Scénario de démonstration (données 2024 reconstituées), calculé par le moteur à l’ouverture de cette page en ${t.toFixed(2)} s`,
    map_hint: 'Prix simulés en $/MWh (pas des prix observés) et flux sur les quinze interconnexions ; les lignes en corail sont saturées. Les barres donnent le prix moyen de chaque heure : cliquez pour figer l’heure, cliquez un pays pour lire sa position.',
    welfare: 'welfare', volume: 'volume', saturated: 'lignes saturées',
    loading: 'Calcul du cas de référence…', demo_err: 'Le serveur de démonstration ne répond pas.',
    ex_kicker: 'Explorer', ex_title: 'Pourquoi ce prix, dans cette zone, à cette heure',
    ex_lead: 'Les ordres du scénario de démonstration (centrales et demande de la zone, données 2024 reconstituées) forment une courbe d’offre et une courbe de demande. Le prix zonal ne se lit pas à leur croisement : le réseau déplace l’équilibre par les importations et les exportations.',
    ex_supply: 'Offre (centrales)', ex_demand: 'Demande (charge)', ex_price: 'prix zonal', ex_export: 'export', ex_import: 'import',
    ex_seg_title: 'Ordres de la zone à l’heure choisie', ex_accepted: 'retenu', ex_marginal: 'marginal', ex_rejected: 'hors marché',
    ex_prices_title: 'Les quatorze prix sur vingt-quatre heures', ex_prices_hint: 'Prix simulés sur le scénario de démonstration, pas des prix observés. Une ligne par zone, une colonne par heure : les zones de même couleur partagent le même prix, un trait sépare les groupes isolés par une ligne saturée. Cliquez une zone pour l’explorer.',
    m_kicker: 'Le moteur', m_title: 'Trois questions, trois programmes, dans cet ordre',
    m_lead: 'Un couplage de marché répond chaque jour à trois questions. Le moteur les prend l’une après l’autre, comme un algorithme de bourse, mais à livre ouvert : les règles sont dans le code et dans la documentation.',
    steps: [
      ['P1', 'optimisation linéaire, entière avec des blocs', 'Qui est servi ?', 'Maximiser le welfare, la valeur créée par les échanges, sous l’équilibre de chaque zone, les capacités des lignes et la contrainte d’interdépendance CIV / GHA / BFA.'],
      ['P1bis', 'optimisation linéaire', 'Combien ?', 'Parmi les solutions de welfare égal, retenir celle qui échange le plus de volume, exactement, sans tolérance numérique.'],
      ['P2', 'optimisation linéaire', 'À quel prix ?', 'Parmi tous les prix compatibles avec l’équilibre (ordres acceptés, rejetés, lignes saturées ou libres), choisir le milieu de l’intervalle admissible.'],
    ] as [string, string, string, string][],
    m_interval: ['prix admissible le plus bas', 'retenu', 'le plus haut'], m_note: 'Les blocs paradoxalement acceptés sont rejetés et le calcul repris ; les ordres au même prix sont servis au prorata ; une condition de revenu minimum non satisfaite retire les offres de l’acteur et relance le calcul.',
    f_kicker: 'Fiche technique', f_title: 'Ce qui est dans la boîte', f_lead: 'Un moteur de clearing complet, des salles de formation et des données de référence sourcées, dans un seul dépôt.',
    spec: [
      ['Ordres', 'Segments prix–quantité avec profil horaire (solaire, hydraulique, base, pointe, constant)'],
      ['Blocs', 'Tout ou rien (fill-or-kill), liés (enfant ⇒ parent), exclusifs (au plus un par groupe) ; blocs paradoxalement acceptés rejetés itérativement, paradoxalement rejetés signalés'],
      ['Conditions', 'Revenu minimum (terme fixe + terme variable × volume) : retrait des offres et relance'],
      ['Départage', 'Welfare, puis volume exact, puis prix au milieu de l’intervalle admissible ; ex æquo au prorata des quantités'],
      ['Réseau', 'Quatorze zones, quinze interconnexions, capacités d’échange (NTC) éditables par salle, flux signés, rentes de congestion'],
      ['Données', 'Scénario 2024 reconstitué à partir de sources publiques (parc, demande, capacités d’échange estimées) et quatre variantes pédagogiques : sécheresse hydraulique, ligne Nigeria–Bénin indisponible, gaz cher, forte demande'],
      ['Vérifications', 'Bornes de prix, flux dans les capacités, équilibre horaire, règles de blocs, identité du welfare ; 65 tests, campagne de cas aléatoires'],
      ['Interfaces', 'Salles de formation (web, temps réel), API REST documentée, ligne de commande, exports CSV et JSON, français et anglais'],
      ['Solveurs', 'Solveur libre HiGHS inclus ; Gurobi utilisé s’il est installé ; modèles Pyomo'],
      ['Licence', 'Apache 2.0 pour le code, CC BY 4.0 pour les données et la documentation'],
    ] as [string, string][],
    w_title: 'Trois usages',
    w: [
      ['Former', 'Une séance de marché en trois manches : chaque participant représente un pays, dépose ses offres, découvre son résultat et les prix des voisins. Guide du formateur inclus.'],
      ['Étudier', 'Un cas-test public, des règles écrites et un moteur ouvert pour travailler le couplage zonal, les blocs et l’indétermination des prix.'],
      ['Comparer', 'Rejouer un cas, confronter les résultats à ceux d’une autre plateforme, discuter des règles de départage avant le lancement du marché.'],
    ] as [string, string][],
    guide_trainer: 'Guide du formateur', guide_trader: 'Guide du trader',
    o_kicker: 'Ouvert et vérifiable', o_title: 'Rien à croire sur parole',
    o_lead: 'Le code est public sous licence Apache 2.0, les données et la documentation sous CC BY 4.0. Les valeurs du cas de référence sont fixées par des tests, et une campagne de cas aléatoires contrôle les propriétés du clearing à chaque modification.',
    o_links: ['Règles de marché', 'Données de référence', 'Architecture', 'Déploiement', 'Dépôt GitHub'],
    o_note: 'Trois commandes suffisent pour rejouer sur votre poste le cas de test qui fixe les valeurs de non-régression du moteur : welfare 22 317 910 USD, volume 167 900 MWh.',
    d_title: 'Avertissements',
    d1: 'Simulateur pédagogique indépendant. Ce projet n’est pas affilié au West African Power Pool, à son Centre d’Information et de Coordination ni à aucun fournisseur de plateforme de marché. « WAPP » et « West African Power Pool » appartiennent au WAPP.',
    d2: 'Les données du scénario de démonstration (parc, demande, capacités d’échange) sont reconstituées à partir de sources publiques et de valeurs estimées. Les prix affichés sont des résultats de simulation sur ces données, pas des prix observés : le marché day-ahead du WAPP n’a pas encore démarré. Elles servent à la formation et à la recherche, pas à l’exploitation.',
    a_title: 'Auteurs',
    a_text: 'Kodjovi Plakoo et Enrico Patanè, Mastère Spécialisé OSE 2025, Mines Paris-PSL, avec Lucien Kouakou, Mouhamadou Sow et Wissem Hmila pour les premières phases du projet. Encadrement : El Hadji Tamsir Diop (SENELEC) et Adrien Atayi (EPEX SPOT).',
    a_paper: 'Note technique à paraître.', a_paper_link: 'Lire la note technique', contact: 'Questions et contributions',
    footer: 'Simulateur pédagogique indépendant, non affilié au WAPP.',
    sim_badge: 'Simulation sur données 2024 reconstituées, pas des prix observés',
    src_title: 'D’où viennent ces chiffres ?',
    src_items: [
      ['Sourcé', 'Capacités installées et principales centrales de chaque pays, capacités contractuelles de plusieurs lignes, prix du gaz au Nigeria et au Ghana : rapports publics cités, ligne par ligne, dans la documentation.'],
      ['Estimé', 'Pointes de demande de plusieurs pays, capacités d’échange des lignes sans valeur publiée (corridor Ghana–Togo–Bénin, boucle OMVG, Mali), profils horaires de charge et de production.'],
      ['Hypothèse', 'Prix des offres de vente : coût variable typique de chaque technologie (hydraulique 12 à 36 $/MWh, fioul lourd 125 à 210), prix d’achat par tranche. Ce ne sont pas les offres réelles des acteurs.'],
    ] as [string, string][],
    src_note: 'Le marché day-ahead du WAPP n’a pas encore démarré : il n’existe pas de prix observés auxquels comparer ces résultats. Les niveaux de prix dépendent de nos hypothèses ; la structure (qui importe, quelles lignes saturent) dépend surtout des capacités d’échange, à valider avec le centre de coordination du WAPP.',
    src_link: 'Sources et hypothèses, ligne par ligne',
  },
  en: {
    nav: [['#explorer', 'Explore'], ['#moteur', 'The engine'], ['#fiche', 'Spec sheet'], ['#ouvert', 'Code']] as [string, string][],
    nav_guides: 'Guides', nav_app: 'Open the simulator',
    kicker: 'Open reference implementation · zonal market coupling',
    title_1: 'The West African Power Pool day-ahead market,', title_2: 'explained by computation.',
    lead: 'Traders submit orders for the next day; the engine sets volumes, prices and flows across fourteen countries. Every rule is written down, tested, and you can check it right here.',
    cta_app: 'Open the simulator', cta_explore: 'Explore a zone',
    computed: (t: number) => `Demonstration scenario (reconstructed 2024 data), computed by the engine when this page opened in ${t.toFixed(2)} s`,
    map_hint: 'Simulated prices in $/MWh (not observed prices) and flows on the fifteen interconnections; coral lines are saturated. The bars give the mean price of each hour: click to freeze the hour, click a country to read its position.',
    welfare: 'welfare', volume: 'volume', saturated: 'saturated lines',
    loading: 'Computing the reference case…', demo_err: 'The demonstration server is not responding.',
    ex_kicker: 'Explore', ex_title: 'Why this price, in this zone, at this hour',
    ex_lead: 'The demonstration scenario’s orders (the zone’s plants and demand, reconstructed 2024 data) form a supply curve and a demand curve. The zonal price is not read at their crossing: the network shifts the balance through imports and exports.',
    ex_supply: 'Supply (plants)', ex_demand: 'Demand (load)', ex_price: 'zonal price', ex_export: 'export', ex_import: 'import',
    ex_seg_title: 'Orders of the zone at the chosen hour', ex_accepted: 'accepted', ex_marginal: 'marginal', ex_rejected: 'out of market',
    ex_prices_title: 'Fourteen prices over twenty-four hours', ex_prices_hint: 'Simulated prices on the demonstration scenario, not observed prices. One row per zone, one column per hour: zones sharing a colour share a price, a rule separates groups isolated by a saturated line. Click a zone to explore it.',
    m_kicker: 'The engine', m_title: 'Three questions, three programs, in that order',
    m_lead: 'A market coupling answers three questions every day. The engine takes them one after the other, like an exchange algorithm, but with the book open: the rules are in the code and in the documentation.',
    steps: [
      ['P1', 'linear optimisation, integer with blocks', 'Who is served?', 'Maximise welfare, the value created by trades, under each zone’s balance, line capacities and the CIV / GHA / BFA interdependence constraint.'],
      ['P1bis', 'linear optimisation', 'How much?', 'Among equal-welfare solutions, keep the one that trades the most volume, exactly, with no numerical tolerance.'],
      ['P2', 'linear optimisation', 'At what price?', 'Among all prices consistent with equilibrium (accepted and rejected orders, saturated or free lines), pick the midpoint of the admissible interval.'],
    ] as [string, string, string, string][],
    m_interval: ['lowest admissible price', 'chosen', 'highest'], m_note: 'Paradoxically accepted blocks are rejected and the run repeated; equal-price orders are served pro rata; an unmet minimum income condition withdraws the actor’s orders and reruns the clearing.',
    f_kicker: 'Spec sheet', f_title: 'What is in the box', f_lead: 'A complete clearing engine, training rooms and sourced reference data, in a single repository.',
    spec: [
      ['Orders', 'Price–quantity segments with hourly profiles (solar, hydro, baseload, peaking, flat)'],
      ['Blocks', 'All-or-nothing (fill-or-kill), linked (child ⇒ parent), exclusive (at most one per group); paradoxically accepted blocks rejected iteratively, paradoxically rejected ones reported'],
      ['Conditions', 'Minimum income (fixed term + variable term × volume): orders withdrawn and clearing rerun'],
      ['Tie-break', 'Welfare, then exact volume, then the midpoint of the admissible price interval; equal prices shared pro rata'],
      ['Network', 'Fourteen zones, fifteen interconnections, exchange capacities (NTC) editable per room, signed flows, congestion rents'],
      ['Data', '2024 scenario rebuilt from public sources (fleet, demand, estimated exchange capacities) and four teaching variants: hydro drought, Nigeria–Benin line out, expensive gas, high demand'],
      ['Checks', 'Price bounds, flows within capacities, hourly balance, block rules, welfare identity; 65 tests, random-case campaign'],
      ['Interfaces', 'Training rooms (web, live), documented REST API, command line, CSV and JSON exports, French and English'],
      ['Solvers', 'Open-source HiGHS solver included; Gurobi used when installed; Pyomo models'],
      ['Licence', 'Apache 2.0 for the code, CC BY 4.0 for data and documentation'],
    ] as [string, string][],
    w_title: 'Three uses',
    w: [
      ['Train', 'A three-round market session: each participant represents a country, submits orders, discovers their result and the neighbours’ prices. Trainer guide included.'],
      ['Study', 'A public test case, written rules and an open engine to work on zonal coupling, blocks and price indeterminacy.'],
      ['Compare', 'Replay a case, confront results with those of another platform, discuss tie-break rules before the market goes live.'],
    ] as [string, string][],
    guide_trainer: 'Trainer guide', guide_trader: 'Trader guide',
    o_kicker: 'Open and verifiable', o_title: 'Nothing to take on faith',
    o_lead: 'The code is public under the Apache 2.0 licence, data and documentation under CC BY 4.0. Reference-case values are pinned by tests, and a campaign of random cases checks clearing properties on every change.',
    o_links: ['Market rules', 'Reference data', 'Architecture', 'Deployment', 'GitHub repository'],
    o_note: 'Three commands replay on your machine the test case that pins the engine’s regression values: welfare 22,317,910 USD, volume 167,900 MWh.',
    d_title: 'Disclaimers',
    d1: 'Independent educational simulator. This project is not affiliated with the West African Power Pool, its Information and Coordination Centre, or any market platform vendor. “WAPP” and “West African Power Pool” belong to the WAPP.',
    d2: 'The demonstration scenario’s data (fleet, demand, exchange capacities) are rebuilt from public sources and estimated values. The prices shown are simulation results on these data, not observed prices: the WAPP day-ahead market has not started yet. They are meant for training and research, not for operations.',
    a_title: 'Authors',
    a_text: 'Kodjovi Plakoo and Enrico Patanè, Advanced Master OSE 2025, Mines Paris-PSL, with Lucien Kouakou, Mouhamadou Sow and Wissem Hmila for the first phases of the project. Supervision: El Hadji Tamsir Diop (SENELEC) and Adrien Atayi (EPEX SPOT).',
    a_paper: 'Technical note forthcoming.', a_paper_link: 'Read the technical note', contact: 'Questions and contributions',
    footer: 'Independent educational simulator, not affiliated with the WAPP.',
    sim_badge: 'Simulation on reconstructed 2024 data, not observed prices',
    src_title: 'Where do these figures come from?',
    src_items: [
      ['Sourced', 'Installed capacities and main plants of each country, contractual capacities of several lines, gas prices in Nigeria and Ghana: public reports cited, line by line, in the documentation.'],
      ['Estimated', 'Peak demand of several countries, exchange capacities of lines with no published value (Ghana–Togo–Benin corridor, OMVG loop, Mali), hourly load and generation profiles.'],
      ['Assumption', 'Sell order prices: typical variable cost of each technology (hydro 12 to 36 $/MWh, heavy fuel oil 125 to 210), buy prices by tranche. These are not the actors’ real bids.'],
    ] as [string, string][],
    src_note: 'The WAPP day-ahead market has not started yet: there are no observed prices to compare these results with. Price levels depend on our assumptions; the structure (who imports, which lines saturate) depends mostly on exchange capacities, to be validated with the WAPP coordination centre.',
    src_link: 'Sources and assumptions, line by line',
  },
}
type Strings = typeof L.fr

/* ── Explorer computations ────────────────────────────────────────────── */
type Seg = { actor: string; price: number; qty: number }
type Curves = { sup: Seg[]; dem: Seg[]; price: number; net: number; lines: { other: string; flow: number; cap: number; sat: boolean }[]; supAt: number; demAt: number }

function zoneCurves(demo: Demo, zone: string, h: number): Curves {
  const prof = (name?: string) => demo.profiles[name || 'baseload'] || demo.profiles.flat || Array(24).fill(1)
  const sup = demo.supply.filter(r => r.zone === zone).map(r => ({ actor: r.actor, price: r.price, qty: Math.round(r.quantity * prof(r.profile)[h]) })).filter(r => r.qty > 0).sort((a, b) => a.price - b.price)
  const dem = demo.demand.filter(r => r.zone === zone).map(r => ({ actor: r.actor, price: r.price, qty: Math.round(r.quantity * demo.load[h]) })).filter(r => r.qty > 0).sort((a, b) => b.price - a.price)
  const price = demo.prices[zone]?.[String(h)] ?? 0
  let net = 0; const lines: Curves['lines'] = []
  for (const key of Object.keys(demo.ntc)) {
    const [u, v] = key.split('->'); if (u !== zone && v !== zone) continue
    const f = demo.flows[key]?.[String(h)] ?? 0; const cap = demo.ntc[key]; const out = u === zone ? f : -f
    net += out; lines.push({ other: u === zone ? v : u, flow: out, cap, sat: Math.abs(f) >= cap - 1 })
  }
  const supAt = sup.filter(r => r.price <= price + 0.5).reduce((a, r) => a + r.qty, 0)
  const demAt = dem.filter(r => r.price >= price - 0.5).reduce((a, r) => a + r.qty, 0)
  return { sup, dem, price, net, lines, supAt, demAt }
}

function sentence(c: Curves, zone: string, hour: number, lang: Lang) {
  const name = ZONE_NAMES[zone][lang === 'fr' ? 0 : 1]; const p = Math.round(c.price); const n = Math.round(c.net)
  const flows = c.lines.map(l => `${zone}–${l.other} ${l.flow >= 0 ? '→' : '←'} ${nf(Math.abs(Math.round(l.flow)))}/${nf(l.cap)} MW${l.sat ? (lang === 'fr' ? ' (saturée)' : ' (saturated)') : ''}`).join(' · ')
  if (lang === 'fr') {
    const pos = n > 1 ? `exporte ${nf(n)} MW` : n < -1 ? `importe ${nf(-n)} MW` : 'est à l’équilibre avec ses voisins'
    return `À ${hh(hour)}, le prix de la zone ${name} est de ${p} $/MWh. À ce prix, les centrales disposées à produire offrent ${nf(c.supAt)} MW et la demande acceptable est de ${nf(c.demAt)} MW : la zone ${pos}. ${flows ? `Lignes : ${flows}.` : ''}`
  }
  const pos = n > 1 ? `exports ${nf(n)} MW` : n < -1 ? `imports ${nf(-n)} MW` : 'is balanced with its neighbours'
  return `At ${hh(hour)}, the price of zone ${name} is ${p} $/MWh. At that price, plants willing to run offer ${nf(c.supAt)} MW and acceptable demand is ${nf(c.demAt)} MW: the zone ${pos}. ${flows ? `Lines: ${flows}.` : ''}`
}

const niceCeil = (v: number) => { const pow = Math.pow(10, Math.floor(Math.log10(Math.max(v, 1)))); const f = v / pow; const m = f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10; return m * pow }
const ticks = (max: number, n: number) => { const step = niceCeil(max / n); const out: number[] = []; for (let v = 0; v <= max + 1e-9; v += step) out.push(v); return out }

/* ── Components ───────────────────────────────────────────────────────── */
function Ticker({ demo, hour, s }: { demo: Demo; hour: number; s: Strings }) {
  const h = String(hour)
  const items: ReactNode[] = [
    <span key="s" className="text-mint/60 text-xs">{s.sim_badge}</span>,
    <span key="h" className="text-amber">{hh(hour)}</span>,
    ...ZONES.map(z => <span key={z}><span className="text-mint/70">{z}</span> <span className="text-white">{Math.round(demo.prices[z]?.[h] ?? 0)}</span></span>),
    <span key="w"><span className="text-mint/70">{s.welfare}</span> <span className="text-white">{money(demo.welfare)}</span></span>,
    <span key="v"><span className="text-mint/70">{s.volume}</span> <span className="text-white">{nf(demo.volume)} MWh</span></span>,
    <span key="l"><span className="text-mint/70">{s.saturated}</span> <span className="text-white">{demo.saturated_lines}/15</span></span>,
  ]
  const row = (k: string) => items.map((it, i) => <span key={`${k}${i}`} className="inline-flex items-center px-5">{it}</span>)
  return (
    <div className="bg-deep border-y border-white/10 overflow-hidden font-mono text-sm h-9 flex items-center" aria-hidden>
      <div className="ticker-track flex whitespace-nowrap w-max">{row('a')}{row('b')}</div>
    </div>
  )
}

function HourStrip({ demo, hour, onPick, dark }: { demo: Demo; hour: number; onPick: (h: number) => void; dark?: boolean }) {
  const means = demo.hours.map(h => ZONES.reduce((a, z) => a + (demo.prices[z]?.[String(h)] ?? 0), 0) / ZONES.length)
  const max = Math.max(...means, 1)
  return (
    <div>
      <div className="flex items-end gap-[3px] h-14">
        {demo.hours.map((h, i) => (
          <button key={h} onClick={() => onPick(h)} title={`${hh(h)} · ${Math.round(means[i])} $/MWh`} aria-label={hh(h)}
            className={`flex-1 rounded-sm transition-colors ${h === hour ? 'bg-amber' : dark ? 'bg-mint/40 hover:bg-mint/70' : 'bg-accent/30 hover:bg-accent/60'}`}
            style={{ height: `${Math.max(8, (means[i] / max) * 100)}%` }} />
        ))}
      </div>
      <div className={`flex justify-between font-mono text-xs mt-1.5 ${dark ? 'text-mint/70' : 'text-ink-3'}`}>{[0, 6, 12, 18, 23].map(h => <span key={h}>{hh(h)}</span>)}</div>
    </div>
  )
}

function SimBadge({ label, light }: { label: string; light?: boolean }) {
  return <span className={`text-sm italic ${light ? 'text-mint/70' : 'text-ink-3'}`}>{label}</span>
}

function Kicker({ children, light }: { children: ReactNode; light?: boolean }) {
  return <div className={`font-mono text-xs uppercase tracking-[0.18em] ${light ? 'text-mint' : 'text-accent'}`}>{children}</div>
}

function Hero({ demo, err, s, lang }: { demo: Demo | null; err: boolean; s: Strings; lang: Lang }) {
  const [hour, setHour] = useState(19); const [play, setPlay] = useState(true); const [sel, setSel] = useState<string | null>(null)
  useEffect(() => { if (!play || !demo) return; const id = setInterval(() => setHour(h => (h + 1) % 24), 1600); return () => clearInterval(id) }, [play, demo])
  const readout = useMemo(() => { if (!demo || !sel) return null; const c = zoneCurves(demo, sel, hour); const n = Math.round(c.net); return { name: ZONE_NAMES[sel][lang === 'fr' ? 0 : 1], p: Math.round(c.price), n } }, [demo, sel, hour, lang])
  return (
    <section id="marche" className="text-white" style={{ background: 'radial-gradient(1100px 700px at 75% 15%, #10493A 0%, #0B3D30 50%, #07241C 100%)' }}>
      {demo && <Ticker demo={demo} hour={hour} s={s} />}
      <div className="wrap grid lg:grid-cols-12 gap-x-12 gap-y-10 pt-14 pb-16 items-center">
        <div className="lg:col-span-5 min-w-0">
          <Kicker light>{s.kicker}</Kicker>
          <h1 className="font-display font-normal text-4xl md:text-6xl leading-[0.98] tracking-tight mt-5">{s.title_1} <em className="text-amber">{s.title_2}</em></h1>
          <p className="text-lg text-brand-ink mt-6 max-w-xl">{s.lead}</p>
          <div className="flex flex-wrap gap-3 mt-8">
            <Link to="/app" className="h-11 px-5 inline-flex items-center rounded bg-white text-brand font-medium hover:bg-brand-ink whitespace-nowrap">{s.cta_app}</Link>
            <a href="#explorer" className="h-11 px-5 inline-flex items-center rounded border border-white/30 text-white hover:bg-white/10 whitespace-nowrap">{s.cta_explore}</a>
          </div>
          {demo && <div className="font-mono text-xs text-mint/80 mt-8">{s.computed(demo.elapsed)}</div>}
        </div>
        <div className="lg:col-span-7 min-w-0">
          {demo ? (
            <>
              <NetworkMap theme="dark" prices={demo.prices} flows={demo.flows} ntc={demo.ntc} hour={hour} unit="$/MWh" selected={sel} onSelect={z => setSel(z === sel ? null : z)} />
              <div className="mt-4 flex items-center gap-4">
                <button onClick={() => setPlay(p => !p)} className="font-mono text-sm text-amber w-8 shrink-0" aria-label={play ? 'pause' : 'play'}>{play ? '❚❚' : '▶'}</button>
                <div className="flex-1 min-w-0"><HourStrip demo={demo} hour={hour} onPick={h => { setPlay(false); setHour(h) }} dark /></div>
                <div className="font-mono text-xl text-white w-14 text-right shrink-0">{hh(hour)}</div>
              </div>
              <p className="text-sm text-mint/70 mt-3">
                {readout ? <span className="text-white"><span className="text-amber">{sel}</span> {readout.name} · {readout.p} $/MWh · {readout.n > 1 ? `${s.ex_export} ${nf(readout.n)} MW` : readout.n < -1 ? `${s.ex_import} ${nf(-readout.n)} MW` : '± 0 MW'}</span> : s.map_hint}
              </p>
            </>
          ) : <div className="aspect-[560/340] flex items-center justify-center text-mint/70">{err ? s.demo_err : s.loading}</div>}
        </div>
      </div>
    </section>
  )
}

function CurveChart({ c, s }: { c: Curves; s: Strings }) {
  const W = 760, H = 400, Lm = 56, Rm = 24, Tm = 24, Bm = 44
  const totalS = c.sup.reduce((a, r) => a + r.qty, 0), totalD = c.dem.reduce((a, r) => a + r.qty, 0)
  const xMax = niceCeil(Math.max(totalS, totalD, c.demAt + Math.abs(c.net), 10) * 1.08)
  const yMax = niceCeil(Math.max(...c.sup.map(r => r.price), ...c.dem.map(r => r.price), c.price, 50) * 1.1)
  const X = (q: number) => Lm + (q / xMax) * (W - Lm - Rm), Y = (p: number) => Tm + (1 - p / yMax) * (H - Tm - Bm)
  const path = (segs: Seg[], endY: number) => { let x = 0; const d: string[] = []; segs.forEach((r, i) => { d.push(i === 0 ? `M${X(0)} ${Y(r.price)}` : `L${X(x)} ${Y(r.price)}`); x += r.qty; d.push(`L${X(x)} ${Y(r.price)}`) }); if (segs.length) d.push(`L${X(x)} ${endY}`); return d.join(' ') }
  const bx1 = X(Math.min(c.demAt, c.demAt + c.net)), bx2 = X(Math.max(c.demAt, c.demAt + c.net)); const by = Y(c.price)
  const netLabel = c.net > 1 ? `${s.ex_export} ${nf(Math.round(c.net))} MW` : c.net < -1 ? `${s.ex_import} ${nf(Math.round(-c.net))} MW` : null
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img">
      {ticks(yMax, 5).map(v => <g key={`y${v}`}><line x1={Lm} x2={W - Rm} y1={Y(v)} y2={Y(v)} stroke="#E2E0D9" /><text x={Lm - 8} y={Y(v) + 3.5} textAnchor="end" fontSize="11" fontFamily="JetBrains Mono, monospace" fill="#8C8B84">{nf(v)}</text></g>)}
      {ticks(xMax, 5).map(v => <text key={`x${v}`} x={X(v)} y={H - Bm + 18} textAnchor="middle" fontSize="11" fontFamily="JetBrains Mono, monospace" fill="#8C8B84">{nf(v)}</text>)}
      <text x={W - Rm} y={H - 6} textAnchor="end" fontSize="11" fill="#5C5B56">MW</text>
      <text x={Lm - 8} y={Tm - 8} textAnchor="end" fontSize="11" fill="#5C5B56">$/MWh</text>
      <path d={path(c.sup, Y(yMax))} fill="none" stroke="#0F6E56" strokeWidth={2.5} strokeLinejoin="round" />
      <path d={path(c.dem, Y(0))} fill="none" stroke="#B5443C" strokeWidth={2.5} strokeLinejoin="round" />
      <line x1={Lm} x2={W - Rm} y1={by} y2={by} stroke="#1B1B19" strokeDasharray="5 4" strokeWidth={1.2} />
      <text x={W - Rm - 4} y={by - 6} textAnchor="end" fontSize="12" fontFamily="JetBrains Mono, monospace" fill="#1B1B19">{`${s.ex_price} ${nf(c.price, 1)}`}</text>
      {netLabel && (() => {
        const narrow = bx2 - bx1 < 12
        const tw = netLabel.length * 7.2 + 18
        const right = bx2 + 14 + tw <= W - Rm
        const bx = right ? bx2 + 14 : bx1 - 14 - tw
        return (
          <g>
            {narrow
              ? <circle cx={(bx1 + bx2) / 2} cy={by} r={4.5} fill="#F2B134" stroke="#1B1B19" strokeWidth={1} />
              : <>
                  <line x1={bx1} x2={bx2} y1={by} y2={by} stroke="#F2B134" strokeWidth={4} strokeLinecap="round" />
                  <line x1={bx1} x2={bx1} y1={by - 6} y2={by + 6} stroke="#F2B134" strokeWidth={2} /><line x1={bx2} x2={bx2} y1={by - 6} y2={by + 6} stroke="#F2B134" strokeWidth={2} />
                </>}
            <line x1={right ? bx2 : bx1} x2={right ? bx + 2 : bx + tw - 2} y1={by} y2={by + 22} stroke="#8C8B84" strokeWidth={1} />
            <rect x={bx} y={by + 12} width={tw} height={22} rx={4} fill="#FFFFFF" stroke="#C8C6BE" />
            <text x={bx + tw / 2} y={by + 27} textAnchor="middle" fontSize="12" fontWeight="600" fill="#854F0B">{netLabel}</text>
          </g>
        )
      })()}
      <g fontSize="12" fill="#5C5B56">
        <line x1={Lm} x2={Lm + 22} y1={Tm + 2} y2={Tm + 2} stroke="#0F6E56" strokeWidth={3} /><text x={Lm + 28} y={Tm + 6}>{s.ex_supply}</text>
        <line x1={Lm + 150} x2={Lm + 172} y1={Tm + 2} y2={Tm + 2} stroke="#B5443C" strokeWidth={3} /><text x={Lm + 178} y={Tm + 6}>{s.ex_demand}</text>
      </g>
    </svg>
  )
}

function SegmentTable({ c, s }: { c: Curves; s: Strings }) {
  const status = (price: number, side: 'S' | 'D') => {
    const d = price - c.price
    if (Math.abs(d) <= 0.5) return ['bg-amber', s.ex_marginal]
    return (side === 'S' ? d < 0 : d > 0) ? ['bg-up', s.ex_accepted] : ['bg-line-strong', s.ex_rejected]
  }
  const Row = ({ r, side }: { r: Seg; side: 'S' | 'D' }) => { const [dot, label] = status(r.price, side); return (
    <tr><td className="pr-1"><span className={`inline-block w-2 h-2 rounded-full ${dot}`} /></td><td className="truncate" title={r.actor}>{r.actor}</td><td className="num">{nf(r.qty)}</td><td className="num">{nf(r.price)}</td><td className="text-xs text-ink-3 text-right whitespace-nowrap pr-0">{label}</td></tr>) }
  return (
    <div className="grid md:grid-cols-2 gap-x-10 gap-y-4 mt-6">
      {[['S', s.ex_supply, c.sup], ['D', s.ex_demand, c.dem]].map(([side, title, rows]) => (
        <div key={side as string} className="min-w-0">
          <div className="text-xs uppercase tracking-wide text-ink-3 font-medium mb-1">{title as string}</div>
          <table className="text-sm table-fixed w-full"><colgroup><col className="w-4" /><col /><col className="w-12" /><col className="w-14" /><col className="w-20" /></colgroup><thead><tr><th /><th>{s.ex_seg_title.split(' ')[0]}</th><th className="text-right">MW</th><th className="text-right">$/MWh</th><th /></tr></thead>
            <tbody>{(rows as Seg[]).slice(0, 9).map((r, i) => <Row key={i} r={r} side={side as 'S' | 'D'} />)}</tbody></table>
          {(rows as Seg[]).length > 9 && <div className="text-xs text-ink-3 mt-1">… {(rows as Seg[]).length - 9}</div>}
        </div>
      ))}
    </div>
  )
}

function Explorer({ demo, s, lang }: { demo: Demo; s: Strings; lang: Lang }) {
  const [zone, setZone] = useState('SEN'); const [hour, setHour] = useState(19)
  const c = useMemo(() => zoneCurves(demo, zone, hour), [demo, zone, hour])
  return (
    <section id="explorer" className="landing bg-page">
      <div className="wrap py-20">
        <div className="grid lg:grid-cols-12 gap-x-12 gap-y-10">
          <div className="lg:col-span-4 min-w-0">
            <Kicker>{s.ex_kicker}</Kicker>
            <h2 className="mt-4">{s.ex_title}</h2>
            <p className="text-ink-2 text-lg mt-5">{s.ex_lead}</p>
            <div className="mt-8 flex flex-wrap gap-1.5">
              {ZONES.map(z => <button key={z} onClick={() => setZone(z)} className={`h-8 px-2.5 rounded font-mono text-sm border transition-colors ${z === zone ? 'bg-brand text-white border-brand' : 'bg-surface text-ink-2 border-line hover:border-line-strong'}`}>{z}</button>)}
            </div>
            <div className="mt-6 flex items-center gap-4"><div className="flex-1 min-w-0"><HourStrip demo={demo} hour={hour} onPick={setHour} /></div><div className="font-mono text-xl w-14 text-right">{hh(hour)}</div></div>
            <p className="mt-8 text-base leading-relaxed text-ink border-l-2 border-amber pl-4">{sentence(c, zone, hour, lang)}</p>
          </div>
          <div className="lg:col-span-8 min-w-0">
            <div className="bg-surface border border-line rounded-lg p-4 md:p-6">
              <div className="flex items-center justify-between flex-wrap gap-2 mb-2"><span className="font-display text-2xl">{ZONE_NAMES[zone][lang === 'fr' ? 0 : 1]} <span className="font-mono text-sm text-ink-3">{zone} · {hh(hour)}</span></span><SimBadge label={s.sim_badge} /></div>
              <CurveChart c={c} s={s} />
              <SegmentTable c={c} s={s} />
            </div>
          </div>
        </div>
        <div className="mt-14 bg-surface border border-line rounded-lg p-6 md:p-8">
          <div className="flex items-center justify-between flex-wrap gap-3"><span className="font-display text-2xl">{s.src_title}</span><SimBadge label={s.sim_badge} /></div>
          <div className="grid md:grid-cols-3 gap-8 mt-6">
            {s.src_items.map(([k, v]) => <div key={k}><div className="font-mono text-xs uppercase tracking-wider text-accent">{k}</div><p className="text-ink-2 mt-2 leading-relaxed text-sm">{v}</p></div>)}
          </div>
          <p className="text-ink mt-6 leading-relaxed max-w-4xl">{s.src_note}</p>
          <a href={LINKS.data} target="_blank" rel="noreferrer" className="inline-block mt-3 text-accent font-medium hover:underline underline-offset-4">{s.src_link} →</a>
        </div>
        <div className="mt-14 border-t border-line pt-8">
          <div className="flex items-center justify-between flex-wrap gap-3"><span className="font-display text-2xl flex items-center gap-3">{s.ex_prices_title} <SimBadge label={s.sim_badge} /></span><span className="text-sm text-ink-3 max-w-xl">{s.ex_prices_hint}</span></div>
          <div className="mt-5"><PriceHeatmap prices={demo.prices} hours={demo.hours} highlight={zone} unit="$/MWh" lang={lang} onSelect={setZone} /></div>
        </div>
      </div>
    </section>
  )
}

function IntervalSketch({ s }: { s: Strings }) {
  return (
    <svg viewBox="0 0 300 64" className="w-full h-auto mt-5" role="img">
      <line x1="20" x2="280" y1="30" y2="30" stroke="#8FD3B5" strokeWidth="2" />
      <line x1="20" x2="20" y1="22" y2="38" stroke="#8FD3B5" strokeWidth="2" /><line x1="280" x2="280" y1="22" y2="38" stroke="#8FD3B5" strokeWidth="2" />
      <circle cx="150" cy="30" r="6" fill="#F2B134" />
      <g fontSize="10" fontFamily="JetBrains Mono, monospace" fill="#D7E8E1">
        <text x="20" y="54" textAnchor="start">{s.m_interval[0]}</text>
        <text x="150" y="16" textAnchor="middle" fill="#F2B134">{`p* ${s.m_interval[1]}`}</text>
        <text x="280" y="54" textAnchor="end">{s.m_interval[2]}</text>
      </g>
    </svg>
  )
}

export default function Landing() {
  const { lang } = useLang(); const s = L[lang]
  const [demo, setDemo] = useState<Demo | null>(null); const [err, setErr] = useState(false)
  useEffect(() => { fetch(`${BASE}/demo`).then(r => { if (!r.ok) throw new Error(); return r.json() }).then(setDemo).catch(() => setErr(true)) }, [])
  useEffect(() => { document.title = lang === 'fr' ? 'Simulateur de marché day-ahead du WAPP' : 'WAPP day-ahead market simulator' }, [lang])
  const ext = (href: string, children: ReactNode, cls = '') => <a href={href} target="_blank" rel="noreferrer" className={cls}>{children}</a>
  const docLinks = [LINKS.rules, LINKS.data, LINKS.architecture, LINKS.deploy, LINKS.github]
  const repo = LINKS.github.replace(/^https?:\/\//, '')

  return (
    <div className="min-h-screen landing">
      <header className="bg-brand text-white sticky top-0 z-10">
        <div className="wrap flex items-center justify-between h-16">
          <a href="#marche" className="flex items-center gap-3"><img src="/mark-light.svg" alt="" className="h-9 w-9" /><span className="font-display text-2xl whitespace-nowrap hidden sm:inline">WAPP DAM Simulator</span></a>
          <nav className="flex items-center gap-5 text-sm">
            {s.nav.map(([href, label]) => <a key={href} href={href} className="hidden lg:inline text-brand-ink hover:text-white">{label}</a>)}
            <Link to="/guide/formateur" className="hidden md:inline text-brand-ink hover:text-white">{s.nav_guides}</Link>
            <Link to="/app" className="h-9 px-4 inline-flex items-center rounded bg-amber text-deep font-medium whitespace-nowrap hover:bg-white">{s.nav_app}</Link>
            <LangToggle dark />
          </nav>
        </div>
      </header>

      <main>
        <Hero demo={demo} err={err} s={s} lang={lang} />
        {demo && <Explorer demo={demo} s={s} lang={lang} />}

        <section id="moteur" className="bg-brand text-white">
          <div className="wrap py-20 grid lg:grid-cols-12 gap-x-12 gap-y-10">
            <div className="lg:col-span-4"><Kicker light>{s.m_kicker}</Kicker><h2 className="mt-4 text-white">{s.m_title}</h2><p className="text-brand-ink text-lg mt-5">{s.m_lead}</p></div>
            <div className="lg:col-span-8 min-w-0">
              <ol className="grid md:grid-cols-3 gap-px bg-white/10 border border-white/10 rounded-lg overflow-hidden">
                {s.steps.map(([code, kind, q, txt], i) => (
                  <li key={code} className="bg-brand p-6">
                    <div className="flex items-baseline justify-between font-mono text-xs gap-3"><span className="text-amber">{code}</span><span className="text-mint/70 text-right">{kind}</span></div>
                    <div className="font-display text-3xl mt-4 leading-tight">{q}</div>
                    <p className="text-brand-ink mt-3 leading-relaxed text-sm">{txt}</p>
                    {i === 2 && <IntervalSketch s={s} />}
                  </li>
                ))}
              </ol>
              <p className="mt-6 text-sm text-mint/80 leading-relaxed">{s.m_note}</p>
            </div>
          </div>
        </section>

        <section id="fiche" className="bg-surface border-b border-line">
          <div className="wrap py-20 grid lg:grid-cols-12 gap-x-12 gap-y-10">
            <div className="lg:col-span-4"><Kicker>{s.f_kicker}</Kicker><h2 className="mt-4">{s.f_title}</h2><p className="text-ink-2 text-lg mt-5">{s.f_lead}</p></div>
            <dl className="lg:col-span-8 spec md:grid md:grid-cols-[180px_1fr] md:gap-x-8 border-t border-line">
              {s.spec.map(([k, v]) => <Fragment key={k}><dt>{k}</dt><dd>{v}</dd></Fragment>)}
            </dl>
          </div>
        </section>

        <section id="publics">
          <div className="wrap py-20">
            <h2>{s.w_title}</h2>
            <ol className="grid md:grid-cols-3 gap-x-12 gap-y-10 mt-10">
              {s.w.map(([h, p], i) => <li key={h} className="border-t border-line pt-5"><div className="font-mono text-xs text-accent">0{i + 1}</div><div className="font-display text-3xl mt-2">{h}</div><p className="text-ink-2 mt-3 leading-relaxed">{p}</p></li>)}
            </ol>
            <div className="mt-10 flex flex-wrap gap-6 text-base">
              <Link to="/guide/formateur" className="text-accent font-medium hover:underline underline-offset-4">{s.guide_trainer} →</Link>
              <Link to="/guide/trader" className="text-accent font-medium hover:underline underline-offset-4">{s.guide_trader} →</Link>
            </div>
          </div>
        </section>

        <section id="ouvert" className="bg-deep text-white">
          <div className="wrap py-20 grid lg:grid-cols-12 gap-x-12 gap-y-10">
            <div className="lg:col-span-5">
              <Kicker light>{s.o_kicker}</Kicker><h2 className="mt-4 text-white">{s.o_title}</h2><p className="text-brand-ink text-lg mt-5">{s.o_lead}</p>
              <ul className="mt-8">{s.o_links.map((label, i) => <li key={label}>{ext(docLinks[i], <><span>{label}</span><span className="font-mono text-mint/70">→</span></>, 'flex items-center justify-between border-b border-white/10 py-3 text-white hover:text-amber')}</li>)}</ul>
            </div>
            <div className="lg:col-span-7 min-w-0">
              <pre className="bg-black/40 border border-white/10 rounded-lg p-5 font-mono text-sm leading-6 overflow-x-auto text-brand-ink"><code>
<span className="text-amber">$</span> git clone https://{repo}.git && cd wapp-dam-simulator{'\n'}
<span className="text-amber">$</span> pip install -r requirements.txt && pytest -q{'\n'}
<span className="text-white">65 passed</span>{'\n'}
<span className="text-amber">$</span> python -m engine.cli --reference --out resultat.json --prices-csv prix.csv{'\n'}
<span className="text-white">welfare=22,317,910 volume=167,900 MWh elapsed=0.5s solver=appsi_highs</span>
              </code></pre>
              <p className="mt-4 text-sm text-mint/80 leading-relaxed">{s.o_note}</p>
            </div>
          </div>
        </section>

        <section id="avertissements" className="bg-surface border-b border-line">
          <div className="wrap py-16 grid lg:grid-cols-12 gap-x-12 gap-y-8">
            <div className="lg:col-span-4"><h2>{s.d_title}</h2></div>
            <div className="lg:col-span-8 grid md:grid-cols-2 gap-8"><p className="text-ink-2 leading-relaxed">{s.d1}</p><p className="text-ink-2 leading-relaxed">{s.d2}</p></div>
          </div>
        </section>

        <section id="auteurs">
          <div className="wrap py-16 grid lg:grid-cols-12 gap-x-12 gap-y-8">
            <div className="lg:col-span-4"><h2>{s.a_title}</h2></div>
            <div className="lg:col-span-8">
              <p className="text-ink leading-relaxed text-lg max-w-3xl">{s.a_text}</p>
              <div className="mt-5 flex flex-wrap gap-6 text-base">
                {LINKS.paper ? ext(LINKS.paper, s.a_paper_link + ' →', 'text-accent font-medium') : <span className="text-ink-3">{s.a_paper}</span>}
                {ext(LINKS.issues, s.contact + ' →', 'text-accent font-medium')}
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-line">
        <div className="wrap py-8 flex flex-wrap items-center justify-between gap-4 text-sm text-ink-3">
          <span>© 2026 Kodjovi Plakoo, Enrico Patanè · {s.footer}</span>
          <span className="flex gap-5">{ext(LINKS.licence, 'Apache 2.0')}{ext(LINKS.github, 'GitHub')}<Link to="/app">{s.nav_app}</Link></span>
        </div>
      </footer>
    </div>
  )
}
