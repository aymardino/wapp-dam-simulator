import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, fmt, session, type OrderBook, type Participant, type Reference, type RoomInfo, type Run, type Scenario, type Settings } from '../api'
import { useLang } from '../i18n'
import { PriceChart, DispatchChart, FlowChart } from '../components/Charts'
import { useRoomEvents } from '../hooks'
import { useT } from '../i18n'
import { Badge, Button, Empty, ErrorBox, Field, Header, Kpi, Panel, Tabs } from '../components/ui'
import NetworkMap from '../components/NetworkMap'

const CORRIDORS = ['NGA->BEN', 'NGA->NER', 'GHA->CIV', 'GHA->BFA', 'CIV->BFA', 'CIV->MLI', 'CIV->LBR', 'SEN->MLI']

export default function Desk() {
  const { code = '' } = useParams(); const t = useT(); const { lang } = useLang()
  const token = session.token(code, 'trainer'); const memberToken = session.token(code, 'member')
  const [room, setRoom] = useState<RoomInfo | null>(null)
  const [ref, setRef] = useState<Reference | null>(null)
  const [orders, setOrders] = useState<(OrderBook & { participant: Participant })[]>([])
  const [run, setRun] = useState<Run | null>(null)
  const [s, setS] = useState<Settings | null>(null)
  const [ntc, setNtc] = useState<Record<string, number>>({})
  const [hour, setHour] = useState(19)
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [view, setView] = useState<'map' | 'prices' | 'dispatch' | 'flows'>('map')
  const [live, setLive] = useState(false)
  const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null); const [savedAt, setSavedAt] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!token) return
    try {
      const r = await api.room(code); setRoom(r); setS(prev => prev ?? r.settings); setNtc(prev => (Object.keys(prev).length ? prev : r.ntc))
      setOrders(await api.allOrders(code, token))
      if (r.last_run_id) { const lr = await api.latest(code); setRun(lr); const hs: number[] = lr.result.summary.hours; setHour(h => (hs.includes(h) ? h : hs[0])) }
    } catch (ex: any) { setErr(ex.message) }
  }, [code, token])
  useEffect(() => { api.reference().then(setRef); load() }, [load])
  useEffect(() => { api.scenarios(lang).then(setScenarios).catch(() => {}) }, [lang])
  useRoomEvents(code, () => { setLive(true); load() })

  if (!token) return <div className="p-10 text-lg">{t('desk')} : <a className="text-accent font-medium" href="/app">{t('back')}</a></div>
  const cur = s?.currency || 'USD'; const unit = `${cur}/MWh`

  const patchSettings = async (patch: Partial<Settings>) => {
    setS(prev => (prev ? { ...prev, ...patch } : prev)); setErr(null)
    try { setS(await api.settings(code, token, patch)); setSavedAt(new Date().toLocaleTimeString()) } catch (ex: any) { setErr(ex.message) }
  }
  const saveNtc = async () => { setErr(null); try { setNtc(await api.ntc(code, token, ntc)) } catch (ex: any) { setErr(ex.message) } }
  const resetNtc = async () => { setErr(null); try { setNtc(await api.resetNtc(code, token)) } catch (ex: any) { setErr(ex.message) } }
  const togglePhase = async () => { if (!room) return; try { setRoom(await api.phase(code, token, room.phase === 'submission' ? 'cleared' : 'submission')) } catch (ex: any) { setErr(ex.message) } }
  const clear = async () => { setBusy(true); setErr(null); try { setRun(await api.clear(code, token)); await load() } catch (ex: any) { setErr(ex.message) } finally { setBusy(false) } }

  const d = run?.result?.summary?.diagnostics
  const zonesInfo = run?.result?.summary?.zones as Record<string, any> | undefined
  const traders = room?.participants.filter(p => p.role === 'trader') || []
  const coveredZones = new Set(orders.filter(o => o.supply.length + o.demand.length + o.blocks.length > 0).map(o => o.participant.zone))
  const nZones = ref?.zones.length || 14
  const refZones: string[] = run?.result?.summary?.reference_zones || []

  return (
    <div className="min-h-screen">
      <Header title={`${t('desk')} · ${room?.name || code}`} code={code} phase={room?.phase} meta={`${t('invite')} · ${t('delivery')} ${room?.settings.market_date || ''}`}
        switchTo={{ label: memberToken ? t('switch_room') : t('switch_room'), to: memberToken ? `/room/${code}` : `/?code=${code}` }} />
      <main className="p-5 max-w-[1500px] mx-auto">
        <ErrorBox message={err} />
        <div className="grid md:grid-cols-4 gap-3 mb-5">
          <Kpi label={t('participants')} value={traders.length} sub={t('trader_count')} />
          <Kpi label={t('orders')} value={room ? room.counts.supply + room.counts.demand + room.counts.blocks : 0} sub={room ? `${room.counts.blocks} ${t('blocks').toLowerCase()} · ${room.counts.mic} MIC` : ''} />
          <Kpi label={t('welfare')} value={run ? fmt.money(run.welfare / 1e6, 'M ' + cur) : '—'} />
          <Kpi label={t('volume')} value={run ? `${fmt.n(run.volume / 1000, 1)} GWh` : '—'} />
        </div>

        <div className="grid gap-5 xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          <div className="flex flex-col gap-5">
            <Panel title={t('run_clearing')}>
              <p className="text-ink-2 mb-3">{t('run_hint')}</p>
              {s && <div className="mb-3 max-w-md"><Field label={t('fill_mode')} hint={t(`fill_${s.fill_mode || 'actors'}_hint`)}>
                <select value={s.fill_mode || 'actors'} onChange={e => patchSettings({ fill_mode: e.target.value as any })}>
                  <option value="actors">{t('fill_actors')}</option><option value="zones">{t('fill_zones')}</option><option value="none">{t('fill_none')}</option>
                </select></Field></div>}
              <p className="mb-4"><span className="font-mono font-medium">{coveredZones.size}</span> {t('with_orders')} · <span className="font-mono font-medium">{nZones - coveredZones.size}</span> {t('without_orders')}</p>
              <div className="flex items-center gap-3">
                <Button primary onClick={clear} disabled={busy}>{busy ? t('running') : t('run_clearing')}</Button>
                <Button onClick={togglePhase}>{room?.phase === 'submission' ? t('close_market') : t('open_market')}</Button>
              </div>
            </Panel>

            <Panel title={t('participants')}>
              {traders.length === 0 ? <Empty>{t('no_orders')}</Empty> :
                <table><thead><tr><th>{t('your_name')}</th><th>{t('zone')}</th><th className="text-right">{t('orders')}</th></tr></thead><tbody>
                  {traders.map(p => { const ob = orders.find(o => o.participant.id === p.id); const n = ob ? ob.supply.length + ob.demand.length + ob.blocks.length : 0; return <tr key={p.id}>
                    <td className="font-medium">{p.name}</td><td>{p.zone && <Badge tone="accent">{p.zone}</Badge>}</td><td className="num">{n}</td>
                  </tr> })}
                </tbody></table>}
            </Panel>

            {s && <Panel title={t('settings')} right={<span className="text-sm text-ink-3">{savedAt ? `${t('saved_at')} ${savedAt}` : t('autosave')}</span>}>
              <div className="grid grid-cols-2 gap-4">
                <Field label={t('horizon')}>
                  <select value={s.hours.length === 24 ? '24' : 'one'} onChange={e => patchSettings({ hours: e.target.value === '24' ? Array.from({ length: 24 }, (_, i) => i) : [19] })}>
                    <option value="24">{t('hours24')}</option><option value="one">{t('one_hour')}</option>
                  </select>
                </Field>
                {s.hours.length !== 24 ? <Field label={t('hour')}><input type="number" min={0} max={23} value={s.hours[0]} onChange={e => patchSettings({ hours: [+e.target.value] })} /></Field> : <Field label={t('currency')}><input value={s.currency} onChange={e => setS({ ...s, currency: e.target.value })} onBlur={e => patchSettings({ currency: e.target.value })} /></Field>}
                <Field label={t('pricing')}><select value={s.pricing} onChange={e => patchSettings({ pricing: e.target.value })}>{(ref?.rules.pricing || ['complete', 'l2']).map(x => <option key={x}>{x}</option>)}</select></Field>
                <Field label={t('pab')}><select value={s.pab_rule} onChange={e => patchSettings({ pab_rule: e.target.value })}>{(ref?.rules.pab_rule || ['euphemia']).map(x => <option key={x}>{x}</option>)}</select></Field>
                <Field label={t('tie')}><select value={s.tie_rule} onChange={e => patchSettings({ tie_rule: e.target.value })}>{(ref?.rules.tie_rule || ['prorata']).map(x => <option key={x}>{x}</option>)}</select></Field>
                <div className="col-span-2"><Field label={t('scenario')} hint={scenarios.find(x => x.key === s.scenario)?.description}>
                  <select value={s.scenario} onChange={e => patchSettings({ scenario: e.target.value })}>{scenarios.map(x => <option key={x.key} value={x.key}>{x.name}</option>)}</select>
                </Field></div>
              </div>
            </Panel>}

            <Panel title={t('ntc')} right={<><Button small onClick={resetNtc}>{t('reset')}</Button><Button small onClick={saveNtc}>{t('save')}</Button></>}>
              <div className="grid grid-cols-2 gap-x-6">
                {(ref?.lines || []).map(l => { const k = `${l.from}->${l.to}`; return <div key={k} className="flex items-center justify-between gap-2 py-1 border-b border-line">
                  <span className="font-mono text-sm">{k}</span><span className="text-xs text-ink-3 ml-auto">{room?.ntc_default?.[k] ?? l.ntc}</span>
                  <input type="number" min={0} step={10} value={ntc[k] ?? room?.ntc_default?.[k] ?? l.ntc} onChange={e => setNtc({ ...ntc, [k]: +e.target.value })} className="w-24 h-8" />
                </div> })}
              </div>
            </Panel>
          </div>

          <div className="flex flex-col gap-5">
            <Panel title={t('results')} right={<>{live && <Badge tone="up">{t('live')}</Badge>}{run && <><a className="text-sm text-accent font-medium" href={api.csvUrl(code, run.id)}>{t('export_csv')}</a><a className="text-sm text-accent font-medium" href={api.jsonUrl(code, run.id)} target="_blank" rel="noreferrer">{t('export_json')}</a><span className="text-sm text-ink-3">#{run.id} · {new Date(run.run_at).toLocaleTimeString()}</span></>}</>}>
              {!run || !d ? <Empty>{t('no_clearing')}</Empty> : <>
                {refZones.length === nZones && <div className="mb-3 rounded bg-warn-soft text-warn px-4 py-2.5">{t('demo_badge')}</div>}
                <div className="flex flex-wrap gap-2 mb-4">
                  {refZones.length > 0 && refZones.length < nZones && <Badge tone="warn">{t('reference_badge')} · {refZones.length} {t('zones_word')}</Badge>}
                  <Badge tone={d.pro === 0 ? 'up' : 'down'}>{d.pro} {t('check_pro')}</Badge>
                  <Badge tone={d.unsaturated_price_gaps === 0 ? 'up' : 'down'}>{d.unsaturated_price_gaps} {t('check_gaps')}</Badge>
                  <Badge tone={d.tie_break === 'exact' ? 'up' : 'warn'}>{t('check_tie')} {d.tie_break} · {d.tie_rule}</Badge>
                  {d.prb?.length > 0 && <Badge tone="warn">PRB · {d.prb.join(', ')}</Badge>}
                  {d.mic_withdrawn?.length > 0 && <Badge tone="warn">MIC · {d.mic_withdrawn.join(', ')}</Badge>}
                </div>
                <Tabs tabs={[{ key: 'map', label: t('tab_map') }, { key: 'prices', label: t('tab_prices') }, { key: 'dispatch', label: t('tab_dispatch') }, { key: 'flows', label: t('tab_flows') }]} active={view} onChange={setView} />
                {view === 'map' && <div className="flex items-center justify-between mb-2"><h3>{t('network')} · {t('prices_at')} {`H${String(hour).padStart(2, '0')}`}</h3>
                  <select value={hour} onChange={e => setHour(+e.target.value)} className="h-8 font-mono">{(run.result.summary.hours as number[]).map(h => <option key={h} value={h}>{`H${String(h).padStart(2, '0')}`}</option>)}</select></div>}
                <div className="rounded-lg bg-panel p-2 mb-4">
                  {view === 'map' && <NetworkMap prices={run.result.prices} flows={run.result.flows} ntc={room?.ntc || {}} hour={hour} unit={unit} />}
                  {view === 'prices' && <PriceChart prices={run.result.prices} hours={run.result.summary.hours} unit={unit} />}
                  {view === 'dispatch' && <DispatchChart dispatch={run.result.dispatch} hours={run.result.summary.hours} label={k => t('p_' + k)} />}
                  {view === 'flows' && <FlowChart flows={run.result.flows} hours={run.result.summary.hours} ntc={room?.ntc || {}} corridors={CORRIDORS} />}
                </div>
                {zonesInfo && <table><thead><tr><th>{t('zone')}</th><th className="text-right">{t('avg24')} ({unit})</th><th className="text-right">{t('position')} (MWh)</th><th className="text-right">{t('surplus')} ({cur})</th></tr></thead><tbody>
                  {Object.entries(zonesInfo).map(([z, zi]: [string, any]) => <tr key={z}>
                    <td className="font-semibold">{z}</td><td className="num">{fmt.n(zi.avg_price, 1)}</td>
                    <td className={`num ${zi.net_position >= 0 ? 'text-up' : 'text-down'}`}>{zi.net_position >= 0 ? '+' : ''}{fmt.n(zi.net_position)}</td>
                    <td className="num">{fmt.n(zi.consumer_surplus + zi.producer_surplus)}</td>
                  </tr>)}
                </tbody></table>}
              </>}
            </Panel>
          </div>
        </div>
      </main>
    </div>
  )
}
