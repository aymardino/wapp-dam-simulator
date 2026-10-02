/** WAPP network map on a geographic background (Natural Earth, public domain): 14 zones coloured by price,
 *  15 lines whose width follows the flow at the chosen hour, saturated lines in red. */
import { useId, useMemo } from 'react'
import { geoMercator, geoPath } from 'd3-geo'
import westAfrica from '../data/west_africa.geo.json'

const NODES: Record<string, [number, number]> = {
  SEN: [-14.9, 14.7], GMB: [-15.6, 13.45], GNB: [-15.1, 12.0], GIN: [-11.4, 10.5], SLE: [-11.8, 8.5], LBR: [-9.5, 6.6],
  MLI: [-4.6, 14.5], BFA: [-1.6, 12.3], NER: [6.0, 15.6], CIV: [-5.6, 7.4], GHA: [-1.2, 7.9], TGO: [1.0, 8.6], BEN: [2.3, 9.5], NGA: [8.0, 9.1],
}
const LINES: [string, string][] = [['NGA', 'BEN'], ['NGA', 'NER'], ['BEN', 'TGO'], ['TGO', 'GHA'], ['GHA', 'CIV'], ['GHA', 'BFA'], ['CIV', 'BFA'], ['CIV', 'MLI'], ['CIV', 'LBR'], ['LBR', 'SLE'], ['SLE', 'GIN'], ['GIN', 'GNB'], ['GNB', 'GMB'], ['GMB', 'SEN'], ['SEN', 'MLI']]
const W = 560, H = 340
const R = 14
/** Offset (SVG units) of the small countries' nodes, towards the sea, to avoid overlaps. */
const OFFSET: Record<string, [number, number]> = { GMB: [-30, 2], GNB: [-24, 24], TGO: [-4, 34], BEN: [14, 40], SLE: [-16, 8], LBR: [-8, 18] }
const EXTENT: any = { type: 'Polygon', coordinates: [[[-18.5, 3.5], [-18.5, 24.5], [16.5, 24.5], [16.5, 3.5], [-18.5, 3.5]]] }  // clockwise ring (d3-geo convention)

type Theme = 'light' | 'dark'
/** Palettes: light (application) and dark (website). Nodes go from colour "lo" (low price) to "hi" (high price). */
const PALETTE = {
  light: { sea: '#DCE7EE', member: '#F6F5EF', other: '#E8E6DF', border: '#1B1B19', borderOp: [0.9, 0.5], lo: [225, 245, 238], hi: [11, 61, 48], flow: '#0F6E56', sat: '#A32D2D', nodeStroke: '#FFFFFF', selStroke: '#0F6E56', legendBg: '#FFFFFF', legendText: '#5C5B56', credit: '#8C8B84', leader: '#1B1B19' },
  dark: { sea: '#07241C', member: '#10493A', other: '#0C352A', border: '#D7E8E1', borderOp: [0.45, 0.2], lo: [168, 224, 196], hi: [242, 177, 52], flow: '#8FD3B5', sat: '#FF6B4A', nodeStroke: '#07241C', selStroke: '#FFFFFF', legendBg: '#07241C', legendText: '#D7E8E1', credit: '#8FA89F', leader: '#D7E8E1' },
}

function color(p: number, lo: number, hi: number, pal: typeof PALETTE.light) {
  const x = hi > lo ? Math.min(1, Math.max(0, (p - lo) / (hi - lo))) : 0.5
  const c = pal.lo.map((v, i) => Math.round(v + (pal.hi[i] - v) * x))
  return { fill: `rgb(${c[0]},${c[1]},${c[2]})`, dark: x > 0.45 }
}

export default function NetworkMap({ prices, flows, ntc, hour, selected, unit, theme = 'light', onSelect }: { prices: Record<string, Record<string, number>>; flows: Record<string, Record<string, number>>; ntc: Record<string, number>; hour: number; selected?: string | null; unit: string; theme?: Theme; onSelect?: (zone: string) => void }) {
  const pal = PALETTE[theme]; const gid = useId()
  const { paths, pos, anchor } = useMemo(() => {
    const projection = geoMercator().fitExtent([[6, 6], [W - 6, H - 30]], EXTENT)
    const path = geoPath(projection)
    const paths: { id: string; member: boolean; d: string }[] = (westAfrica as any).features.map((f: any) => ({ id: String(f.id), member: !!f.properties.member, d: path(f) || '' }))
    const pos: Record<string, [number, number]> = {}
    const anchor: Record<string, [number, number]> = {}
    for (const [z, ll] of Object.entries(NODES)) {
      const p = projection(ll as [number, number]); if (!p) continue
      anchor[z] = [p[0], p[1]]
      const o = OFFSET[z] || [0, 0]; pos[z] = [p[0] + o[0], p[1] + o[1]]
    }
    return { paths, pos, anchor }
  }, [])
  const h = String(hour)
  const vals = Object.keys(NODES).map(z => prices[z]?.[h] ?? 0)
  const lo = Math.min(...vals), hi = Math.max(...vals)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img">
      <title>Réseau WAPP, prix et flux à {`H${h.padStart(2, '0')}`}</title>
      <rect x="0" y="0" width={W} height={H} fill={pal.sea} />
      {paths.map(p => <path key={p.id} d={p.d} fill={p.member ? pal.member : pal.other} stroke={pal.border} strokeWidth={p.member ? 0.8 : 0.5} strokeOpacity={p.member ? pal.borderOp[0] : pal.borderOp[1]} />)}
      {LINES.map(([u, v]) => {
        const key = `${u}->${v}`; const f = flows[key]?.[h] ?? 0; const cap = ntc[key] || 1
        const [x1, y1] = pos[u], [x2, y2] = pos[v]
        const w = 1.5 + 5 * Math.min(1, Math.abs(f) / cap)
        const sat = Math.abs(f) >= cap - 1
        const [fx1, fy1, fx2, fy2] = f >= 0 ? [x1, y1, x2, y2] : [x2, y2, x1, y1]
        const mx = (fx1 + fx2) / 2, my = (fy1 + fy2) / 2, ang = Math.atan2(fy2 - fy1, fx2 - fx1) * 180 / Math.PI
        const stroke = sat ? pal.sat : pal.flow
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
        const p = prices[z]?.[h]; const c = color(p ?? lo, lo, hi, pal); const isSel = selected === z
        const [ax, ay] = anchor[z]; const moved = OFFSET[z] != null
        const txt = theme === 'dark' ? '#07241C' : c.dark ? '#FFFFFF' : '#0B3D30'; const txt2 = theme === 'dark' ? '#0B3D30' : c.dark ? '#D7E8E1' : '#0B3D30'
        return (
          <g key={z} onClick={onSelect ? () => onSelect(z) : undefined} style={onSelect ? { cursor: 'pointer' } : undefined}>
            {moved && <><line x1={ax} y1={ay} x2={x} y2={y} stroke={pal.leader} strokeWidth={0.8} strokeOpacity={0.6} /><circle cx={ax} cy={ay} r={1.8} fill={pal.leader} /></>}
            <circle cx={x} cy={y} r={isSel ? R + 3 : R} fill={c.fill} stroke={isSel ? pal.selStroke : pal.nodeStroke} strokeWidth={isSel ? 2.5 : 1.5} />
            <text x={x} y={y - 2.5} textAnchor="middle" fontSize="8.5" fontWeight="600" fill={txt}>{z}</text>
            <text x={x} y={y + 7} textAnchor="middle" fontSize="8" fontFamily="JetBrains Mono, monospace" fill={txt2}>{p == null ? '—' : Math.round(p)}</text>
            <title>{`${z} : ${p == null ? '—' : p.toFixed(1)} ${unit}`}</title>
          </g>
        )
      })}
      <g fontSize="9" fill={pal.legendText}>
        <rect x="0" y={H - 20} width={W} height="20" fill={pal.legendBg} fillOpacity="0.85" />
        <text x="12" y={H - 7}>{`${unit} · ${Math.round(lo)}`}</text>
        <rect x="80" y={H - 15} width="60" height="8" rx="2" fill={`url(#${gid})`} />
        <text x="146" y={H - 7}>{Math.round(hi)}</text>
        <defs><linearGradient id={gid}><stop offset="0" stopColor={`rgb(${pal.lo.join(',')})`} /><stop offset="1" stopColor={`rgb(${pal.hi.join(',')})`} /></linearGradient></defs>
        <line x1="200" y1={H - 11} x2="230" y2={H - 11} stroke={pal.flow} strokeWidth="3" /><text x="236" y={H - 7}>flux</text>
        <line x1="280" y1={H - 11} x2="310" y2={H - 11} stroke={pal.sat} strokeWidth="3" /><text x="316" y={H - 7}>saturée</text>
        <text x={W - 12} y={H - 7} textAnchor="end" fill={pal.credit}>Natural Earth</text>
      </g>
    </svg>
  )
}
