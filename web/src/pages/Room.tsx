import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, fmt, session, type Block, type Demand, type Mic, type MyResult, type OrderBook, type Participant, type RoomInfo, type Run, type Supply } from '../api'
import { useT } from '../i18n'
import { Badge, Bars, Button, Empty, ErrorBox, Header, Kpi, Panel, Tabs } from '../components/ui'
import NetworkMap from '../components/NetworkMap'
import { PriceChart, DispatchChart, FlowChart } from '../components/Charts'
import { useRoomEvents } from '../hooks'

const PROFILES = ['baseload', 'hydro', 'solar', 'peaker', 'flat']
const EMPTY: OrderBook = { supply: [], demand: [], blocks: [], mic: [] }
type TabKey = 'supply' | 'demand' | 'blocks' | 'mic'
type ViewKey = 'map' | 'prices' | 'dispatch' | 'flows'
const CORRIDORS = ['NGA->BEN', 'NGA->NER', 'GHA->CIV', 'GHA->BFA', 'CIV->BFA', 'CIV->MLI', 'CIV->LBR', 'SEN->MLI']
const hh = (h: number) => `H${String(h).padStart(2, '0')}`

export default function Room() {
  const { code = '' } = useParams(); const t = useT()
  const token = session.token(code, 'member'); const trainerToken = session.token(code, 'trainer')
  const [room, setRoom] = useState<RoomInfo | null>(null)
  const [me, setMe] = useState<Participant | null>(null)
  const [book, setBook] = useState<OrderBook>(EMPTY)
  const [tab, setTab] = useState<TabKey>('supply')
  const [view, setView] = useState<ViewKey>('map')
  const [live, setLive] = useState(false)
  const [run, setRun] = useState<Run | null>(null)
  const [mine, setMine] = useState<MyResult | null>(null)
  const [hour, setHour] = useState<number>(19)
  const [err, setErr] = useState<string | null>(null); const [savedAt, setSavedAt] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const r = await api.room(code); setRoom(r)
      if (r.last_run_id) {
        const lr = await api.latest(code); setRun(lr)
        const hs: number[] = lr.result.summary.hours
        setHour(h => (hs.includes(h) ? h : hs[Math.min(19, hs.length - 1)]))
        if (token) setMine(await api.myResult(code, token))
      }
    } catch (ex: any) { setErr(ex.message) }
  }, [code, token])

  useEffect(() => {
    if (!token) return
    api.myOrders(code, token).then(b => { setMe(b.participant); setBook({ supply: b.supply, demand: b.demand, blocks: b.blocks, mic: b.mic }) }).catch(e => setErr(e.message))
    load()
  }, [code, token, load])
  useRoomEvents(code, () => { setLive(true); load() })

  if (!token) return <div className="p-10 text-lg">{t('join_room')} : <a className="text-accent font-medium" href={`/?code=${code}`}>{code}</a></div>
  const cur = room?.settings.currency || 'USD'; const unit = `${cur}/MWh`
  const open = room?.phase === 'submission' && me?.role === 'trader'

  const save = async () => {
    setErr(null)
    try { await api.putOrders(code, token, book); setSavedAt(new Date().toLocaleTimeString()); load() } catch (ex: any) { setErr(ex.message) }
  }
  const upd = <K extends TabKey>(k: K, i: number, patch: Partial<OrderBook[K][number]>) =>
    setBook(b => ({ ...b, [k]: (b[k] as any[]).map((row, j) => (j === i ? { ...row, ...patch } : row)) }))
  const del = (k: TabKey, i: number) => setBook(b => ({ ...b, [k]: (b[k] as any[]).filter((_, j) => j !== i) }))
  const add = (k: TabKey) => setBook(b => ({
    ...b, [k]: [...(b[k] as any[]), k === 'supply' ? ({ actor: '', segment: 0, quantity: 100, price: 50, profile: 'baseload' } as Supply)
      : k === 'demand' ? ({ actor: '', segment: 0, quantity: 200, price: 150 } as Demand)
      : k === 'blocks' ? ({ name: '', side: 'S', quantity: 100, price: 40, h_start: 0, h_end: 23 } as Block)
      : ({ actor: '', fixed_term: 0, variable_term: 0 } as Mic)],
  }))

  const summary = run?.result?.summary
  const prices = run?.result?.prices as Record<string, Record<string, number>> | undefined
  const flows = run?.result?.flows as Record<string, Record<string, number>> | undefined
  const zones: string[] = prices ? Object.keys(prices) : []
  const hours: number[] = summary?.hours || []
  const sold = mine?.actors.filter(a => a.side === 'S') || []; const bought = mine?.actors.filter(a => a.side === 'D') || []
  const sum = (xs: any[], k: string) => xs.reduce((s, a) => s + (a[k] || 0), 0)
  const removeBtn = (k: TabKey, i: number) => open && <button className="text-ink-3 hover:text-down text-lg leading-none" onClick={() => del(k, i)} aria-label={t('remove')}>×</button>
  const addBtn = (k: TabKey) => open && <Button small onClick={() => add(k)}>+ {t('add')}</Button>

  return (
    <div className="min-h-screen">
      <Header title={room?.name || code} code={code} phase={room?.phase}
        meta={`${t('delivery')} ${room?.settings.market_date || ''} · ${room?.settings.hours.length === 24 ? t('hours24') : hh(room?.settings.hours[0] ?? 0)} · ${me?.name || ''}${me?.zone ? ` (${me.zone})` : ''}`}
        switchTo={trainerToken ? { label: t('switch_desk'), to: `/desk/${code}` } : undefined} />
      <main className="p-5 grid gap-5 xl:grid-cols-[minmax(0,5fr)_minmax(0,5fr)_minmax(0,3fr)]">
        <Panel title={<>{t('my_orders')} {me?.zone && <Badge tone="accent">{me.zone}</Badge>}</>}
          right={open ? <><span className="text-sm text-ink-3">{savedAt ? `${t('saved_at')} ${savedAt}` : ''}</span><Button primary onClick={save}>{t('save')}</Button></> : <Badge>{t('closed_hint')}</Badge>}>
          <ErrorBox message={err} />
          <Tabs tabs={[{ key: 'supply', label: t('supply'), count: book.supply.length }, { key: 'demand', label: t('demand'), count: book.demand.length }, { key: 'blocks', label: t('blocks'), count: book.blocks.length }, { key: 'mic', label: 'MIC', count: book.mic.length }]} active={tab} onChange={setTab} />

          {tab === 'supply' && (book.supply.length === 0 ? <Empty action={addBtn('supply')}>{t('empty_supply')}</Empty> : <>
            <table><thead><tr><th>{t('actor')}</th><th>{t('segment')}</th><th>{t('mw')}</th><th>{unit}</th><th>{t('profile')}</th><th /></tr></thead><tbody>
              {book.supply.map((r, i) => <tr key={i}>
                <td><input value={r.actor} onChange={e => upd('supply', i, { actor: e.target.value })} disabled={!open} className="w-40" placeholder="Centrale" /></td>
                <td><input type="number" min={0} max={3} value={r.segment} onChange={e => upd('supply', i, { segment: +e.target.value })} disabled={!open} className="w-14" /></td>
                <td><input type="number" min={0} value={r.quantity} onChange={e => upd('supply', i, { quantity: +e.target.value })} disabled={!open} className="w-24" /></td>
                <td><input type="number" min={0} max={500} value={r.price} onChange={e => upd('supply', i, { price: +e.target.value })} disabled={!open} className="w-24" /></td>
                <td><select value={r.profile} onChange={e => upd('supply', i, { profile: e.target.value })} disabled={!open}>{PROFILES.map(p => <option key={p}>{p}</option>)}</select></td>
                <td className="text-right">{removeBtn('supply', i)}</td>
              </tr>)}
            </tbody></table><div className="mt-3">{addBtn('supply')}</div></>)}

          {tab === 'demand' && (book.demand.length === 0 ? <Empty action={addBtn('demand')}>{t('empty_demand')}</Empty> : <>
            <table><thead><tr><th>{t('actor')}</th><th>{t('segment')}</th><th>{t('mw')}</th><th>{unit}</th><th /></tr></thead><tbody>
              {book.demand.map((r, i) => <tr key={i}>
                <td><input value={r.actor} onChange={e => upd('demand', i, { actor: e.target.value })} disabled={!open} className="w-40" placeholder="Réseau" /></td>
                <td><input type="number" min={0} max={3} value={r.segment} onChange={e => upd('demand', i, { segment: +e.target.value })} disabled={!open} className="w-14" /></td>
                <td><input type="number" min={0} value={r.quantity} onChange={e => upd('demand', i, { quantity: +e.target.value })} disabled={!open} className="w-24" /></td>
                <td><input type="number" min={0} max={500} value={r.price} onChange={e => upd('demand', i, { price: +e.target.value })} disabled={!open} className="w-24" /></td>
                <td className="text-right">{removeBtn('demand', i)}</td>
              </tr>)}
            </tbody></table><div className="mt-3">{addBtn('demand')}</div></>)}

          {tab === 'blocks' && (book.blocks.length === 0 ? <Empty action={addBtn('blocks')}>{t('empty_blocks')}</Empty> : <>
            <table><thead><tr><th>{t('actor')}</th><th>{t('side')}</th><th>{t('mw')}</th><th>{unit}</th><th>{t('start')}</th><th>{t('end')}</th><th>{t('parent')}</th><th>{t('group')}</th><th /></tr></thead><tbody>
              {book.blocks.map((r, i) => <tr key={i}>
                <td><input value={r.name} onChange={e => upd('blocks', i, { name: e.target.value })} disabled={!open} className="w-32" /></td>
                <td><select value={r.side} onChange={e => upd('blocks', i, { side: e.target.value as 'S' | 'D' })} disabled={!open}><option value="S">{t('supply')}</option><option value="D">{t('demand')}</option></select></td>
                <td><input type="number" min={0} value={r.quantity} onChange={e => upd('blocks', i, { quantity: +e.target.value })} disabled={!open} className="w-20" /></td>
                <td><input type="number" min={0} max={500} value={r.price} onChange={e => upd('blocks', i, { price: +e.target.value })} disabled={!open} className="w-20" /></td>
                <td><input type="number" min={0} max={23} value={r.h_start} onChange={e => upd('blocks', i, { h_start: +e.target.value })} disabled={!open} className="w-14" /></td>
                <td><input type="number" min={0} max={23} value={r.h_end} onChange={e => upd('blocks', i, { h_end: +e.target.value })} disabled={!open} className="w-14" /></td>
                <td><input value={r.parent_name || ''} onChange={e => upd('blocks', i, { parent_name: e.target.value || null })} disabled={!open} className="w-24" /></td>
                <td><input value={r.excl_group || ''} onChange={e => upd('blocks', i, { excl_group: e.target.value || null })} disabled={!open} className="w-14" /></td>
                <td className="text-right">{removeBtn('blocks', i)}</td>
              </tr>)}
            </tbody></table><div className="mt-3">{addBtn('blocks')}</div></>)}

          {tab === 'mic' && (book.mic.length === 0 ? <Empty action={addBtn('mic')}>{t('empty_mic')}</Empty> : <>
            <table><thead><tr><th>{t('actor')}</th><th>{t('fixed')} ({cur})</th><th>{t('variable')} ({unit})</th><th /></tr></thead><tbody>
              {book.mic.map((r, i) => <tr key={i}>
                <td><input value={r.actor} onChange={e => upd('mic', i, { actor: e.target.value })} disabled={!open} className="w-40" /></td>
                <td><input type="number" min={0} value={r.fixed_term} onChange={e => upd('mic', i, { fixed_term: +e.target.value })} disabled={!open} className="w-28" /></td>
                <td><input type="number" min={0} value={r.variable_term} onChange={e => upd('mic', i, { variable_term: +e.target.value })} disabled={!open} className="w-24" /></td>
                <td className="text-right">{removeBtn('mic', i)}</td>
              </tr>)}
            </tbody></table><div className="mt-3">{addBtn('mic')}</div></>)}
          <p className="text-sm text-ink-3 mt-4">{t('order_book_hint')}</p>
        </Panel>

        <Panel title={`${t('market')} · ${t('last_clearing')}`} right={<>{live && <Badge tone="up">{t('live')}</Badge>}{run && <>{(summary?.reference_zones?.length || 0) > 0 && <Badge tone="warn">{t('reference_badge')} · {summary.reference_zones.length} {t('zones_word')}</Badge>}<span className="text-sm text-ink-3">#{run.id} · {new Date(run.run_at).toLocaleTimeString()}</span></>}</>}>
          {!run || !prices || !flows ? <Empty>{t('waiting_clearing')}</Empty> : <>
            <div className="grid grid-cols-3 gap-3 mb-4">
              <Kpi label={t('welfare')} value={fmt.money(run.welfare / 1e6, 'M ' + cur)} />
              <Kpi label={t('volume')} value={`${fmt.n(run.volume / 1000, 1)} GWh`} />
              <div className="bg-panel rounded-lg px-4 py-3"><div className="text-xs uppercase tracking-wide text-ink-3 mb-1">{t('hour')}</div>
                <select value={hour} onChange={e => setHour(+e.target.value)} className="h-8 w-full font-mono">{hours.map(h => <option key={h} value={h}>{hh(h)}</option>)}</select></div>
            </div>
            <Tabs tabs={[{ key: 'map', label: t('tab_map') }, { key: 'prices', label: t('tab_prices') }, { key: 'dispatch', label: t('tab_dispatch') }, { key: 'flows', label: t('tab_flows') }]} active={view} onChange={setView} />
            <div className="rounded-lg bg-panel p-2 mb-4">
              {view === 'map' && <NetworkMap prices={prices} flows={flows} ntc={room?.ntc || {}} hour={hour} selected={me?.zone} unit={unit} />}
              {view === 'prices' && <PriceChart prices={prices} hours={hours} highlight={me?.zone} unit={unit} />}
              {view === 'dispatch' && <DispatchChart dispatch={run.result.dispatch} hours={hours} label={k => t('p_' + k)} />}
              {view === 'flows' && <FlowChart flows={flows} hours={hours} ntc={room?.ntc || {}} corridors={CORRIDORS} />}
            </div>
            <table><thead><tr><th>{t('zone')}</th><th className="text-right">{t('prices_at')} {hh(hour)}</th><th className="text-right">{t('avg24')}</th><th className="text-right">{t('position')} (MWh)</th><th className="w-24">24 h</th></tr></thead><tbody>
              {zones.map(z => {
                const series = hours.map(h => prices[z][String(h)]); const net = summary.net_pos[z] as number
                return <tr key={z} className={z === me?.zone ? 'bg-accent-soft/60' : ''}>
                  <td className="font-semibold">{z}</td>
                  <td className="num">{fmt.n(prices[z][String(hour)], 1)}</td>
                  <td className="num text-ink-2">{fmt.n(series.reduce((a, b) => a + b, 0) / series.length, 1)}</td>
                  <td className={`num ${net >= 0 ? 'text-up' : 'text-down'}`}>{net >= 0 ? '+' : ''}{fmt.n(net)}</td>
                  <td><Bars values={series} labels={hours} height={22} /></td>
                </tr>
              })}
            </tbody></table>
          </>}
        </Panel>

        <Panel title={t('my_result')}>
          {!mine ? <Empty>{t('waiting_clearing')}</Empty> : <>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <Kpi label={t('sold')} value={`${fmt.n(sum(sold, 'accepted_mwh'))} MWh`} sub={`${t('offered')} ${fmt.n(sum(sold, 'offered_mwh'))}`} />
              <Kpi label={t('bought')} value={`${fmt.n(sum(bought, 'accepted_mwh'))} MWh`} sub={`${t('offered')} ${fmt.n(sum(bought, 'offered_mwh'))}`} />
              <Kpi label={t('surplus')} value={fmt.money(sum(mine.actors, 'surplus'), cur)} tone={sum(mine.actors, 'surplus') >= 0 ? 'up' : 'down'} />
              <Kpi label={t('rejected')} value={mine.actors.reduce((n, a) => n + (a.rejected?.length || 0), 0)} />
            </div>
            <table><thead><tr><th>{t('actor')}</th><th className="text-right">{t('accepted')}</th><th className="text-right">{t('avg_price')}</th><th className="text-right">{t('surplus')}</th></tr></thead><tbody>
              {mine.actors.map((a, i) => <tr key={i}>
                <td><div className="font-medium">{a.actor}</div><div className="text-xs text-ink-3">{a.side === 'S' ? t('supply') : t('demand')}{a.status === 'withdrawn_mic' && <span className="text-warn"> · {t('withdrawn')}</span>}</div></td>
                <td className="num">{fmt.n(a.accepted_mwh)}<span className="text-ink-3"> / {fmt.n(a.offered_mwh)}</span></td>
                <td className="num">{fmt.n(a.avg_price, 1)}</td>
                <td className={`num ${a.surplus >= 0 ? 'text-up' : 'text-down'}`}>{fmt.n(a.surplus)}</td>
              </tr>)}
            </tbody></table>
            {mine.blocks.length > 0 && <table className="mt-4"><thead><tr><th>{t('blocks')}</th><th>{t('status')}</th></tr></thead><tbody>
              {mine.blocks.map((b, i) => <tr key={i}><td>{b.name} <span className="text-ink-3 text-sm">{b.accepted ? t('accepted') : t('rejected')}</span></td><td><Badge tone={b.status === 'OK' ? 'up' : b.status === 'PAB' ? 'down' : 'warn'}>{b.status}</Badge></td></tr>)}
            </tbody></table>}
            {me?.zone && <div className="mt-5"><h3 className="mb-2">{me.zone} · {unit}</h3><Bars values={hours.map(h => mine.zone_prices[String(h)] || 0)} labels={hours} height={56} /></div>}
          </>}
        </Panel>
      </main>
    </div>
  )
}
