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
import { AUTHORS, CONTRIBUTORS, SUPERVISORS, PARTNERS, TIMELINE, type Person, type Partner } from '../about'

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
    nav: [['#explorer', 'Comprendre'], ['#moteur', 'Le calcul'], ['#fiche', 'Fiche'], ['#ouvert', 'Code'], ['#apropos', 'À propos']] as [string, string][],
    nav_guides: 'Guides', nav_app: 'Essayer le simulateur',
    kicker: 'Simulateur ouvert · marché de l’électricité d’Afrique de l’Ouest',
    title: ['Comment quatorze pays fixeront, chaque jour,', 'le prix de leur électricité.'],
    lead: 'L’Afrique de l’Ouest doit ouvrir en 2027 un marché commun de l’électricité. Ce simulateur montre le calcul, étape par étape : qui vend, qui achète, à quel prix.',
    cta_app: 'Essayer le simulateur', cta_explore: 'Comprendre un prix',
    computed: (t: number) => `Calculé à l’instant par le moteur, en ${t.toFixed(2)} s, sur des données 2024 reconstituées.`,
    hand_map: 'cliquez un pays, changez d’heure',
    map_hint: 'Un cercle, un pays et son prix en $/MWh. En corail, les lignes pleines : de chaque côté, le prix n’est plus le même. Prix simulés, pas observés.',
    welfare: 'valeur créée', volume: 'énergie échangée', saturated: 'lignes pleines',
    loading: 'Le moteur calcule…', demo_err: 'Le serveur de démonstration ne répond pas.',
    ex_kicker: 'Comprendre un prix', ex_title: ['Pourquoi ce prix,', 'ici, à cette heure ?'],
    ex_lead: 'On range les centrales d’un pays de la moins chère à la plus chère : c’est la courbe verte. La demande est en rouge. Le prix se fixe à leur rencontre, corrigé de ce que les lignes laissent entrer ou sortir.',
    hand_ex: 'choisissez un pays, puis une heure',
    ex_cap: 'prix plafond : 500', ex_sup_end: 'production possible :', ex_dem_end: 'demande :', ex_supply: 'Offre des centrales', ex_demand: 'Demande', ex_price: 'prix du pays', ex_export: 'export', ex_import: 'import',
    ex_seg_title: 'Offres', ex_accepted: 'retenu', ex_marginal: 'fixe le prix', ex_rejected: 'non retenu',
    ex_prices_title: 'Les prix des quatorze pays, heure par heure', ex_prices_hint: 'Même couleur, même prix : ces pays forment un seul marché. Un trait sépare ceux qu’une ligne pleine isole. Cliquez un pays pour l’explorer.',
    m_kicker: 'Le calcul', m_title: ['Trois questions,', 'dans l’ordre.'],
    m_lead: 'Chaque jour, le marché répond à trois questions. Le moteur fait pareil, à livre ouvert.',
    steps: [
      ['1', 'P1 · optimisation', 'Qui est servi ?', 'On retient les échanges qui créent le plus de valeur, sans dépasser la capacité des lignes.'],
      ['2', 'P1bis · optimisation', 'Combien ?', 'À valeur égale, on échange le plus d’énergie possible.'],
      ['3', 'P2 · optimisation', 'À quel prix ?', 'Parmi tous les prix compatibles avec ces échanges, on retient celui du milieu.'],
    ] as [string, string, string, string][],
    m_interval: ['prix le plus bas possible', 'retenu', 'le plus haut'], m_note: 'Et les cas particuliers ? Une offre « tout ou rien » acceptée à perte est retirée, puis on recalcule. Deux offres au même prix se partagent la quantité. Tout est écrit dans les règles de marché.',
    f_kicker: 'Sous le capot', f_title: ['Ce qu’il y a', 'dans la boîte.'], f_lead: 'Un moteur de calcul, des salles de formation et des données, dans un seul dépôt.',
    spec: [
      ['Offres', 'Prix et quantité par tranche, avec un profil horaire : solaire, hydraulique, base, pointe'],
      ['Blocs', 'Offres « tout ou rien », liées entre elles ou exclusives'],
      ['Revenu minimum', 'Un vendeur peut exiger une recette minimale ; sinon ses offres sont retirées'],
      ['Départage', 'Valeur créée, puis énergie échangée, puis prix du milieu ; à prix égal, partage au prorata'],
      ['Réseau', '14 pays, 15 lignes, capacités modifiables par salle'],
      ['Données', 'Scénario 2024 reconstitué de sources publiques, et quatre variantes : sécheresse, ligne coupée, gaz cher, forte demande'],
      ['Vérifications', '67 tests automatiques et une campagne de cas aléatoires'],
      ['Accès', 'Salles en ligne, API documentée, ligne de commande, exports CSV et JSON, français et anglais'],
      ['Solveur', 'HiGHS, libre et inclus ; Gurobi s’il est installé'],
      ['Licence', 'Apache 2.0 pour le code, CC BY 4.0 pour les données'],
    ] as [string, string][],
    w_title: ['Trois façons', 'de s’en servir.'],
    w: [
      ['Former', 'Une séance en trois manches. Chacun représente un pays, dépose ses offres, découvre son résultat.'],
      ['Étudier', 'Des règles écrites, un cas-test public, un moteur ouvert : de quoi travailler sur les prix et les blocs.'],
      ['Comparer', 'Rejouez un cas et confrontez le résultat à celui d’une autre plateforme, avant le lancement du marché.'],
    ] as [string, string][],
    guide_trainer: 'Guide du formateur', guide_trader: 'Guide du trader',
    o_kicker: 'Code ouvert', o_title: ['Rien à croire', 'sur parole.'],
    o_lead: 'Le code, les règles et les données sont publics. Trois commandes suffisent pour tout refaire chez vous.',
    o_links: ['Fiche technique', 'Règles de marché', 'Données de référence', 'Architecture', 'Déploiement', 'Dépôt GitHub'],
    o_note: 'Vous devez retrouver exactement ces chiffres : valeur créée 22 317 910, énergie échangée 167 900 MWh.',
    d_title: 'À savoir',
    d1: 'Ce simulateur est un outil pédagogique indépendant. Il n’est affilié ni au West African Power Pool, ni à son centre de coordination, ni à un fournisseur de plateforme. « WAPP » et « West African Power Pool » appartiennent au WAPP.',
    d2: 'Les prix affichés sont simulés sur des données reconstituées de sources publiques. Ce ne sont pas des prix observés : le marché n’a pas encore démarré. À utiliser pour former et étudier, pas pour exploiter un réseau.',
    a_kicker: 'À propos', a_title: ['Qui est derrière', 'ce simulateur ?'],
    a_p: [
      'Ce simulateur est né d’un projet de groupe du Mastère Spécialisé OSE de Mines Paris – PSL. SENELEC nous a proposé le sujet : refaire, pour le comprendre, le calcul qui fixera les prix du futur marché ouest-africain.',
      'Le projet a réuni cinq étudiants de la promotion 2025. Nous deux, Kodjovi et Enrico, avons écrit le moteur et l’application, livrés au printemps 2026, et nous continuons de les faire évoluer : règles de prix complètes, données 2024, mise en ligne.',
      'Tout est en accès libre, parce qu’un marché se comprend mieux quand on peut refaire le calcul soi-même. Vous formez, vous exploitez, vous régulez ou vous cherchez ? Écrivez-nous.',
    ],
    sign: 'Kodjovi & Enrico',
    a_authors: 'Auteurs du simulateur', a_contrib: 'Groupe projet du Mastère', a_sup: 'Encadrement',
    p_title: 'Cadre du projet',
    p_note: 'Projet mené au Mastère Spécialisé OSE (Centre de Mathématiques Appliquées, Mines Paris – PSL), avec SENELEC. Ces institutions ont accueilli ou encadré le projet ; elles ne répondent pas du contenu du site.',
    v_kicker: 'En vidéo', v_title: 'Le simulateur en deux minutes',
    a_paper: 'Note technique à paraître.', a_paper_link: 'Lire la note technique', contact: 'Questions et contributions',
    footer: 'Simulateur pédagogique indépendant, non affilié au WAPP.',
    sim_badge: 'Simulation sur des données 2024 reconstituées',
    src_title: 'D’où viennent ces chiffres ?',
    src_items: [
      ['Sourcé', 'Les centrales et les capacités de chaque pays, plusieurs lignes, le prix du gaz au Nigeria et au Ghana : rapports publics, cités un par un.'],
      ['Estimé', 'La demande de pointe de plusieurs pays, la capacité des lignes sans chiffre publié, les profils horaires.'],
      ['Supposé', 'Le prix des offres : nous prenons le coût typique de chaque technologie. Ce ne sont pas les offres réelles des acteurs.'],
    ] as [string, string][],
    src_note: 'Le marché n’a pas encore démarré : il n’existe pas de prix réels à comparer. Le niveau des prix dépend de nos hypothèses ; qui importe et quelles lignes saturent dépend surtout des capacités des lignes, à valider avec le WAPP.',
    src_link: 'Toutes les sources, ligne par ligne',
  },
  en: {
    nav: [['#explorer', 'Understand'], ['#moteur', 'The maths'], ['#fiche', 'Spec sheet'], ['#ouvert', 'Code'], ['#apropos', 'About']] as [string, string][],
    nav_guides: 'Guides', nav_app: 'Try the simulator',
    kicker: 'Open simulator · West African electricity market',
    title: ['How fourteen countries will set, every day,', 'the price of their electricity.'],
    lead: 'West Africa is due to open a common electricity market in 2027. This simulator shows the computation, step by step: who sells, who buys, at what price.',
    cta_app: 'Try the simulator', cta_explore: 'Understand a price',
    computed: (t: number) => `Computed just now by the engine, in ${t.toFixed(2)} s, on reconstructed 2024 data.`,
    hand_map: 'click a country, change the hour',
    map_hint: 'One circle, one country and its price in $/MWh. In coral, the full lines: the price is no longer the same on either side. Simulated prices, not observed ones.',
    welfare: 'value created', volume: 'energy traded', saturated: 'full lines',
    loading: 'The engine is computing…', demo_err: 'The demonstration server is not responding.',
    ex_kicker: 'Understand a price', ex_title: ['Why this price,', 'here, at this hour?'],
    ex_lead: 'Line up a country’s plants from cheapest to most expensive: that is the green curve. Demand is in red. The price settles where they meet, adjusted for what the lines let in or out.',
    hand_ex: 'pick a country, then an hour',
    ex_cap: 'price cap: 500', ex_sup_end: 'possible output:', ex_dem_end: 'demand:', ex_supply: 'Supply from plants', ex_demand: 'Demand', ex_price: 'country price', ex_export: 'export', ex_import: 'import',
    ex_seg_title: 'Orders', ex_accepted: 'accepted', ex_marginal: 'sets the price', ex_rejected: 'not accepted',
    ex_prices_title: 'The prices of the fourteen countries, hour by hour', ex_prices_hint: 'Same colour, same price: those countries form a single market. A rule separates the ones a full line isolates. Click a country to explore it.',
    m_kicker: 'The maths', m_title: ['Three questions,', 'in order.'],
    m_lead: 'Every day, the market answers three questions. The engine does the same, with the book open.',
    steps: [
      ['1', 'P1 · optimisation', 'Who is served?', 'Keep the trades that create the most value, without exceeding line capacities.'],
      ['2', 'P1bis · optimisation', 'How much?', 'At equal value, trade as much energy as possible.'],
      ['3', 'P2 · optimisation', 'At what price?', 'Among all prices consistent with those trades, take the one in the middle.'],
    ] as [string, string, string, string][],
    m_interval: ['lowest possible price', 'chosen', 'highest'], m_note: 'And the special cases? An “all or nothing” order accepted at a loss is removed, then we recompute. Two orders at the same price share the quantity. Everything is written in the market rules.',
    f_kicker: 'Under the hood', f_title: ['What is', 'in the box.'], f_lead: 'A clearing engine, training rooms and data, in a single repository.',
    spec: [
      ['Orders', 'Price and quantity by tranche, with an hourly profile: solar, hydro, baseload, peaking'],
      ['Blocks', '“All or nothing” orders, linked to one another or exclusive'],
      ['Minimum income', 'A seller can require a minimum income; otherwise its orders are withdrawn'],
      ['Tie-break', 'Value created, then energy traded, then the middle price; equal prices shared pro rata'],
      ['Network', '14 countries, 15 lines, capacities editable per room'],
      ['Data', '2024 scenario rebuilt from public sources, and four variants: drought, line out, expensive gas, high demand'],
      ['Checks', '67 automated tests and a campaign of random cases'],
      ['Access', 'Online rooms, documented API, command line, CSV and JSON exports, French and English'],
      ['Solver', 'HiGHS, open source and included; Gurobi when installed'],
      ['Licence', 'Apache 2.0 for the code, CC BY 4.0 for the data'],
    ] as [string, string][],
    w_title: ['Three ways', 'to use it.'],
    w: [
      ['Train', 'A three-round session. Everyone represents a country, submits orders and discovers their result.'],
      ['Study', 'Written rules, a public test case, an open engine: material to work on prices and blocks.'],
      ['Compare', 'Replay a case and confront the result with another platform’s, before the market opens.'],
    ] as [string, string][],
    guide_trainer: 'Trainer guide', guide_trader: 'Trader guide',
    o_kicker: 'Open code', o_title: ['Nothing to take', 'on faith.'],
    o_lead: 'The code, the rules and the data are public. Three commands are enough to redo everything at home.',
    o_links: ['Technical sheet', 'Market rules', 'Reference data', 'Architecture', 'Deployment', 'GitHub repository'],
    o_note: 'You should get exactly these figures: value created 22,317,910, energy traded 167,900 MWh.',
    d_title: 'Good to know',
    d1: 'This simulator is an independent educational tool. It is not affiliated with the West African Power Pool, its coordination centre or any platform vendor. “WAPP” and “West African Power Pool” belong to the WAPP.',
    d2: 'The prices shown are simulated on data rebuilt from public sources. They are not observed prices: the market has not started yet. Use it to train and to study, not to operate a network.',
    a_kicker: 'About', a_title: ['Who is behind', 'this simulator?'],
    a_p: [
      'This simulator grew out of a group project of the Advanced Master OSE at Mines Paris – PSL. SENELEC gave us the subject: redo, in order to understand it, the computation that will set the prices of the future West African market.',
      'The project brought together five students of the class of 2025. The two of us, Kodjovi and Enrico, wrote the engine and the application, delivered in the spring of 2026, and we keep developing them: complete pricing rules, 2024 data, an online site.',
      'Everything is open access, because a market is better understood when you can redo the computation yourself. You train, operate, regulate or research? Write to us.',
    ],
    sign: 'Kodjovi & Enrico',
    a_authors: 'Authors of the simulator', a_contrib: 'Master’s project group', a_sup: 'Supervision',
    p_title: 'Project framework',
    p_note: 'Project carried out at the Advanced Master OSE (Centre for Applied Mathematics, Mines Paris – PSL), with SENELEC. These institutions hosted or supervised the project; they are not responsible for the content of this site.',
    v_kicker: 'On video', v_title: 'The simulator in two minutes',
    a_paper: 'Technical note forthcoming.', a_paper_link: 'Read the technical note', contact: 'Questions and contributions',
    footer: 'Independent educational simulator, not affiliated with the WAPP.',
    sim_badge: 'Simulation on reconstructed 2024 data',
    src_title: 'Where do these figures come from?',
    src_items: [
      ['Sourced', 'The plants and capacities of each country, several lines, the gas price in Nigeria and Ghana: public reports, cited one by one.'],
      ['Estimated', 'The peak demand of several countries, the capacity of lines with no published figure, the hourly profiles.'],
      ['Assumed', 'The order prices: we take the typical cost of each technology. These are not the actors’ real bids.'],
    ] as [string, string][],
    src_note: 'The market has not started yet: there are no real prices to compare with. Price levels depend on our assumptions; who imports and which lines fill up depends mostly on line capacities, to be validated with the WAPP.',
    src_link: 'All the sources, line by line',
  },
}
/** French typography: non-breaking spaces before ? ! : ; » and after «, so that punctuation never wraps alone. */
const frTypo = (x: unknown): unknown =>
  typeof x === 'string' ? x.replace(/ ([?!:;»])/g, '\u00a0$1').replace(/« /g, '«\u00a0')
    : Array.isArray(x) ? x.map(frTypo)
    : typeof x === 'function' ? (...a: unknown[]) => frTypo((x as (...b: unknown[]) => unknown)(...a)) : x
L.fr = Object.fromEntries(Object.entries(L.fr).map(([k, v]) => [k, k === 'nav' ? v : frTypo(v)])) as typeof L.fr
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
  const fr = lang === 'fr'; const name = ZONE_NAMES[zone][fr ? 0 : 1]; const p = Math.round(c.price); const n = Math.round(c.net)
  const plant = c.sup.find(r => Math.abs(r.price - c.price) <= 0.5); const load = c.dem.find(r => Math.abs(r.price - c.price) <= 0.5)
  const full = c.lines.filter(l => l.sat).map(l => `${zone}–${l.other}`)
  if (fr) {
    const trade = n > 1 ? `Le pays exporte ${nf(n)} MW.` : n < -1 ? `Le pays importe ${nf(-n)} MW.` : 'Le pays n’échange presque rien avec ses voisins.'
    const why = plant ? `La dernière centrale appelée, ${plant.actor}, demande ${p} $/MWh : c’est elle qui fixe le prix.`
      : load ? 'Ici, c’est la demande qui fixe le prix : la dernière tranche servie paie exactement ce montant.'
      : 'Ce prix vient d’un pays voisin : aucune ligne pleine ne les sépare, ils forment un seul marché.'
    const lines = full.length ? ` ${full.length > 1 ? 'Lignes pleines' : 'Ligne pleine'} : ${full.join(', ')}.` : ''
    return frTypo(`${name}, ${hour} h : ${p} $/MWh. ${trade} ${why}${lines}`) as string
  }
  const trade = n > 1 ? `The country exports ${nf(n)} MW.` : n < -1 ? `The country imports ${nf(-n)} MW.` : 'The country trades almost nothing with its neighbours.'
  const why = plant ? `The last plant called, ${plant.actor}, asks ${p} $/MWh: it sets the price.`
    : load ? 'Here demand sets the price: the last tranche served pays exactly that amount.'
    : 'This price comes from a neighbouring country: no full line separates them, they form a single market.'
  const lines = full.length ? ` Full line${full.length > 1 ? 's' : ''}: ${full.join(', ')}.` : ''
  return `${name}, ${String(hour).padStart(2, '0')}:00: ${p} $/MWh. ${trade} ${why}${lines}`
}

const niceCeil = (v: number) => { const pow = Math.pow(10, Math.floor(Math.log10(Math.max(v, 1)))); const f = v / pow; const m = [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10].find(k => f <= k) ?? 10; return m * pow }
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
    <section id="marche" className="text-white" style={{ background: 'url(/patterns/topo-dark.svg) center / cover no-repeat, radial-gradient(1100px 700px at 75% 15%, #10493A 0%, #0B3D30 50%, #07241C 100%)' }}>
      {demo && <Ticker demo={demo} hour={hour} s={s} />}
      <div className="wrap grid lg:grid-cols-12 gap-x-12 gap-y-10 pt-14 pb-16 items-center">
        <div className="lg:col-span-5 min-w-0">
          <Kicker light>{s.kicker}</Kicker>
          <h1 className="font-display font-normal text-4xl md:text-6xl leading-[0.98] tracking-tight mt-5">{s.title[0]} <em className="text-amber">{s.title[1]}</em></h1>
          <p className="font-display text-xl md:text-2xl leading-snug text-white/90 mt-6 max-w-xl">{s.lead}</p>
          <div className="flex flex-wrap gap-3 mt-8">
            <Link to="/app" className="h-11 px-5 inline-flex items-center rounded bg-white text-brand font-medium hover:bg-brand-ink whitespace-nowrap">{s.cta_app}</Link>
            <a href="#explorer" className="h-11 px-5 inline-flex items-center rounded border border-white/30 text-white hover:bg-white/10 whitespace-nowrap">{s.cta_explore}</a>
          </div>
          {demo && <div className="font-mono text-xs text-mint/80 mt-8">{s.computed(demo.elapsed)}</div>}
        </div>
        <div className="lg:col-span-7 min-w-0">
          {demo ? (
            <>
              <div className="font-hand text-2xl text-amber text-right pr-3 -mb-1 hidden sm:block" style={{ transform: 'rotate(-1.5deg)' }}>{s.hand_map} ↓</div>
              <NetworkMap theme="dark" lang={lang} prices={demo.prices} flows={demo.flows} ntc={demo.ntc} hour={hour} unit="$/MWh" selected={sel} onSelect={z => setSel(z === sel ? null : z)} />
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
  const W = 760, H = 460, Lm = 56, Rm = 24, Tm = 24, Bm = 44
  const totalS = c.sup.reduce((a, r) => a + r.qty, 0), totalD = c.dem.reduce((a, r) => a + r.qty, 0)
  const xMax = niceCeil(Math.max(totalS, totalD, c.demAt + Math.abs(c.net), 10) * 1.08)
  const yMax = 500   // regulatory price bounds of the market: the same frame for every zone
  const X = (q: number) => Lm + (q / xMax) * (W - Lm - Rm), Y = (p: number) => Tm + (1 - p / yMax) * (H - Tm - Bm)
  const path = (segs: Seg[]) => { let x = 0; const d: string[] = []; segs.forEach((r, i) => { d.push(i === 0 ? `M${X(0)} ${Y(r.price)}` : `L${X(x)} ${Y(r.price)}`); x += r.qty; d.push(`L${X(x)} ${Y(r.price)}`) }); return d.join(' ') }
  const lastS = c.sup.length ? c.sup[c.sup.length - 1].price : 0, lastD = c.dem.length ? c.dem[c.dem.length - 1].price : 0
  const endLabel = (q: number, label: string) => { const x = X(q); const right = x + 150 <= W - Rm; return { x: right ? x + 6 : x - 6, anchor: right ? 'start' : 'end', text: `${label} ${nf(q)} MW` } }
  const sEnd = endLabel(totalS, s.ex_sup_end), dEnd = endLabel(totalD, s.ex_dem_end)
  const bx1 = X(Math.min(c.demAt, c.demAt + c.net)), bx2 = X(Math.max(c.demAt, c.demAt + c.net)); const by = Y(c.price)
  const netLabel = c.net > 1 ? `${s.ex_export} ${nf(Math.round(c.net))} MW` : c.net < -1 ? `${s.ex_import} ${nf(Math.round(-c.net))} MW` : null
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img">
      {ticks(yMax, 5).map(v => <g key={`y${v}`}><line x1={Lm} x2={W - Rm} y1={Y(v)} y2={Y(v)} stroke="#E2E0D9" /><text x={Lm - 8} y={Y(v) + 3.5} textAnchor="end" fontSize="11" fontFamily="JetBrains Mono, monospace" fill="#8C8B84">{nf(v)}</text></g>)}
      {ticks(xMax, 5).map(v => <text key={`x${v}`} x={X(v)} y={H - Bm + 18} textAnchor="middle" fontSize="11" fontFamily="JetBrains Mono, monospace" fill="#8C8B84">{nf(v)}</text>)}
      <text x={W - Rm} y={H - 6} textAnchor="end" fontSize="11" fill="#5C5B56">MW</text>
      <text x={Lm - 8} y={Tm - 8} textAnchor="end" fontSize="11" fill="#5C5B56">$/MWh</text>
      <text x={W - Rm} y={Y(yMax) - 6} textAnchor="end" fontSize="11" fill="#8C8B84">{s.ex_cap}</text>
      <path d={path(c.sup)} fill="none" stroke="#0F6E56" strokeWidth={2.5} strokeLinejoin="round" />
      <path d={path(c.dem)} fill="none" stroke="#B5443C" strokeWidth={2.5} strokeLinejoin="round" />
      {c.sup.length > 0 && <>
        <line x1={X(totalS)} x2={X(totalS)} y1={Y(lastS)} y2={Y(yMax)} stroke="#0F6E56" strokeWidth={1.5} strokeDasharray="4 4" />
        <text x={sEnd.x} y={Tm + 14} textAnchor={sEnd.anchor as 'start' | 'end'} fontSize="11" fill="#0F6E56">{sEnd.text}</text>
      </>}
      {c.dem.length > 0 && <>
        <line x1={X(totalD)} x2={X(totalD)} y1={Y(lastD)} y2={Y(0)} stroke="#B5443C" strokeWidth={1.5} strokeDasharray="4 4" />
        <text x={dEnd.x} y={Y(0) - 8} textAnchor={dEnd.anchor as 'start' | 'end'} fontSize="11" fill="#B5443C">{dEnd.text}</text>
      </>}
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
          <table className="text-sm table-fixed w-full"><colgroup><col className="w-4" /><col /><col className="w-12" /><col className="w-14" /><col className="w-20" /></colgroup><thead><tr><th /><th>{s.ex_seg_title}</th><th className="text-right">MW</th><th className="text-right">$/MWh</th><th /></tr></thead>
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
    <section id="explorer" className="landing bg-surface border-b border-line">
      <div className="wrap py-20">
        <div className="grid lg:grid-cols-12 gap-x-16 gap-y-10">
          <div className="lg:col-span-5 min-w-0">
            <Kicker>{s.ex_kicker}</Kicker>
            <h2 className="mt-4">{s.ex_title[0]} <em className="text-accent">{s.ex_title[1]}</em></h2>
            <p className="font-display text-xl leading-snug text-ink mt-5">{s.ex_lead}</p>
            <div className="font-hand text-2xl text-accent mt-7 -mb-1" style={{ transform: 'rotate(-1deg)', transformOrigin: 'left' }}>{s.hand_ex} ↓</div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {ZONES.map(z => <button key={z} onClick={() => setZone(z)} className={`h-8 px-2.5 rounded font-mono text-sm border transition-colors ${z === zone ? 'bg-brand text-white border-brand' : 'bg-surface text-ink-2 border-line hover:border-line-strong'}`}>{z}</button>)}
            </div>
            <div className="mt-6 flex items-center gap-4"><div className="flex-1 min-w-0"><HourStrip demo={demo} hour={hour} onPick={setHour} /></div><div className="font-mono text-xl w-14 text-right">{hh(hour)}</div></div>
            <p className="mt-8 text-base leading-relaxed text-ink border-l-2 border-amber pl-4">{sentence(c, zone, hour, lang)}</p>
          </div>
          <div className="lg:col-span-7 min-w-0">
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

function Avatar({ p, size }: { p: Person; size: number }) {
  const [loaded, setLoaded] = useState(false)
  const words = p.name.split(/\s+/); const initials = (words[0][0] + words[words.length - 1][0]).toUpperCase()
  return (
    <span className="relative inline-flex shrink-0 rounded-full overflow-hidden bg-brand text-white font-display items-center justify-center" style={{ width: size, height: size, fontSize: size * 0.36 }}>
      {!loaded && <span aria-hidden>{initials}</span>}
      {p.photo && <img src={p.photo} alt={p.name} onLoad={() => setLoaded(true)} className={loaded ? 'absolute inset-0 w-full h-full object-cover' : 'hidden'} />}
    </span>
  )
}

function PartnerMark({ p }: { p: Partner }) {
  const [loaded, setLoaded] = useState(false)
  return (
    <a href={p.url} target="_blank" rel="noreferrer" className="flex items-center justify-center min-h-20 text-center text-ink-2 hover:text-ink">
      {!loaded && <span className="font-display text-xl leading-tight">{p.name}</span>}
      {p.logo && <img src={p.logo} alt={p.name} onLoad={() => setLoaded(true)} className={loaded ? 'max-h-14 md:max-h-20 max-w-full object-contain' : 'hidden'} />}
    </a>
  )
}

function About({ s, lang }: { s: Strings; lang: Lang }) {
  const i = lang === 'fr' ? 0 : 1
  const small = (p: Person) => (
    <li key={p.name} className="flex items-center gap-3 py-2.5 border-b border-line last:border-b-0">
      <Avatar p={p} size={40} /><div className="min-w-0"><div className="font-medium text-ink truncate">{p.name}</div><div className="text-sm text-ink-3 truncate">{p.role[i]} · {p.org}</div></div>
    </li>
  )
  return (
    <section id="apropos" className="bg-page" style={{ backgroundImage: 'url(/patterns/mesh-light.svg)', backgroundSize: 'cover', backgroundPosition: 'center' }}>
      <div className="wrap py-20 grid lg:grid-cols-12 gap-x-16 gap-y-12">
        <div className="lg:col-span-6 min-w-0">
          <Kicker>{s.a_kicker}</Kicker>
          <h2 className="mt-4">{s.a_title[0]} <em className="text-accent">{s.a_title[1]}</em></h2>
          <p className="font-display text-xl md:text-2xl leading-snug text-ink mt-6">{s.a_p[0]}</p>
          <p className="text-ink-2 leading-relaxed mt-4">{s.a_p[1]}</p>
          <p className="text-ink-2 leading-relaxed mt-4">{s.a_p[2]}</p>
          <div className="font-hand text-4xl text-accent mt-5" style={{ transform: 'rotate(-2deg)', transformOrigin: 'left' }}>{s.sign}</div>
          <div className="mt-6 flex flex-wrap gap-6 text-base">
            {LINKS.contact && <a href={`mailto:${LINKS.contact}`} className="text-accent font-medium">{LINKS.contact}</a>}
            <a href={LINKS.issues} target="_blank" rel="noreferrer" className="text-accent font-medium">{s.contact} →</a>
            {LINKS.paper ? <a href={LINKS.paper} target="_blank" rel="noreferrer" className="text-accent font-medium">{s.a_paper_link} →</a> : <span className="text-ink-3">{s.a_paper}</span>}
          </div>
          <ol className="mt-10 border-l border-line-strong">
            {TIMELINE.map(([date, fr, en]) => (
              <li key={date} className="relative pl-6 pb-5 last:pb-0">
                <span className="absolute -left-[5px] top-1.5 w-[9px] h-[9px] rounded-full bg-accent" />
                <div className="font-mono text-xs text-ink-3">{date}</div><div className="text-ink">{lang === 'fr' ? fr : en}</div>
              </li>
            ))}
          </ol>
        </div>
        <div className="lg:col-span-6 min-w-0">
          <div className="text-xs uppercase tracking-wide text-ink-3 font-medium mb-4">{s.a_authors}</div>
          <div className="grid sm:grid-cols-2 gap-6">
            {AUTHORS.map(p => (
              <div key={p.name} className="bg-surface border border-line rounded-lg p-5 min-w-0">
                <Avatar p={p} size={96} />
                <div className="font-display text-2xl mt-4 leading-tight">{p.name}</div>
                <div className="text-ink-2 mt-1">{p.role[i]}</div>
                <div className="text-sm text-ink-3 mt-1">{p.org}</div>
                {p.linkedin && <a href={p.linkedin} target="_blank" rel="noreferrer" className="inline-block mt-3 text-accent text-sm font-medium">LinkedIn →</a>}
              </div>
            ))}
          </div>
          <div className="grid sm:grid-cols-2 gap-x-8 gap-y-8 mt-8">
            <div className="min-w-0"><div className="text-xs uppercase tracking-wide text-ink-3 font-medium mb-1">{s.a_sup}</div><ul>{SUPERVISORS.map(small)}</ul></div>
            <div className="min-w-0"><div className="text-xs uppercase tracking-wide text-ink-3 font-medium mb-1">{s.a_contrib}</div><ul>{CONTRIBUTORS.map(small)}</ul></div>
          </div>
        </div>
      </div>
    </section>
  )
}

function Partners({ s }: { s: Strings }) {
  return (
    <section id="cadre" className="bg-surface border-t border-line">
      <div className="wrap py-12">
        <div className="font-mono text-xs uppercase tracking-[0.18em] text-ink-3">{s.p_title}</div>
        <div className="grid grid-cols-3 gap-x-6 md:gap-x-16 items-center mt-6 max-w-3xl">{PARTNERS.map(p => <PartnerMark key={p.name} p={p} />)}</div>
        <p className="text-sm text-ink-3 mt-8 max-w-4xl leading-relaxed">{s.p_note}</p>
      </div>
    </section>
  )
}

function VideoSection({ s }: { s: Strings }) {
  const url = LINKS.video; if (!url) return null
  const file = /\.(mp4|webm)$/i.test(url)
  return (
    <section id="video" className="bg-deep text-white">
      <div className="wrap py-16 grid lg:grid-cols-12 gap-x-12 gap-y-8 items-center">
        <div className="lg:col-span-4"><Kicker light>{s.v_kicker}</Kicker><h2 className="mt-4 text-white">{s.v_title}</h2></div>
        <div className="lg:col-span-8"><div className="aspect-video rounded-lg overflow-hidden border border-white/10 bg-black">
          {file ? <video src={url} controls preload="metadata" className="w-full h-full" /> : <iframe src={url} title={s.v_title} allow="accelerometer; encrypted-media; picture-in-picture" allowFullScreen className="w-full h-full" />}
        </div></div>
      </div>
    </section>
  )
}

export default function Landing() {
  const { lang } = useLang(); const s = L[lang]
  const [demo, setDemo] = useState<Demo | null>(null); const [err, setErr] = useState(false)
  useEffect(() => { fetch(`${BASE}/demo`).then(r => { if (!r.ok) throw new Error(); return r.json() }).then(setDemo).catch(() => setErr(true)) }, [])
  useEffect(() => { document.title = lang === 'fr' ? 'Simulateur de marché day-ahead du WAPP' : 'WAPP day-ahead market simulator' }, [lang])
  const ext = (href: string, children: ReactNode, cls = '') => <a href={href} target="_blank" rel="noreferrer" className={cls}>{children}</a>
  const docLinks = [lang === 'fr' ? LINKS.sheet_fr : LINKS.sheet, LINKS.rules, LINKS.data, LINKS.architecture, LINKS.deploy, LINKS.github]
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
        <VideoSection s={s} />
        {demo && <Explorer demo={demo} s={s} lang={lang} />}

        <section id="moteur" className="bg-brand text-white" style={{ backgroundImage: 'url(/patterns/mesh-dark.svg)', backgroundSize: 'cover', backgroundPosition: 'center' }}>
          <div className="wrap py-20 grid lg:grid-cols-12 gap-x-12 gap-y-10">
            <div className="lg:col-span-4"><Kicker light>{s.m_kicker}</Kicker><h2 className="mt-4 text-white">{s.m_title[0]} <em className="text-amber">{s.m_title[1]}</em></h2><p className="font-display text-xl leading-snug text-white/90 mt-5">{s.m_lead}</p></div>
            <div className="lg:col-span-8 min-w-0">
              <ol className="grid md:grid-cols-3 gap-px bg-white/10 border border-white/10 rounded-lg overflow-hidden">
                {s.steps.map(([code, kind, q, txt], i) => (
                  <li key={code} className="bg-brand p-6">
                    <div className="flex items-start justify-between gap-3"><span className="font-display text-6xl leading-[0.8] text-amber">{code}</span><span className="font-mono text-xs text-mint/70 text-right">{kind}</span></div>
                    <div className="font-display text-3xl mt-5 leading-tight">{q}</div>
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
            <div className="lg:col-span-4"><Kicker>{s.f_kicker}</Kicker><h2 className="mt-4">{s.f_title[0]} <em className="text-accent">{s.f_title[1]}</em></h2><p className="font-display text-xl leading-snug text-ink mt-5">{s.f_lead}</p></div>
            <dl className="lg:col-span-8 spec md:grid md:grid-cols-[180px_1fr] md:gap-x-8 border-t border-line">
              {s.spec.map(([k, v]) => <Fragment key={k}><dt>{k}</dt><dd>{v}</dd></Fragment>)}
            </dl>
          </div>
        </section>

        <section id="publics" style={{ backgroundImage: 'url(/patterns/topo-light.svg)', backgroundSize: 'cover', backgroundPosition: 'center' }}>
          <div className="wrap py-20">
            <h2>{s.w_title[0]} <em className="text-accent">{s.w_title[1]}</em></h2>
            <ol className="grid md:grid-cols-3 gap-x-12 gap-y-10 mt-10">
              {s.w.map(([h, p], i) => <li key={h} className="border-t border-line pt-5"><div className="font-mono text-xs text-accent">0{i + 1}</div><div className="font-display text-3xl mt-2">{h}</div><p className="text-ink-2 mt-3 leading-relaxed">{p}</p></li>)}
            </ol>
            <div className="mt-10 flex flex-wrap gap-6 text-base">
              <Link to="/guide/formateur" className="text-accent font-medium hover:underline underline-offset-4">{s.guide_trainer} →</Link>
              <Link to="/guide/trader" className="text-accent font-medium hover:underline underline-offset-4">{s.guide_trader} →</Link>
            </div>
          </div>
        </section>

        <section id="ouvert" className="bg-deep text-white" style={{ backgroundImage: 'url(/patterns/topo-dark.svg)', backgroundSize: 'cover', backgroundPosition: 'center' }}>
          <div className="wrap py-20 grid lg:grid-cols-12 gap-x-12 gap-y-10">
            <div className="lg:col-span-5">
              <Kicker light>{s.o_kicker}</Kicker><h2 className="mt-4 text-white">{s.o_title[0]} <em className="text-amber">{s.o_title[1]}</em></h2><p className="font-display text-xl leading-snug text-white/90 mt-5">{s.o_lead}</p>
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

        <About s={s} lang={lang} />
        <Partners s={s} />
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
