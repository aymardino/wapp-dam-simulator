import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, fmt, session, type Block, type Demand, type Mic, type MyResult, type OrderBook, type Participant, type RoomInfo, type Run, type Supply } from '../api'
import { useT } from '../i18n'
import { Badge, Bars, Button, ErrorBox, Section, Stat, TopBar } from '../components/ui'

const PROFILES = ['baseload', 'hydro', 'solar', 'peaker', 'flat']
const EMPTY: OrderBook = { supply: [], demand: [], blocks: [], mic: [] }

export default function Room() {
  const { code = '' } = useParams(); const t = useT()
  const token = session.token(code)
  const [room, setRoom] = useState<RoomInfo | null>(null)
  const [me, setMe] = useState<Participant | null>(null)
  const [book, setBook] = useState<OrderBook>(EMPTY)
  const [run, setRun] = useState<Run | null>(null)
  const [mine, setMine] = useState<MyResult | null>(null)
  const [hour, setHour] = useState<number>(19)
  const [err, setErr] = useState<string | null>(null); const [saved, setSaved] = useState(false)

  const load = useCallback(async () => {
    try {
      const r = await api.room(code); setRoom(r)
      if (r.last_run_id) {
        const lr = await api.latest(code); setRun(lr)
        if (!lr.result.summary.hours.includes(hour)) setHour(lr.result.summary.hours[Math.min(19, lr.result.summary.hours.length - 1)])
        if (token) setMine(await api.myResult(code, token))
      }
    } catch (ex: any) { setErr(ex.message) }
  }, [code, token])

  useEffect(() => {
    if (!token) return
    api.myOrders(code, token).then(b => { setMe(b.participant); setBook({ supply: b.supply, demand: b.demand, blocks: b.blocks, mic: b.mic }) }).catch(e => setErr(e.message))
    load()
    const id = setInterval(load, 10000)
    return () => clearInterval(id)
  }, [code, token, load])

  if (!token) return <div className="p-8">{t('join_room')} : <a className="text-accent" href="/">/</a></div>
  const cur = room?.settings.currency || 'USD'
  const open = room?.phase === 'submission' && me?.role === 'trader'

  const save = async () => {
    setErr(null); setSaved(false)
    try { await api.putOrders(code, token, book); setSaved(true); load() } catch (ex: any) { setErr(ex.message) }
  }
  const upd = <K extends keyof OrderBook>(k: K, i: number, patch: Partial<OrderBook[K][number]>) =>
    setBook(b => ({ ...b, [k]: (b[k] as any[]).map((row, j) => (j === i ? { ...row, ...patch } : row)) }))
  const del = (k: keyof OrderBook, i: number) => setBook(b => ({ ...b, [k]: (b[k] as any[]).filter((_, j) => j !== i) }))
  const add = (k: keyof OrderBook) => setBook(b => ({
    ...b, [k]: [...(b[k] as any[]), k === 'supply' ? ({ actor: '', segment: 0, quantity: 100, price: 50, profile: 'baseload' } as Supply)
      : k === 'demand' ? ({ actor: '', segment: 0, quantity: 200, price: 150 } as Demand)
      : k === 'blocks' ? ({ name: '', side: 'S', quantity: 100, price: 40, h_start: 0, h_end: 23 } as Block)
      : ({ actor: '', fixed_term: 0, variable_term: 0 } as Mic)],
  }))

  const summary = run?.result?.summary
  const prices = run?.result?.prices as Record<string, Record<string, number>> | undefined
  const zones: string[] = prices ? Object.keys(prices) : []
  const hours: number[] = summary?.hours || []
  const sold = mine?.actors.filter(a => a.side === 'S') || []; const bought = mine?.actors.filter(a => a.side === 'D') || []
  const sum = (xs: any[], k: string) => xs.reduce((s, a) => s + (a[k] || 0), 0)

  return (
    <div className="min-h-screen">
      <TopBar title={room?.name || code} meta={`${t('delivery')} ${room?.settings.market_date || ''} · ${room?.settings.hours.length === 24 ? t('hours24') : `${t('hour')} ${room?.settings.hours[0]}`}`} phase={room?.phase} />
      <main className="grid lg:grid-cols-[1.1fr_1.3fr_0.9fr] gap-0 divide-x divide-line">
        <section className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h2>{t('my_orders')} · {me?.name} {me?.zone && <Badge tone="accent">{me.zone}</Badge>}</h2>
            {open ? <Button primary onClick={save}>{t('save')}</Button> : <Badge>{t('closed_hint')}</Badge>}
          </div>
          <ErrorBox message={err} />
          {saved && <div className="text-xs text-up mb-2">{t('saved')}</div>}

          <h3 className="text-xs text-ink-3 mt-2 mb-1">{t('supply')}</h3>
          <table><thead><tr><th>{t('actor')}</th><th>{t('segment')}</th><th>{t('mw')}</th><th>{cur}/MWh</th><th>{t('profile')}</th><th /></tr></thead><tbody>
            {book.supply.map((r, i) => <tr key={i}>
              <td><input value={r.actor} onChange={e => upd('supply', i, { actor: e.target.value })} disabled={!open} className="w-32" /></td>
              <td><input type="number" min={0} max={3} value={r.segment} onChange={e => upd('supply', i, { segment: +e.target.value })} disabled={!open} className="w-12" /></td>
              <td><input type="number" min={0} value={r.quantity} onChange={e => upd('supply', i, { quantity: +e.target.value })} disabled={!open} className="w-20" /></td>
              <td><input type="number" min={0} max={500} value={r.price} onChange={e => upd('supply', i, { price: +e.target.value })} disabled={!open} className="w-20" /></td>
              <td><select value={r.profile} onChange={e => upd('supply', i, { profile: e.target.value })} disabled={!open}>{PROFILES.map(p => <option key={p}>{p}</option>)}</select></td>
              <td>{open && <button className="text-ink-3" onClick={() => del('supply', i)}>×</button>}</td>
            </tr>)}
          </tbody></table>
          {open && <button className="text-xs text-accent mt-1" onClick={() => add('supply')}>+ {t('add')}</button>}

          <h3 className="text-xs text-ink-3 mt-4 mb-1">{t('demand')}</h3>
          <table><thead><tr><th>{t('actor')}</th><th>{t('segment')}</th><th>{t('mw')}</th><th>{cur}/MWh</th><th /></tr></thead><tbody>
            {book.demand.map((r, i) => <tr key={i}>
              <td><input value={r.actor} onChange={e => upd('demand', i, { actor: e.target.value })} disabled={!open} className="w-32" /></td>
              <td><input type="number" min={0} max={3} value={r.segment} onChange={e => upd('demand', i, { segment: +e.target.value })} disabled={!open} className="w-12" /></td>
              <td><input type="number" min={0} value={r.quantity} onChange={e => upd('demand', i, { quantity: +e.target.value })} disabled={!open} className="w-20" /></td>
              <td><input type="number" min={0} max={500} value={r.price} onChange={e => upd('demand', i, { price: +e.target.value })} disabled={!open} className="w-20" /></td>
              <td>{open && <button className="text-ink-3" onClick={() => del('demand', i)}>×</button>}</td>
            </tr>)}
          </tbody></table>
          {open && <button className="text-xs text-accent mt-1" onClick={() => add('demand')}>+ {t('add')}</button>}

          <h3 className="text-xs text-ink-3 mt-4 mb-1">{t('blocks')}</h3>
          <table><thead><tr><th>{t('actor')}</th><th>{t('side')}</th><th>{t('mw')}</th><th>{cur}/MWh</th><th>{t('start')}</th><th>{t('end')}</th><th>{t('parent')}</th><th>{t('group')}</th><th /></tr></thead><tbody>
            {book.blocks.map((r, i) => <tr key={i}>
              <td><input value={r.name} onChange={e => upd('blocks', i, { name: e.target.value })} disabled={!open} className="w-28" /></td>
              <td><select value={r.side} onChange={e => upd('blocks', i, { side: e.target.value as 'S' | 'D' })} disabled={!open}><option value="S">{t('supply')}</option><option value="D">{t('demand')}</option></select></td>
              <td><input type="number" min={0} value={r.quantity} onChange={e => upd('blocks', i, { quantity: +e.target.value })} disabled={!open} className="w-16" /></td>
              <td><input type="number" min={0} max={500} value={r.price} onChange={e => upd('blocks', i, { price: +e.target.value })} disabled={!open} className="w-16" /></td>
              <td><input type="number" min={0} max={23} value={r.h_start} onChange={e => upd('blocks', i, { h_start: +e.target.value })} disabled={!open} className="w-12" /></td>
              <td><input type="number" min={0} max={23} value={r.h_end} onChange={e => upd('blocks', i, { h_end: +e.target.value })} disabled={!open} className="w-12" /></td>
              <td><input value={r.parent_name || ''} onChange={e => upd('blocks', i, { parent_name: e.target.value || null })} disabled={!open} className="w-20" /></td>
              <td><input value={r.excl_group || ''} onChange={e => upd('blocks', i, { excl_group: e.target.value || null })} disabled={!open} className="w-12" /></td>
              <td>{open && <button className="text-ink-3" onClick={() => del('blocks', i)}>×</button>}</td>
            </tr>)}
          </tbody></table>
          {open && <button className="text-xs text-accent mt-1" onClick={() => add('blocks')}>+ {t('add')}</button>}

          <h3 className="text-xs text-ink-3 mt-4 mb-1">{t('mic')}</h3>
          <table><thead><tr><th>{t('actor')}</th><th>{t('fixed')} ({cur})</th><th>{t('variable')}</th><th /></tr></thead><tbody>
            {book.mic.map((r, i) => <tr key={i}>
              <td><input value={r.actor} onChange={e => upd('mic', i, { actor: e.target.value })} disabled={!open} className="w-32" /></td>
              <td><input type="number" min={0} value={r.fixed_term} onChange={e => upd('mic', i, { fixed_term: +e.target.value })} disabled={!open} className="w-24" /></td>
              <td><input type="number" min={0} value={r.variable_term} onChange={e => upd('mic', i, { variable_term: +e.target.value })} disabled={!open} className="w-20" /></td>
              <td>{open && <button className="text-ink-3" onClick={() => del('mic', i)}>×</button>}</td>
            </tr>)}
          </tbody></table>
          {open && <button className="text-xs text-accent mt-1" onClick={() => add('mic')}>+ {t('add')}</button>}
        </section>

        <section className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h2>{t('market')} · {t('last_clearing')}</h2>
            {run && <span className="text-xs text-ink-3">#{run.id} · {new Date(run.run_at).toLocaleTimeString()}</span>}
          </div>
          {!run ? <p className="text-ink-2">{t('no_clearing')}</p> : <>
            <div className="grid grid-cols-3 gap-2 mb-4">
              <Stat label={t('welfare')} value={fmt.money(run.welfare / 1e6, 'M ' + cur)} />
              <Stat label={t('volume')} value={`${fmt.n(run.volume / 1000, 1)} GWh`} />
              <Stat label={t('hour')} value={<select value={hour} onChange={e => setHour(+e.target.value)} className="h-7 text-base">{hours.map(h => <option key={h} value={h}>{`H${String(h).padStart(2, '0')}`}</option>)}</select>} />
            </div>
            <table><thead><tr><th>{t('zone')}</th><th className="text-right">{t('price')} {`H${String(hour).padStart(2, '0')}`}</th><th className="text-right">{t('avg24')}</th><th className="text-right">{t('position')} (MWh)</th><th>24 h</th></tr></thead><tbody>
              {zones.map(z => {
                const series = hours.map(h => prices![z][String(h)])
                const net = summary.net_pos[z] as number
                return <tr key={z} className={z === me?.zone ? 'bg-panel' : ''}>
                  <td className="font-medium">{z}</td>
                  <td className="num">{fmt.n(prices![z][String(hour)], 1)}</td>
                  <td className="num">{fmt.n(series.reduce((a, b) => a + b, 0) / series.length, 1)}</td>
                  <td className={`num ${net >= 0 ? 'text-up' : 'text-down'}`}>{net >= 0 ? '+' : ''}{fmt.n(net)}</td>
                  <td className="w-28"><Bars values={series} labels={hours} height={24} /></td>
                </tr>
              })}
            </tbody></table>
          </>}
        </section>

        <section className="p-4">
          <h2 className="mb-3">{t('my_result')}</h2>
          {!mine ? <p className="text-ink-2">{t('no_clearing')}</p> : <>
            <div className="grid grid-cols-2 gap-2 mb-3">
              <Stat label={t('sold')} value={`${fmt.n(sum(sold, 'accepted_mwh'))} MWh`} sub={`${t('offered')} ${fmt.n(sum(sold, 'offered_mwh'))}`} />
              <Stat label={t('bought')} value={`${fmt.n(sum(bought, 'accepted_mwh'))} MWh`} sub={`${t('offered')} ${fmt.n(sum(bought, 'offered_mwh'))}`} />
              <Stat label={t('surplus')} value={fmt.money(sum(mine.actors, 'surplus'), cur)} />
              <Stat label={t('rejected')} value={mine.actors.reduce((n, a) => n + (a.rejected?.length || 0), 0)} />
            </div>
            <table><thead><tr><th>{t('actor')}</th><th>{t('side')}</th><th className="text-right">{t('accepted')}</th><th className="text-right">{t('avg_price')}</th><th className="text-right">{t('surplus')}</th></tr></thead><tbody>
              {mine.actors.map((a, i) => <tr key={i}>
                <td>{a.actor}{a.status === 'withdrawn_mic' && <span className="text-xs text-warn"> · {t('withdrawn')}</span>}</td>
                <td>{a.side === 'S' ? t('supply') : t('demand')}</td>
                <td className="num">{fmt.n(a.accepted_mwh)} / {fmt.n(a.offered_mwh)}</td>
                <td className="num">{fmt.n(a.avg_price, 1)}</td>
                <td className={`num ${a.surplus >= 0 ? 'text-up' : 'text-down'}`}>{fmt.n(a.surplus)}</td>
              </tr>)}
            </tbody></table>
            {mine.blocks.length > 0 && <>
              <h3 className="text-xs text-ink-3 mt-4 mb-1">{t('blocks')}</h3>
              <table><tbody>{mine.blocks.map((b, i) => <tr key={i}><td>{b.name}</td><td>{b.accepted ? t('accepted') : t('rejected')}</td><td><Badge tone={b.status === 'OK' ? 'up' : b.status === 'PAB' ? 'down' : 'warn'}>{b.status}</Badge></td></tr>)}</tbody></table>
            </>}
            {me?.zone && <div className="mt-4"><div className="text-xs text-ink-3 mb-1">{me.zone} · {cur}/MWh</div><Bars values={hours.map(h => mine.zone_prices[String(h)] || 0)} labels={hours} /></div>}
          </>}
        </section>
      </main>
    </div>
  )
}
