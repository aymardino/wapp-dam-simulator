/** Carte de chaleur des prix : une ligne par zone (triées par prix moyen décroissant), une colonne par heure,
 *  couleur = prix. Les zones couplées forment des bandes de même couleur ; un trait sépare les groupes de prix. */
const NAMES: Record<string, [string, string]> = { SEN: ['Sénégal', 'Senegal'], GMB: ['Gambie', 'The Gambia'], GNB: ['Guinée-Bissau', 'Guinea-Bissau'], GIN: ['Guinée', 'Guinea'], SLE: ['Sierra Leone', 'Sierra Leone'], LBR: ['Liberia', 'Liberia'], MLI: ['Mali', 'Mali'], BFA: ['Burkina Faso', 'Burkina Faso'], NER: ['Niger', 'Niger'], CIV: ['Côte d’Ivoire', 'Côte d’Ivoire'], GHA: ['Ghana', 'Ghana'], TGO: ['Togo', 'Togo'], BEN: ['Bénin', 'Benin'], NGA: ['Nigeria', 'Nigeria'] }
const STOPS = [[232, 244, 238], [245, 215, 122], [181, 68, 60]]

function color(x: number) {
  const t = x < 0.5 ? x * 2 : (x - 0.5) * 2
  const [a, b] = x < 0.5 ? [STOPS[0], STOPS[1]] : [STOPS[1], STOPS[2]]
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * t))
  return { bg: `rgb(${c.join(',')})`, dark: x > 0.62 }
}

export default function PriceHeatmap({ prices, hours, highlight, unit, lang = 'fr', onSelect }: { prices: Record<string, Record<string, number>>; hours: number[]; highlight?: string | null; unit: string; lang?: 'fr' | 'en'; onSelect?: (zone: string) => void }) {
  const zones = Object.keys(prices)
  const avg: Record<string, number> = {}
  for (const z of zones) avg[z] = hours.reduce((a, h) => a + (prices[z]?.[String(h)] ?? 0), 0) / Math.max(1, hours.length)
  const order = [...zones].sort((a, b) => avg[b] - avg[a])
  const all = order.flatMap(z => hours.map(h => prices[z]?.[String(h)] ?? 0))
  const lo = Math.min(...all), hi = Math.max(...all)
  const x = (p: number) => (hi > lo ? (p - lo) / (hi - lo) : 0.5)
  const n = (v: number) => Math.round(v).toLocaleString('fr-FR')
  const cols = `minmax(56px, 128px) repeat(${hours.length}, minmax(0, 1fr)) 52px`
  return (
    <div className="overflow-x-auto">
      <div className="min-w-[620px]">
        <div className="grid items-stretch" style={{ gridTemplateColumns: cols }}>
          <div className="text-xs text-ink-3 pb-1.5 self-end">{lang === 'fr' ? 'Zone · heure' : 'Zone · hour'}</div>
          {hours.map(h => <div key={h} className="text-center font-mono text-[11px] text-ink-3 pb-1.5 self-end">{String(h).padStart(2, '0')}</div>)}
          <div className="text-right font-mono text-[11px] text-ink-3 pb-1.5 self-end">{lang === 'fr' ? 'moy.' : 'avg'}</div>
          {order.map((z, i) => {
            const gap = i > 0 && avg[order[i - 1]] - avg[z] > 4
            const sel = highlight === z
            return [
              <div key={`${z}-l`} onClick={onSelect ? () => onSelect(z) : undefined}
                className={`flex items-baseline gap-1.5 pr-2 h-7 ${gap ? 'border-t-2 border-line-strong mt-1' : ''} ${onSelect ? 'cursor-pointer' : ''}`}>
                <span className={`font-mono text-sm ${sel ? 'font-semibold text-accent' : 'text-ink'}`}>{z}</span>
                <span className="text-[11px] text-ink-3 truncate hidden md:inline">{NAMES[z]?.[lang === 'fr' ? 0 : 1] ?? ''}</span>
              </div>,
              ...hours.map(h => {
                const p = prices[z]?.[String(h)] ?? 0; const c = color(x(p))
                return <div key={`${z}-${h}`} title={`${z} ${String(h).padStart(2, '0')}h : ${p.toFixed(1)} ${unit}`}
                  className={`h-7 flex items-center justify-center font-mono text-[11px] ${gap ? 'border-t-2 border-line-strong mt-1' : ''} ${sel ? 'ring-1 ring-inset ring-accent' : ''}`}
                  style={{ background: c.bg, color: c.dark ? '#FFFFFF' : '#1B1B19' }}>
                  <span className="hidden lg:inline">{n(p)}</span>
                </div>
              }),
              <div key={`${z}-a`} className={`h-7 flex items-center justify-end font-mono text-sm pl-2 ${gap ? 'border-t-2 border-line-strong mt-1' : ''} ${sel ? 'text-accent font-semibold' : 'text-ink-2'}`}>{n(avg[z])}</div>,
            ]
          })}
        </div>
        <div className="flex items-center gap-3 mt-3 text-xs text-ink-3">
          <span>{unit} · {n(lo)}</span>
          <span className="h-2.5 w-40 rounded-sm" style={{ background: `linear-gradient(90deg, rgb(${STOPS[0].join(',')}), rgb(${STOPS[1].join(',')}), rgb(${STOPS[2].join(',')}))` }} />
          <span>{n(hi)}</span>
          <span className="ml-auto">{lang === 'fr' ? 'Lignes triées par prix moyen ; un trait sépare les groupes de prix.' : 'Rows sorted by mean price; a rule separates price groups.'}</span>
        </div>
      </div>
    </div>
  )
}
