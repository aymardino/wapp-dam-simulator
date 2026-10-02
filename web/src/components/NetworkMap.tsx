/** Carte du réseau WAPP sur fond géographique (Natural Earth, domaine public) : 14 zones colorées par prix,
 *  15 lignes dont l'épaisseur suit le flux à l'heure choisie, lignes saturées en rouge. */
import { useMemo } from 'react'
import { geoMercator, geoPath } from 'd3-geo'
import westAfrica from '../data/west_africa.geo.json'

const NODES: Record<string, [number, number]> = {
  SEN: [-14.9, 14.7], GMB: [-15.6, 13.45], GNB: [-15.1, 12.0], GIN: [-11.4, 10.5], SLE: [-11.8, 8.5], LBR: [-9.5, 6.6],
  MLI: [-4.6, 14.5], BFA: [-1.6, 12.3], NER: [6.0, 15.6], CIV: [-5.6, 7.4], GHA: [-1.2, 7.9], TGO: [1.0, 8.6], BEN: [2.3, 9.5], NGA: [8.0, 9.1],
}
const LINES: [string, string][] = [['NGA', 'BEN'], ['NGA', 'NER'], ['BEN', 'TGO'], ['TGO', 'GHA'], ['GHA', 'CIV'], ['GHA', 'BFA'], ['CIV', 'BFA'], ['CIV', 'MLI'], ['CIV', 'LBR'], ['LBR', 'SLE'], ['SLE', 'GIN'], ['GIN', 'GNB'], ['GNB', 'GMB'], ['GMB', 'SEN'], ['SEN', 'MLI']]
const W = 560, H = 340
const EXTENT: any = { type: 'Polygon', coordinates: [[[-18.5, 3.5], [-18.5, 24.5], [16.5, 24.5], [16.5, 3.5], [-18.5, 3.5]]] }  // anneau horaire (convention d3-geo)

function color(p: number, lo: number, hi: number) {
  const x = hi > lo ? Math.min(1, Math.max(0, (p - lo) / (hi - lo))) : 0.5
  const a = [225, 245, 238], b = [11, 61, 48]
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * x))
  return { fill: `rgb(${c[0]},${c[1]},${c[2]})`, dark: x > 0.45 }
}

export default function NetworkMap({ prices, flows, ntc, hour, selected, unit }: { prices: Record<string, Record<string, number>>; flows: Record<string, Record<string, number>>; ntc: Record<string, number>; hour: number; selected?: string | null; unit: string }) {
  const { paths, pos } = useMemo(() => {
    const projection = geoMercator().fitExtent([[6, 6], [W - 6, H - 30]], EXTENT)
    const path = geoPath(projection)
    const paths: { id: string; member: boolean; d: string }[] = (westAfrica as any).features.map((f: any) => ({ id: String(f.id), member: !!f.properties.member, d: path(f) || '' }))
    const pos: Record<string, [number, number]> = {}
    for (const [z, ll] of Object.entries(NODES)) { const p = projection(ll as [number, number]); if (p) pos[z] = [p[0], p[1]] }
    return { paths, pos }
  }, [])
  const h = String(hour)
  const vals = Object.keys(NODES).map(z => prices[z]?.[h] ?? 0)
  const lo = Math.min(...vals), hi = Math.max(...vals)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img">
      <title>Réseau WAPP, prix et flux à {`H${h.padStart(2, '0')}`}</title>
      <rect x="0" y="0" width={W} height={H} fill="#DCE7EE" />
      {paths.map(p => <path key={p.id} d={p.d} fill={p.member ? '#F3F2EC' : '#E6E4DC'} stroke="#FFFFFF" strokeWidth={0.9} />)}
      {LINES.map(([u, v]) => {
        const key = `${u}->${v}`; const f = flows[key]?.[h] ?? 0; const cap = ntc[key] || 1
        const [x1, y1] = pos[u], [x2, y2] = pos[v]
        const w = 1.5 + 5 * Math.min(1, Math.abs(f) / cap)
        const sat = Math.abs(f) >= cap - 1
        const [fx1, fy1, fx2, fy2] = f >= 0 ? [x1, y1, x2, y2] : [x2, y2, x1, y1]
        const mx = (fx1 + fx2) / 2, my = (fy1 + fy2) / 2, ang = Math.atan2(fy2 - fy1, fx2 - fx1) * 180 / Math.PI
        const stroke = sat ? '#A32D2D' : '#0F6E56'
        return (
          <g key={key}>
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={stroke} strokeWidth={w} strokeOpacity={Math.abs(f) < 1 ? 0.3 : 0.85} strokeLinecap="round">
              <title>{`${key} : ${Math.round(f)} / ${cap} MW`}</title>
            </line>
            {Math.abs(f) >= 1 && <polygon points="-5,-4 5,0 -5,4" transform={`translate(${mx} ${my}) rotate(${ang})`} fill={stroke} />}
          </g>
        )
      })}
      {Object.entries(pos).map(([z, [x, y]]) => {
        const p = prices[z]?.[h]; const c = color(p ?? lo, lo, hi); const isSel = selected === z
        return (
          <g key={z}>
            <circle cx={x} cy={y} r={isSel ? 20 : 17} fill={c.fill} stroke={isSel ? '#0F6E56' : '#FFFFFF'} strokeWidth={isSel ? 3 : 2} />
            <text x={x} y={y - 3} textAnchor="middle" fontSize="9.5" fontWeight="600" fill={c.dark ? '#FFFFFF' : '#0B3D30'}>{z}</text>
            <text x={x} y={y + 8} textAnchor="middle" fontSize="9" fontFamily="JetBrains Mono, monospace" fill={c.dark ? '#D7E8E1' : '#0B3D30'}>{p == null ? '—' : Math.round(p)}</text>
            <title>{`${z} : ${p == null ? '—' : p.toFixed(1)} ${unit}`}</title>
          </g>
        )
      })}
      <g fontSize="9" fill="#5C5B56">
        <rect x="0" y={H - 20} width={W} height="20" fill="#FFFFFF" fillOpacity="0.85" />
        <text x="12" y={H - 7}>{`${unit} · ${Math.round(lo)}`}</text>
        <rect x="80" y={H - 15} width="60" height="8" rx="2" fill="url(#g)" />
        <text x="146" y={H - 7}>{Math.round(hi)}</text>
        <defs><linearGradient id="g"><stop offset="0" stopColor="rgb(225,245,238)" /><stop offset="1" stopColor="rgb(11,61,48)" /></linearGradient></defs>
        <line x1="200" y1={H - 11} x2="230" y2={H - 11} stroke="#0F6E56" strokeWidth="3" /><text x="236" y={H - 7}>flux</text>
        <line x1="280" y1={H - 11} x2="310" y2={H - 11} stroke="#A32D2D" strokeWidth="3" /><text x="316" y={H - 7}>saturée</text>
        <text x={W - 12} y={H - 7} textAnchor="end" fill="#8C8B84">Natural Earth</text>
      </g>
    </svg>
  )
}
