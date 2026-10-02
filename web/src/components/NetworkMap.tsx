/** Schéma du réseau WAPP : 14 zones colorées par prix, 15 lignes dont l'épaisseur suit le flux à l'heure choisie. */
const POS: Record<string, [number, number]> = {
  SEN: [62, 128], GMB: [78, 158], GNB: [100, 186], GIN: [158, 204], SLE: [150, 254], LBR: [208, 290],
  MLI: [196, 92], BFA: [312, 128], NER: [430, 84], CIV: [268, 240], GHA: [340, 246], TGO: [384, 226], BEN: [416, 212], NGA: [496, 190],
}
const LINES: [string, string][] = [['NGA', 'BEN'], ['NGA', 'NER'], ['BEN', 'TGO'], ['TGO', 'GHA'], ['GHA', 'CIV'], ['GHA', 'BFA'], ['CIV', 'BFA'], ['CIV', 'MLI'], ['CIV', 'LBR'], ['LBR', 'SLE'], ['SLE', 'GIN'], ['GIN', 'GNB'], ['GNB', 'GMB'], ['GMB', 'SEN'], ['SEN', 'MLI']]

function color(p: number, lo: number, hi: number) {
  const x = hi > lo ? Math.min(1, Math.max(0, (p - lo) / (hi - lo))) : 0.5
  const a = [225, 245, 238], b = [11, 61, 48]
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * x))
  return { fill: `rgb(${c[0]},${c[1]},${c[2]})`, dark: x > 0.45 }
}

export default function NetworkMap({ prices, flows, ntc, hour, selected, unit }: { prices: Record<string, Record<string, number>>; flows: Record<string, Record<string, number>>; ntc: Record<string, number>; hour: number; selected?: string | null; unit: string }) {
  const h = String(hour)
  const vals = Object.keys(POS).map(z => prices[z]?.[h] ?? 0)
  const lo = Math.min(...vals), hi = Math.max(...vals)
  return (
    <svg viewBox="0 0 560 320" className="w-full h-auto" role="img">
      <title>Réseau WAPP, prix et flux à {`H${h.padStart(2, '0')}`}</title>
      {LINES.map(([u, v]) => {
        const key = `${u}->${v}`; const f = flows[key]?.[h] ?? 0; const cap = ntc[key] || 1
        const [x1, y1] = POS[u], [x2, y2] = POS[v]
        const w = 1 + 5 * Math.min(1, Math.abs(f) / cap)
        const sat = Math.abs(f) >= cap - 1
        const [fx1, fy1, fx2, fy2] = f >= 0 ? [x1, y1, x2, y2] : [x2, y2, x1, y1]
        const mx = (fx1 + fx2) / 2, my = (fy1 + fy2) / 2, ang = Math.atan2(fy2 - fy1, fx2 - fx1) * 180 / Math.PI
        return (
          <g key={key}>
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={sat ? '#A32D2D' : '#0F6E56'} strokeWidth={w} strokeOpacity={Math.abs(f) < 1 ? 0.25 : 0.8} strokeLinecap="round">
              <title>{`${key} : ${Math.round(f)} / ${cap} MW`}</title>
            </line>
            {Math.abs(f) >= 1 && <polygon points="-5,-4 5,0 -5,4" transform={`translate(${mx} ${my}) rotate(${ang})`} fill={sat ? '#A32D2D' : '#0F6E56'} />}
          </g>
        )
      })}
      {Object.entries(POS).map(([z, [x, y]]) => {
        const p = prices[z]?.[h]; const c = color(p ?? lo, lo, hi); const isSel = selected === z
        return (
          <g key={z}>
            <circle cx={x} cy={y} r={isSel ? 21 : 18} fill={c.fill} stroke={isSel ? '#0F6E56' : '#FFFFFF'} strokeWidth={isSel ? 3 : 2} />
            <text x={x} y={y - 3} textAnchor="middle" fontSize="9.5" fontWeight="600" fill={c.dark ? '#FFFFFF' : '#0B3D30'}>{z}</text>
            <text x={x} y={y + 8} textAnchor="middle" fontSize="9" fontFamily="JetBrains Mono, monospace" fill={c.dark ? '#D7E8E1' : '#0B3D30'}>{p == null ? '—' : Math.round(p)}</text>
            <title>{`${z} : ${p == null ? '—' : p.toFixed(1)} ${unit}`}</title>
          </g>
        )
      })}
      <g fontSize="9" fill="#8C8B84">
        <text x="12" y="306">{`${unit} · ${Math.round(lo)} → ${Math.round(hi)}`}</text>
        <rect x="150" y="298" width="60" height="8" rx="2" fill="url(#g)" />
        <defs><linearGradient id="g"><stop offset="0" stopColor="rgb(225,245,238)" /><stop offset="1" stopColor="rgb(11,61,48)" /></linearGradient></defs>
        <line x1="240" y1="302" x2="270" y2="302" stroke="#0F6E56" strokeWidth="3" /><text x="276" y="306">flux</text>
        <line x1="310" y1="302" x2="340" y2="302" stroke="#A32D2D" strokeWidth="3" /><text x="346" y="306">saturée</text>
      </g>
    </svg>
  )
}
