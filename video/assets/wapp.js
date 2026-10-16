/* Shared helpers of the video, loaded once by index.html after GSAP, strings.js and data.js. Every scene uses:
   WAPP.lang, WAPP.t(key, vars), WAPP.data, number formats, the network map builder and a few motion helpers.
   All helpers are deterministic: they only add tweens to the scene's paused timeline. */
(function () {
  gsap.registerPlugin(SplitText, DrawSVGPlugin, MotionPathPlugin, CustomEase)

  const vars = (window.__hyperframes && window.__hyperframes.getVariables && window.__hyperframes.getVariables()) || {}
  const lang = vars.lang === 'en' ? 'en' : 'fr'
  document.documentElement.lang = lang

  /** French typography: non-breaking spaces before : ; ? ! » and after «, as on the website. */
  const frTypo = s => s.replace(/ ([?!:;»])/g, ' $1').replace(/« /g, '« ')
  const S = window.WAPP_STRINGS

  /** Text of `key` in the video's language, with {placeholders} filled from `values`. */
  function t(key, values) {
    let s = (S[lang] && S[lang][key]) ?? S.fr[key]
    if (s == null) { console.warn('WAPP: missing string', key); return key }
    if (values) s = s.replace(/\{(\w+)\}/g, (m, k) => (values[k] != null ? String(values[k]) : m))
    return lang === 'fr' ? frTypo(s) : s
  }

  const ZONE_NAMES = { SEN: ['Sénégal', 'Senegal'], GMB: ['Gambie', 'The Gambia'], GNB: ['Guinée-Bissau', 'Guinea-Bissau'], GIN: ['Guinée', 'Guinea'], SLE: ['Sierra Leone', 'Sierra Leone'], LBR: ['Liberia', 'Liberia'], MLI: ['Mali', 'Mali'], BFA: ['Burkina Faso', 'Burkina Faso'], NER: ['Niger', 'Niger'], CIV: ['Côte d’Ivoire', 'Côte d’Ivoire'], GHA: ['Ghana', 'Ghana'], TGO: ['Togo', 'Togo'], BEN: ['Bénin', 'Benin'], NGA: ['Nigeria', 'Nigeria'] }
  const zoneName = z => ZONE_NAMES[z][lang === 'fr' ? 0 : 1]
  const locale = lang === 'fr' ? 'fr-FR' : 'en-GB'
  /** 281977 → "281 977" (fr) / "281,977" (en). */
  const num = (x, d = 0) => Number(x).toLocaleString(locale, { minimumFractionDigits: d, maximumFractionDigits: d })
  /** 44924789 → "44,92 M USD" / "44.92 M USD". */
  const money = x => `${num(x / 1e6, 2)} M USD`
  /** 19 → "19 h" (fr) / "19:00" (en). */
  const hour = h => t('hour', { h, hh: String(h).padStart(2, '0') })
  /** 7 → "H07", the website's hour label. */
  const hh = h => `H${String(h).padStart(2, '0')}`

  /* ── Motion helpers ──────────────────────────────────────────────────────── */
  const EASE = 'power3.out'

  /** Scene entrance: the amber line sweeps from left to right and uncovers the scene's frame behind it (the previous
   *  scene stays underneath until covered). Call first, at t = 0, in every scene but the first. Takes 0.7 s. */
  function wipeIn(tl, frameSel, sweepSel, at = 0) {
    tl.fromTo(frameSel, { clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)', duration: 0.7, ease: 'power2.inOut' }, at)
    if (sweepSel) {
      tl.fromTo(sweepSel, { x: 0, opacity: 1 }, { x: 1920, duration: 0.7, ease: 'power2.inOut' }, at)
      tl.to(sweepSel, { opacity: 0, duration: 0.15, ease: 'none' }, at + 0.62)
    }
    return at + 0.7
  }

  /** Text block entrance: rises 36 px and fades in. */
  function rise(tl, sel, at, opts = {}) {
    tl.fromTo(sel, { opacity: 0, y: opts.y ?? 36 }, { opacity: 1, y: 0, duration: opts.duration ?? 0.8, ease: opts.ease ?? EASE, stagger: opts.stagger ?? 0 }, at)
    return tl
  }

  /** The short rule under a title draws itself from the left. */
  function rule(tl, sel, at) {
    tl.fromTo(sel, { scaleX: 0 }, { scaleX: 1, duration: 0.7, ease: 'power2.out' }, at)
    return tl
  }

  /** Stroke drawing of SVG paths / lines / polylines (DrawSVG): from nothing to the full stroke. */
  function draw(tl, sel, at, opts = {}) {
    tl.fromTo(sel, { drawSVG: opts.from ?? '0%' }, { drawSVG: '100%', duration: opts.duration ?? 1, ease: opts.ease ?? 'power2.inOut', stagger: opts.stagger ?? 0 }, at)
    return tl
  }

  /** A figure counts up to `to` (textContent, formatted by `format`); deterministic under seek. */
  function countUp(tl, el, to, at, opts = {}) {
    const node = typeof el === 'string' ? document.querySelector(el) : el
    const fmt = opts.format || (v => num(v))
    const o = { v: opts.from ?? 0 }
    node.textContent = fmt(o.v)
    tl.to(o, { v: to, duration: opts.duration ?? 1.4, ease: opts.ease ?? 'power2.out', onUpdate: () => { node.textContent = fmt(o.v) } }, at)
    return tl
  }

  /* ── Network map (same geometry as the website's NetworkMap, viewBox 1120 × 680) ── */
  const MAP = window.WAPP_DATA.map
  const NODE_LO = [168, 224, 196], NODE_HI = [242, 177, 52]   // dark palette of the website: low price → high price
  const priceColor = (p, lo, hi) => {
    const x = hi > lo ? Math.min(1, Math.max(0, (p - lo) / (hi - lo))) : 0.5
    const c = NODE_LO.map((v, i) => Math.round(v + (NODE_HI[i] - v) * x))
    return `rgb(${c[0]},${c[1]},${c[2]})`
  }
  const NS = 'http://www.w3.org/2000/svg'
  const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e }

  /** Builds the network map into `container` (an <svg> element sized by the scene's CSS) and returns a handle.
   *  Element ids, all prefixed with `prefix`: `${prefix}-land` (group of country paths; members carry the class
   *  `member`), `${prefix}-c-<ISO>` (country path, e.g. -c-SEN), `${prefix}-lines` (group), `${prefix}-l-<U>-<V>` (line
   *  group with `.base`, `.flow` dashes and `.arrow`), `${prefix}-nodes` (group), `${prefix}-n-<Z>` (node group with
   *  `circle`, `.code`, `.price`), `${prefix}-leader-<Z>` (leader of an offset node).
   *  handle.setHour(h) paints prices, colours, widths, directions and saturated lines for hour h (call it at build
   *  time and from tween onUpdate callbacks); handle.dash(tl, from, to) runs the flow dashes over [from, to] s.
   *  opts: { hour (painted at build, default 19), neutral (true: no market yet, uniform nodes and lines, no price, no
   *  arrow; the dashes run along each line), showPrices (false: hide the price under each code) }. The SVG has no sea: it sits on
   *  the scene's ground; add the class wapp-map-fade to the <svg> to fade its rectangular edges. */
  function buildMap(svg, prefix, opts = {}) {
    const data = window.WAPP_DATA
    svg.setAttribute('viewBox', `0 0 ${MAP.width} ${MAP.height}`)
    const land = el('g', { id: `${prefix}-land` }, svg)
    for (const c of MAP.countries) el('path', { id: `${prefix}-c-${c.id}`, d: c.d, class: c.member ? 'member' : 'other', fill: c.member ? '#10493A' : '#0C352A', stroke: '#D7E8E1', 'stroke-width': c.member ? 1.6 : 1, 'stroke-opacity': c.member ? 0.5 : 0.22 }, land)
    const lines = el('g', { id: `${prefix}-lines` }, svg)
    const lineEls = {}
    for (const key of MAP.lines) {
      const [u, v] = key.split('->'); const [x1, y1] = MAP.nodes[u], [x2, y2] = MAP.nodes[v]
      const g = el('g', { id: `${prefix}-l-${u}-${v}` }, lines)
      const base = el('line', { class: 'base', x1, y1, x2, y2, stroke: '#8FD3B5', 'stroke-width': 4, 'stroke-linecap': 'round', 'stroke-opacity': 0.85 }, g)
      const flow = el('line', { class: 'flow', x1, y1, x2, y2, stroke: '#FFFFFF', 'stroke-width': 2.5, 'stroke-linecap': 'round', 'stroke-opacity': 0.75, 'stroke-dasharray': '10 18' }, g)
      const arrow = el('polygon', { class: 'arrow', points: '-10,-8 10,0 -10,8', fill: '#8FD3B5' }, g)
      lineEls[key] = { g, base, flow, arrow, u, v }
    }
    const nodes = el('g', { id: `${prefix}-nodes` }, svg)
    const nodeEls = {}
    for (const [z, [x, y]] of Object.entries(MAP.nodes)) {
      const [ax, ay] = MAP.anchors[z]
      if (ax !== x || ay !== y) {
        const lg = el('g', { id: `${prefix}-leader-${z}`, class: 'leader' }, nodes)
        el('line', { x1: ax, y1: ay, x2: x, y2: y, stroke: '#D7E8E1', 'stroke-width': 1.6, 'stroke-opacity': 0.6 }, lg)
        el('circle', { cx: ax, cy: ay, r: 3.6, fill: '#D7E8E1' }, lg)
      }
      const g = el('g', { id: `${prefix}-n-${z}`, class: 'node' }, nodes)
      const circle = el('circle', { cx: x, cy: y, r: MAP.nodeRadius, fill: '#A8E0C4', stroke: '#07241C', 'stroke-width': 3 }, g)
      const code = el('text', { class: 'code', x, y: y - 4, 'text-anchor': 'middle', 'font-size': 17, 'font-weight': 700, fill: '#07241C', 'font-family': 'Roboto, sans-serif' }, g)
      code.textContent = z
      const price = el('text', { class: 'price', x, y: y + 16, 'text-anchor': 'middle', 'font-size': 16, fill: '#0B3D30', 'font-family': 'JetBrains Mono, monospace' }, g)
      nodeEls[z] = { g, circle, code, price, x, y }
    }
    const handle = {
      svg, lineEls, nodeEls,
      /** Paints hour h: node colours and prices (scale of that hour), line widths, flow direction, saturated lines. */
      setHour(h) {
        const k = String(h)
        if (opts.neutral) {   // the region before any market: same colour everywhere, thin lines, no price, no flow
          for (const n of Object.values(nodeEls)) { n.circle.setAttribute('fill', '#A8E0C4'); n.price.textContent = ''; n.code.setAttribute('y', n.y + 6) }
          for (const L of Object.values(lineEls)) { L.base.setAttribute('stroke', '#8FD3B5'); L.base.setAttribute('stroke-width', 4); L.base.setAttribute('stroke-opacity', 0.85); L.arrow.style.display = 'none' }
          return { lo: 0, hi: 0 }
        }
        const vals = Object.keys(nodeEls).map(z => data.prices[z][k])
        const lo = Math.min(...vals), hi = Math.max(...vals)
        for (const [z, n] of Object.entries(nodeEls)) {
          const p = data.prices[z][k]
          n.circle.setAttribute('fill', priceColor(p, lo, hi))
          n.price.textContent = opts.showPrices === false ? '' : String(Math.round(p))
        }
        for (const [key, L] of Object.entries(lineEls)) {
          const f = data.flows[key][k] || 0, cap = data.ntc[key] || 1
          const sat = Math.abs(f) >= cap - 1
          const w = 3 + 10 * Math.min(1, Math.abs(f) / cap)
          const color = sat ? '#FF6B4A' : '#8FD3B5'
          L.base.setAttribute('stroke', color); L.base.setAttribute('stroke-width', w); L.base.setAttribute('stroke-opacity', Math.abs(f) < 1 ? 0.3 : 0.85)
          const [ux, uy] = MAP.nodes[L.u], [vx, vy] = MAP.nodes[L.v]
          const [fx1, fy1, fx2, fy2] = f >= 0 ? [ux, uy, vx, vy] : [vx, vy, ux, uy]
          for (const [a, b] of [['x1', fx1], ['y1', fy1], ['x2', fx2], ['y2', fy2]]) L.flow.setAttribute(a, b)
          L.flow.setAttribute('stroke-width', Math.max(2, w - 5))
          L.flow.style.display = Math.abs(f) < 1 ? 'none' : ''
          const mx = (fx1 + fx2) / 2, my = (fy1 + fy2) / 2, ang = Math.atan2(fy2 - fy1, fx2 - fx1) * 180 / Math.PI
          L.arrow.setAttribute('transform', `translate(${mx} ${my}) rotate(${ang})`)
          L.arrow.setAttribute('fill', color)
          L.arrow.style.display = Math.abs(f) < 1 ? 'none' : ''
        }
        return { lo, hi }
      },
      /** Flow dashes run from sender to receiver between `from` and `to` seconds of the scene timeline. */
      dash(tl, from, to) {
        const flows = Object.values(lineEls).map(L => L.flow)
        tl.fromTo(flows, { strokeDashoffset: 0 }, { strokeDashoffset: -28 * (to - from) * 1.6, duration: to - from, ease: 'none' }, from)
      },
    }
    handle.setHour(opts.hour ?? 19)
    return handle
  }

  window.WAPP = { lang, t, data: window.WAPP_DATA, zoneName, num, money, hour, hh, wipeIn, rise, rule, draw, countUp, buildMap, priceColor, EASE }
})()
