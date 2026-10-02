/** Page d'accueil publique du site wapp-dam-simulator.org : présentation, carte vivante du cas de référence,
 *  règles en trois questions, publics visés, transparence, avertissements, auteurs. Bilingue (FR/EN). */
import { useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useLang } from '../i18n'
import { LangToggle } from '../components/ui'
import NetworkMap from '../components/NetworkMap'
import { PriceChart } from '../components/Charts'
import { LINKS } from '../links'

type Demo = { hours: number[]; prices: Record<string, Record<string, number>>; flows: Record<string, Record<string, number>>; ntc: Record<string, number>; welfare: number; volume: number; saturated_lines: number; elapsed: number; solver: string }
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) || '/api/v1'

const L = {
  fr: {
    nav_app: 'Ouvrir le simulateur', nav_guides: 'Guides', nav_code: 'Code source', nav_paper: 'Note technique',
    kicker: 'Implémentation ouverte de référence',
    title: 'Le marché day-ahead du West African Power Pool, expliqué par le calcul',
    lead: 'Un simulateur de couplage de marché zonal pour les 14 pays interconnectés du WAPP : les traders déposent leurs offres, le moteur calcule les volumes, les prix et les flux de la veille pour le lendemain, et chaque règle est écrite, testée et vérifiable.',
    cta_app: 'Ouvrir le simulateur', cta_rules: 'Lire les règles de marché', cta_code: 'Voir le code',
    map_title: 'Cas de référence 2024, calculé par le moteur à l’ouverture de cette page',
    map_hint: 'Prix zonal ($/MWh) et flux sur les 15 interconnexions. Les lignes rouges sont saturées : le prix diverge de part et d’autre.',
    hour: 'Heure', welfare: 'Welfare', volume: 'Volume échangé', saturated: 'Lignes saturées', solve: 'Temps de calcul',
    q_title: 'Trois questions, trois programmes',
    q_lead: 'Un couplage de marché répond chaque jour à trois questions. Le moteur les traite dans l’ordre, comme un algorithme de bourse européenne, mais à livre ouvert.',
    q: [
      ['Qui est servi ?', 'P1 maximise le welfare, c’est-à-dire la valeur créée par les échanges, sous les limites des interconnexions (NTC) et l’équilibre de chaque zone. Avec des blocs, c’est un programme en nombres entiers.'],
      ['Combien ?', 'P1bis départage les solutions de welfare égal en maximisant le volume échangé, exactement, sans tolérance numérique.'],
      ['À quel prix ?', 'P2 choisit, parmi tous les prix compatibles avec l’équilibre (ordres acceptés, rejetés, lignes saturées ou non), celui qui est au milieu de l’intervalle admissible : la règle est explicite là où d’autres plateformes restent muettes.'],
    ],
    f_title: 'Ce que contient le simulateur',
    f: [
      ['Ordres de marché complets', 'Segments prix / quantité à profil horaire, blocs fill-or-kill, blocs liés et exclusifs, conditions de revenu minimum.'],
      ['Règles de départage écrites', 'Blocs paradoxaux rejetés itérativement, partage des ex æquo au prorata, prix d’indétermination au milieu de l’intervalle.'],
      ['Salles de formation', 'Un code par salle, un formateur, des traders par pays, clearing en direct, résultats individuels, exports CSV et JSON.'],
      ['Données de référence sourcées', 'Parc de production, demande et capacités d’échange 2024 reconstitués à partir de sources publiques, et cinq scénarios pédagogiques.'],
      ['Vérifications indépendantes', 'Chaque résultat est contrôlé : bornes de prix, flux dans les capacités, équilibre horaire, blocs, identité du welfare.'],
      ['API et ligne de commande', 'Le moteur se pilote par une API REST documentée et par un script, pour rejouer un cas ou comparer avec une autre plateforme.'],
    ],
    w_title: 'Pour qui',
    w: [
      ['Formateurs', 'Animer une séance de marché en trois manches avec des participants qui représentent chacun un pays. Guide du formateur inclus.'],
      ['Étudiants et chercheurs', 'Un cas-test public, des règles écrites et un moteur ouvert pour étudier le couplage zonal, les blocs et l’indétermination des prix.'],
      ['Opérateurs et régulateurs', 'Rejouer un cas, comparer des résultats avec ceux d’une autre plateforme, discuter des règles de départage avant le lancement du marché.'],
    ],
    t_title: 'Ouvert et vérifiable',
    t_lead: 'Le code est publié sous licence Apache 2.0, les données et la documentation sous CC BY 4.0. Les valeurs du cas de référence sont fixées par des tests automatiques, et une campagne de cas aléatoires contrôle les propriétés du clearing à chaque modification.',
    t_items: ['Règles de marché', 'Données de référence', 'Architecture', 'Déploiement'],
    d_title: 'Avertissements',
    d1: 'Simulateur pédagogique indépendant. Ce projet n’est pas affilié au West African Power Pool, à son Centre d’Information et de Coordination ni à aucun fournisseur de plateforme de marché. « WAPP » et « West African Power Pool » appartiennent au WAPP.',
    d2: 'Les données de référence (parc, demande, capacités d’échange) sont reconstituées à partir de sources publiques et de valeurs estimées, notamment les NTC. Elles servent à la formation et à la recherche, pas à l’exploitation.',
    a_title: 'Auteurs',
    a_text: 'Kodjovi Plakoo et Enrico Patanè, Mastère Spécialisé OSE 2025, Mines Paris-PSL, avec Lucien Kouakou, Mouhamadou Sow et Wissem Hmila pour les premiers livrables. Encadrement : El Hadji Tamsir Diop (SENELEC) et Adrien Atayi (EPEX SPOT).',
    a_paper: 'Note technique à paraître.', a_paper_link: 'Lire la note technique', contact: 'Questions et contributions',
    footer: 'Simulateur pédagogique indépendant, non affilié au WAPP.',
    loading: 'Calcul du cas de référence…', demo_err: 'Le serveur de démonstration ne répond pas.',
  },
  en: {
    nav_app: 'Open the simulator', nav_guides: 'Guides', nav_code: 'Source code', nav_paper: 'Technical note',
    kicker: 'Open reference implementation',
    title: 'The West African Power Pool day-ahead market, explained by computation',
    lead: 'A zonal market coupling simulator for the 14 interconnected WAPP countries: traders submit orders, the engine computes the next day’s volumes, prices and flows, and every rule is written down, tested and verifiable.',
    cta_app: 'Open the simulator', cta_rules: 'Read the market rules', cta_code: 'View the code',
    map_title: '2024 reference case, computed by the engine when this page opened',
    map_hint: 'Zonal price ($/MWh) and flows on the 15 interconnections. Red lines are saturated: prices diverge on either side.',
    hour: 'Hour', welfare: 'Welfare', volume: 'Traded volume', saturated: 'Saturated lines', solve: 'Solve time',
    q_title: 'Three questions, three programs',
    q_lead: 'A market coupling answers three questions every day. The engine takes them in order, like a European exchange algorithm, but with the book open.',
    q: [
      ['Who is served?', 'P1 maximises welfare, the value created by trades, under interconnection limits (NTC) and each zone’s balance. With blocks it is a mixed-integer program.'],
      ['How much?', 'P1bis breaks ties between equal-welfare solutions by maximising traded volume, exactly, with no numerical tolerance.'],
      ['At what price?', 'P2 picks, among all prices consistent with equilibrium (accepted and rejected orders, saturated or free lines), the midpoint of the admissible interval: the rule is explicit where other platforms stay silent.'],
    ],
    f_title: 'What is inside',
    f: [
      ['Complete market orders', 'Price / quantity segments with hourly profiles, fill-or-kill blocks, linked and exclusive blocks, minimum income conditions.'],
      ['Written tie-break rules', 'Paradoxical blocks rejected iteratively, pro-rata sharing of equal-price orders, indeterminate prices set at the midpoint of the interval.'],
      ['Training rooms', 'One code per room, one trainer, traders per country, live clearing, individual results, CSV and JSON exports.'],
      ['Sourced reference data', '2024 generation fleet, demand and exchange capacities rebuilt from public sources, plus five teaching scenarios.'],
      ['Independent checks', 'Every result is verified: price bounds, flows within capacities, hourly balance, block rules, welfare identity.'],
      ['API and command line', 'The engine is driven by a documented REST API and a script, to replay a case or compare with another platform.'],
    ],
    w_title: 'Who it is for',
    w: [
      ['Trainers', 'Run a three-round market session with participants who each represent a country. Trainer guide included.'],
      ['Students and researchers', 'A public test case, written rules and an open engine to study zonal coupling, blocks and price indeterminacy.'],
      ['Operators and regulators', 'Replay a case, compare results with another platform, discuss tie-break rules before the market goes live.'],
    ],
    t_title: 'Open and verifiable',
    t_lead: 'The code is released under the Apache 2.0 licence, data and documentation under CC BY 4.0. Reference-case values are pinned by automated tests, and a campaign of random cases checks clearing properties on every change.',
    t_items: ['Market rules', 'Reference data', 'Architecture', 'Deployment'],
    d_title: 'Disclaimers',
    d1: 'Independent educational simulator. This project is not affiliated with the West African Power Pool, its Information and Coordination Centre, or any market platform vendor. “WAPP” and “West African Power Pool” belong to the WAPP.',
    d2: 'Reference data (fleet, demand, exchange capacities) are rebuilt from public sources and estimated values, in particular the NTC. They are meant for training and research, not for operations.',
    a_title: 'Authors',
    a_text: 'Kodjovi Plakoo and Enrico Patanè, Advanced Master OSE 2025, Mines Paris-PSL, with Lucien Kouakou, Mouhamadou Sow and Wissem Hmila for the first deliverables. Supervision: El Hadji Tamsir Diop (SENELEC) and Adrien Atayi (EPEX SPOT).',
    a_paper: 'Technical note forthcoming.', a_paper_link: 'Read the technical note', contact: 'Questions and contributions',
    footer: 'Independent educational simulator, not affiliated with the WAPP.',
    loading: 'Computing the reference case…', demo_err: 'The demonstration server is not responding.',
  },
}

const money = (x: number) => `${(x / 1e6).toLocaleString('fr-FR', { maximumFractionDigits: 2 })} M USD`
const num = (x: number) => x.toLocaleString('fr-FR', { maximumFractionDigits: 0 })

function Section({ id, title, lead, children, tone = 'page' }: { id: string; title: string; lead?: string; children: ReactNode; tone?: 'page' | 'surface' | 'brand' }) {
  const bg = tone === 'surface' ? 'bg-surface border-y border-line' : tone === 'brand' ? 'bg-brand text-white' : ''
  return (
    <section id={id} className={bg}>
      <div className="max-w-6xl mx-auto px-6 py-16">
        <h2 className={`text-2xl ${tone === 'brand' ? 'text-white' : ''}`}>{title}</h2>
        {lead && <p className={`mt-3 max-w-3xl text-lg ${tone === 'brand' ? 'text-brand-ink' : 'text-ink-2'}`}>{lead}</p>}
        <div className="mt-8">{children}</div>
      </div>
    </section>
  )
}

export default function Landing() {
  const { lang } = useLang(); const s = L[lang]
  const [demo, setDemo] = useState<Demo | null>(null); const [err, setErr] = useState(false)
  const [hour, setHour] = useState(19); const [play, setPlay] = useState(true)
  useEffect(() => { fetch(`${BASE}/demo`).then(r => { if (!r.ok) throw new Error(); return r.json() }).then(setDemo).catch(() => setErr(true)) }, [])
  useEffect(() => { if (!play || !demo) return; const id = setInterval(() => setHour(h => (h + 1) % 24), 1500); return () => clearInterval(id) }, [play, demo])
  useEffect(() => { document.title = lang === 'fr' ? 'Simulateur de marché day-ahead du WAPP' : 'WAPP day-ahead market simulator' }, [lang])
  const ext = (href: string, children: ReactNode, cls = '') => <a href={href} target="_blank" rel="noreferrer" className={cls}>{children}</a>
  const docLinks = [LINKS.rules, LINKS.data, LINKS.architecture, LINKS.deploy]

  return (
    <div className="min-h-screen">
      <header className="bg-brand text-white sticky top-0 z-10">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 h-16">
          <a href="#top" className="flex items-center gap-3"><img src="/mark.svg" alt="" className="h-9 w-9" /><span className="font-semibold text-lg whitespace-nowrap hidden sm:inline">WAPP DAM Simulator</span></a>
          <nav className="flex items-center gap-5 text-sm">
            <a href="#rules" className="hidden md:inline text-brand-ink hover:text-white">{s.q_title}</a>
            <Link to="/guide/formateur" className="hidden sm:inline text-brand-ink hover:text-white">{s.nav_guides}</Link>
            {ext(LINKS.github, s.nav_code, 'hidden sm:inline text-brand-ink hover:text-white')}
            <Link to="/app" className="h-9 px-4 inline-flex items-center rounded bg-accent hover:bg-accent-hover text-white font-medium whitespace-nowrap">{s.nav_app}</Link>
            <LangToggle dark />
          </nav>
        </div>
      </header>

      <main id="top">
        <section className="max-w-6xl mx-auto px-6 pt-14 pb-16 grid lg:grid-cols-12 gap-10 items-start">
          <div className="lg:col-span-5 min-w-0">
            <div className="text-sm uppercase tracking-wide text-accent font-semibold">{s.kicker}</div>
            <h1 className="text-3xl mt-3 leading-tight">{s.title}</h1>
            <p className="text-ink-2 text-lg mt-5">{s.lead}</p>
            <div className="flex flex-wrap gap-3 mt-8">
              <Link to="/app" className="h-11 px-5 inline-flex items-center rounded bg-accent hover:bg-accent-hover text-white font-medium text-base">{s.cta_app}</Link>
              {ext(LINKS.rules, s.cta_rules, 'h-11 px-5 inline-flex items-center rounded border border-line-strong bg-surface hover:bg-panel text-ink font-medium text-base')}
              {ext(LINKS.github, s.cta_code, 'h-11 px-5 inline-flex items-center rounded text-accent font-medium text-base hover:underline underline-offset-4')}
            </div>
          </div>
          <div className="lg:col-span-7 min-w-0">
            <div className="bg-surface border border-line rounded-lg shadow-panel overflow-hidden">
              <div className="px-5 min-h-12 py-2.5 flex items-center justify-between gap-3 border-b border-line text-sm text-ink-2">
                <span className="leading-snug">{s.map_title}</span>
                {demo && <span className="flex items-center gap-3 shrink-0 font-mono"><button onClick={() => setPlay(p => !p)} className="text-accent" aria-label={play ? 'pause' : 'play'}>{play ? '❚❚' : '▶'}</button><span>H{String(hour).padStart(2, '0')}</span></span>}
              </div>
              {demo ? <NetworkMap prices={demo.prices} flows={demo.flows} ntc={demo.ntc} hour={hour} unit="$/MWh" />
                : <div className="aspect-[560/340] flex items-center justify-center text-ink-3">{err ? s.demo_err : s.loading}</div>}
              {demo && (
                <div className="px-5 py-3 border-t border-line flex items-center gap-4">
                  <label className="text-sm text-ink-2 shrink-0">{s.hour}</label>
                  <input type="range" min={0} max={23} value={hour} onChange={e => { setPlay(false); setHour(Number(e.target.value)) }} className="flex-1 h-2 p-0 border-0 accent-accent" />
                </div>
              )}
              {demo && (
                <div className="grid grid-cols-2 md:grid-cols-4 border-t border-line divide-x divide-line">
                  {[[s.welfare, money(demo.welfare)], [s.volume, `${num(demo.volume)} MWh`], [s.saturated, `${demo.saturated_lines} / 15`], [s.solve, `${demo.elapsed.toFixed(2)} s`]].map(([k, v]) => (
                    <div key={k} className="px-4 py-3"><div className="text-xs uppercase tracking-wide text-ink-3">{k}</div><div className="font-mono text-base mt-0.5">{v}</div></div>
                  ))}
                </div>
              )}
            </div>
            <p className="text-sm text-ink-3 mt-3">{s.map_hint}</p>
          </div>
        </section>

        <Section id="rules" title={s.q_title} lead={s.q_lead} tone="surface">
          <div className="grid md:grid-cols-3 gap-6">
            {s.q.map(([h, p], i) => (
              <div key={h} className="bg-panel rounded-lg p-6">
                <div className="font-mono text-sm text-accent mb-2">{['P1', 'P1bis', 'P2'][i]}</div>
                <h3 className="normal-case tracking-normal text-lg font-semibold text-ink">{h}</h3>
                <p className="text-ink-2 mt-2 leading-relaxed">{p}</p>
              </div>
            ))}
          </div>
          {demo && (
            <div className="mt-10 bg-surface border border-line rounded-lg p-5">
              <div className="text-sm text-ink-2 mb-2">{lang === 'fr' ? 'Prix horaires des 14 zones, cas de référence 2024' : 'Hourly prices of the 14 zones, 2024 reference case'}</div>
              <PriceChart prices={demo.prices} hours={demo.hours} unit="$/MWh" />
            </div>
          )}
        </Section>

        <Section id="features" title={s.f_title}>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-x-10 gap-y-8">
            {s.f.map(([h, p]) => <div key={h}><h3 className="normal-case tracking-normal text-base font-semibold text-ink">{h}</h3><p className="text-ink-2 mt-1.5 leading-relaxed">{p}</p></div>)}
          </div>
        </Section>

        <Section id="who" title={s.w_title} tone="surface">
          <div className="grid md:grid-cols-3 gap-6">
            {s.w.map(([h, p]) => <div key={h} className="border-l-2 border-accent pl-5"><h3 className="normal-case tracking-normal text-lg font-semibold text-ink">{h}</h3><p className="text-ink-2 mt-2 leading-relaxed">{p}</p></div>)}
          </div>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/guide/formateur" className="text-accent font-medium hover:underline underline-offset-4">{lang === 'fr' ? 'Guide du formateur →' : 'Trainer guide →'}</Link>
            <Link to="/guide/trader" className="text-accent font-medium hover:underline underline-offset-4">{lang === 'fr' ? 'Guide du trader →' : 'Trader guide →'}</Link>
          </div>
        </Section>

        <Section id="open" title={s.t_title} lead={s.t_lead} tone="brand">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {s.t_items.map((label, i) => ext(docLinks[i], <span className="block bg-brand-2 hover:bg-white/10 rounded-lg px-5 py-4 text-white font-medium">{label} →</span>, ''))}
          </div>
          <div className="mt-6 text-sm text-brand-ink">Apache 2.0 · CC BY 4.0 · {ext(LINKS.github, 'GitHub', 'underline underline-offset-4 hover:text-white')}</div>
        </Section>

        <Section id="disclaimers" title={s.d_title}>
          <div className="grid md:grid-cols-2 gap-6 max-w-5xl">
            <p className="text-ink-2 leading-relaxed">{s.d1}</p>
            <p className="text-ink-2 leading-relaxed">{s.d2}</p>
          </div>
        </Section>

        <Section id="authors" title={s.a_title} tone="surface">
          <p className="text-ink-2 leading-relaxed max-w-4xl">{s.a_text}</p>
          <div className="mt-5 flex flex-wrap gap-6 text-base">
            {LINKS.paper ? ext(LINKS.paper, s.a_paper_link + ' →', 'text-accent font-medium') : <span className="text-ink-3">{s.a_paper}</span>}
            {ext(LINKS.issues, s.contact + ' →', 'text-accent font-medium')}
          </div>
        </Section>
      </main>

      <footer className="border-t border-line">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-wrap items-center justify-between gap-4 text-sm text-ink-3">
          <span>© 2026 Kodjovi Plakoo, Enrico Patanè · {s.footer}</span>
          <span className="flex gap-5">{ext(LINKS.licence, 'Apache 2.0')}{ext(LINKS.github, 'GitHub')}<Link to="/app">{s.nav_app}</Link></span>
        </div>
      </footer>
    </div>
  )
}
