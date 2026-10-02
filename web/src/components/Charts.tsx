/** Graphiques ECharts (rendu SVG, modules réduits) : prix par zone, dispatch empilé, flux par ligne. */
import { useEffect, useRef } from 'react'
import * as echarts from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { SVGRenderer } from 'echarts/renderers'

echarts.use([LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, SVGRenderer])

export const ZONE_COLORS: Record<string, string> = {
  NGA: '#B5443C', BEN: '#D97B2B', TGO: '#C9A227', GHA: '#3C8C4E', CIV: '#1F8A8A', BFA: '#2F6DB3', MLI: '#6F5BB5',
  SEN: '#A63D7A', GIN: '#D2607E', SLE: '#2A9DB5', LBR: '#7FA33A', GNB: '#E07B39', GMB: '#6B7280', NER: '#8B5E3C',
}
const PROFILE_COLORS: Record<string, string> = { solar: '#E2B93B', hydro: '#3B8BD4', baseload: '#4FA36C', flat: '#9B7BD1', custom: '#9CA3AF', peaker: '#D85A30', block: '#0F6E56' }
const FONT = 'Inter, ui-sans-serif, system-ui, sans-serif'
const hh = (h: number) => `H${String(h).padStart(2, '0')}`

export function Chart({ option, height = 300 }: { option: echarts.EChartsCoreOption; height?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current) return
    const inst = echarts.init(ref.current, undefined, { renderer: 'svg' })
    inst.setOption({ textStyle: { fontFamily: FONT }, ...option }, true)
    const ro = new ResizeObserver(() => inst.resize()); ro.observe(ref.current)
    return () => { ro.disconnect(); inst.dispose() }
  }, [option])
  return <div ref={ref} style={{ height }} />
}

const base = (unit: string) => ({
  grid: { left: 48, right: 16, top: 24, bottom: 56, containLabel: false },
  tooltip: { trigger: 'axis', valueFormatter: (v: any) => (typeof v === 'number' ? `${Math.round(v * 10) / 10} ${unit}` : v) },
  legend: { bottom: 0, type: 'scroll', itemWidth: 14, textStyle: { fontSize: 12, color: '#5C5B56' } },
  xAxis: { type: 'category', axisLine: { lineStyle: { color: '#C8C6BE' } }, axisLabel: { color: '#5C5B56', fontSize: 11 } },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#E2E0D9' } }, axisLabel: { color: '#5C5B56', fontSize: 11 } },
})

export function PriceChart({ prices, hours, highlight, unit }: { prices: Record<string, Record<string, number>>; hours: number[]; highlight?: string | null; unit: string }) {
  const option: echarts.EChartsCoreOption = {
    ...base(unit),
    xAxis: { ...base(unit).xAxis, data: hours.map(hh) },
    series: Object.keys(prices).map(z => ({
      name: z, type: 'line', showSymbol: false, step: 'middle',
      lineStyle: { width: z === highlight ? 3.5 : 1.5, color: ZONE_COLORS[z] || '#888' },
      itemStyle: { color: ZONE_COLORS[z] || '#888' }, emphasis: { focus: 'series' },
      data: hours.map(h => prices[z][String(h)]),
    })),
  }
  return <Chart option={option} height={320} />
}

export function DispatchChart({ dispatch, hours, label }: { dispatch: Record<string, number[]>; hours: number[]; label: (k: string) => string }) {
  const order = ['solar', 'hydro', 'baseload', 'flat', 'custom', 'peaker', 'block']
  const option: echarts.EChartsCoreOption = {
    ...base('MW'),
    xAxis: { ...base('MW').xAxis, data: hours.map(hh) },
    series: [
      ...order.filter(k => dispatch[k] && dispatch[k].some(v => v > 0)).map(k => ({
        name: label(k), type: 'bar', stack: 'gen', barCategoryGap: '25%', itemStyle: { color: PROFILE_COLORS[k] }, data: dispatch[k].map(v => Math.round(v)),
      })),
      { name: label('demand'), type: 'line', step: 'middle', showSymbol: false, lineStyle: { color: '#1B1B19', width: 2, type: 'dashed' }, itemStyle: { color: '#1B1B19' }, data: (dispatch.demand || []).map(v => Math.round(v)) },
    ],
  }
  return <Chart option={option} height={320} />
}

export function FlowChart({ flows, hours, ntc, corridors }: { flows: Record<string, Record<string, number>>; hours: number[]; ntc: Record<string, number>; corridors: string[] }) {
  const palette = ['#0F6E56', '#2F6DB3', '#D97B2B', '#A63D7A', '#6F5BB5', '#B5443C', '#2A9DB5', '#7FA33A']
  const option: echarts.EChartsCoreOption = {
    ...base('MW'),
    tooltip: { trigger: 'axis', valueFormatter: (v: any) => `${Math.round(v)} MW` },
    xAxis: { ...base('MW').xAxis, data: hours.map(hh) },
    series: corridors.filter(c => flows[c]).map((c, i) => ({
      name: `${c} (NTC ${ntc[c] ?? '?'})`, type: 'line', step: 'middle', showSymbol: false,
      lineStyle: { width: 2, color: palette[i % palette.length] }, itemStyle: { color: palette[i % palette.length] },
      data: hours.map(h => flows[c][String(h)]),
    })),
  }
  return <Chart option={option} height={320} />
}
