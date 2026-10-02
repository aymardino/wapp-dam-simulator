import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, fmt, session, type OrderBook, type Participant, type Reference, type RoomInfo, type Run, type Settings } from '../api'
import { useT } from '../i18n'
import { Badge, Button, ErrorBox, Field, Section, Stat, TopBar } from '../components/ui'

export default function Desk() {
  const { code = '' } = useParams(); const t = useT()
  const token = session.token(code)
  const [room, setRoom] = useState<RoomInfo | null>(null)
  const [ref, setRef] = useState<Reference | null>(null)
  const [orders, setOrders] = useState<(OrderBook & { participant: Participant })[]>([])
  const [run, setRun] = useState<Run | null>(null)
  const [s, setS] = useState<Settings | null>(null)
  const [ntc, setNtc] = useState<Record<string, number>>({})
  const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!token) return
    try {
      const r = await api.room(code); setRoom(r); setS(r.settings); setNtc(r.ntc)
      setOrders(await api.allOrders(code, token))
      if (r.last_run_id) setRun(await api.latest(code))
    } catch (ex: any) { setErr(ex.message) }
  }, [code, token])
  useEffect(() => { api.reference().then(setRef); load(); const id = setInterval(load, 10000); return () => clearInterval(id) }, [load])

  if (!token || session.role(code) !== 'trainer') return <div className="p-8">{t('desk')} : <a className="text-accent" href="/">/</a></div>
  const cur = s?.currency || 'USD'

  const saveSettings = async () => { if (!s) return; setErr(null); try { setS(await api.settings(code, token, s)) } catch (ex: any) { setErr(ex.message) } }
  const saveNtc = async () => { setErr(null); try { setNtc(await api.ntc(code, token, ntc)) } catch (ex: any) { setErr(ex.message) } }
  const resetNtc = async () => { setErr(null); try { setNtc(await api.resetNtc(code, token)) } catch (ex: any) { setErr(ex.message) } }
  const togglePhase = async () => { if (!room) return; try { setRoom(await api.phase(code, token, room.phase === 'submission' ? 'cleared' : 'submission')) } catch (ex: any) { setErr(ex.message) } }
  const clear = async () => { setBusy(true); setErr(null); try { setRun(await api.clear(code, token)); await load() } catch (ex: any) { setErr(ex.message) } finally { setBusy(false) } }

  const d = run?.result?.summary?.diagnostics
  const zonesInfo = run?.result?.summary?.zones as Record<string, any> | undefined

  return (
    <div className="min-h-screen">
      <TopBar title={`${t('desk')} · ${room?.name || code}`} meta={<span>{t('copy_code')} : <span className="font-mono font-medium text-ink">{code}</span></span>} phase={room?.phase} />
      <main className="max-w-6xl mx-auto px-5 py-6">
        <ErrorBox message={err} />
        <div className="grid grid-cols-4 gap-3 mb-6">
          <Stat label={t('participants')} value={room?.participants.filter(p => p.role === 'trader').length ?? 0} sub={t('trader_count')} />
          <Stat label={t('orders')} value={room ? room.counts.supply + room.counts.demand + room.counts.blocks : 0} sub={room ? `${room.counts.blocks} ${t('blocks').toLowerCase()} · ${room.counts.mic} MIC` : ''} />
          <Stat label={t('welfare')} value={run ? fmt.money(run.welfare / 1e6, 'M ' + cur) : '—'} />
          <Stat label={t('volume')} value={run ? `${fmt.n(run.volume / 1000, 1)} GWh` : '—'} />
        </div>

        <div className="flex items-center gap-3 mb-8">
          <Button primary onClick={clear} disabled={busy}>{busy ? t('running') : t('run_clearing')}</Button>
          <Button onClick={togglePhase}>{room?.phase === 'submission' ? t('close_market') : t('open_market')}</Button>
        </div>

        <div className="grid lg:grid-cols-2 gap-10">
          <div>
            {s && <Section title={t('settings')} right={<Button onClick={saveSettings}>{t('save')}</Button>}>
              <div className="grid grid-cols-2 gap-3">
                <Field label={t('horizon')}>
                  <select value={s.hours.length === 24 ? '24' : 'one'} onChange={e => setS({ ...s, hours: e.target.value === '24' ? Array.from({ length: 24 }, (_, i) => i) : [19] })}>
                    <option value="24">{t('hours24')}</option><option value="one">{t('one_hour')}</option>
                  </select>
                </Field>
                {s.hours.length !== 24 && <Field label={t('hour')}><input type="number" min={0} max={23} value={s.hours[0]} onChange={e => setS({ ...s, hours: [+e.target.value] })} /></Field>}
                <Field label={t('pricing')}><select value={s.pricing} onChange={e => setS({ ...s, pricing: e.target.value })}>{(ref?.rules.pricing || ['complete', 'l2']).map(x => <option key={x}>{x}</option>)}</select></Field>
                <Field label={t('pab')}><select value={s.pab_rule} onChange={e => setS({ ...s, pab_rule: e.target.value })}>{(ref?.rules.pab_rule || ['euphemia']).map(x => <option key={x}>{x}</option>)}</select></Field>
                <Field label={t('tie')}><select value={s.tie_rule} onChange={e => setS({ ...s, tie_rule: e.target.value })}>{(ref?.rules.tie_rule || ['prorata']).map(x => <option key={x}>{x}</option>)}</select></Field>
                <Field label={t('currency')}><input value={s.currency} onChange={e => setS({ ...s, currency: e.target.value })} className="w-24" /></Field>
                <label className="flex items-center gap-2 col-span-2 text-sm text-ink"><input type="checkbox" className="h-4 w-4" checked={s.fill_missing} onChange={e => setS({ ...s, fill_missing: e.target.checked })} />{t('fill_missing')}</label>
              </div>
            </Section>}

            <Section title={t('ntc')} right={<div className="flex gap-2"><Button onClick={resetNtc}>{t('reset')}</Button><Button onClick={saveNtc}>{t('save')}</Button></div>}>
              <table><thead><tr><th>{t('line')}</th><th className="text-right">{t('default')}</th><th className="text-right">{t('current')}</th></tr></thead><tbody>
                {(ref?.lines || []).map(l => { const k = `${l.from}->${l.to}`; return <tr key={k}>
                  <td className="font-mono">{k}</td><td className="num text-ink-3">{l.ntc}</td>
                  <td className="text-right"><input type="number" min={0} step={10} value={ntc[k] ?? l.ntc} onChange={e => setNtc({ ...ntc, [k]: +e.target.value })} className="w-24" /></td>
                </tr> })}
              </tbody></table>
            </Section>
          </div>

          <div>
            <Section title={t('participants')}>
              <table><thead><tr><th>{t('your_name')}</th><th>{t('zone')}</th><th>{t('role')}</th><th className="text-right">{t('orders')}</th></tr></thead><tbody>
                {room?.participants.map(p => { const ob = orders.find(o => o.participant.id === p.id); const n = ob ? ob.supply.length + ob.demand.length + ob.blocks.length : 0; return <tr key={p.id}>
                  <td>{p.name}</td><td>{p.zone && <Badge tone="accent">{p.zone}</Badge>}</td><td className="text-ink-2">{p.role}</td><td className="num">{p.role === 'trader' ? n : ''}</td>
                </tr> })}
              </tbody></table>
              {orders.length === 0 && <p className="text-ink-2 text-sm mt-2">{t('no_orders')}</p>}
            </Section>

            {run && d && <Section title={t('checks')}>
              <ul className="text-sm space-y-1">
                <li><Badge tone={d.pro === 0 ? 'up' : 'down'}>{d.pro}</Badge> {t('check_pro')}</li>
                <li><Badge tone={d.unsaturated_price_gaps === 0 ? 'up' : 'down'}>{d.unsaturated_price_gaps}</Badge> {t('check_gaps')}</li>
                <li><Badge tone={d.tie_break === 'exact' ? 'up' : 'warn'}>{d.tie_break}</Badge> {t('check_tie')} · {d.tie_rule}</li>
                {d.prb?.length > 0 && <li><Badge tone="warn">PRB</Badge> {d.prb.join(', ')}</li>}
                {d.mic_withdrawn?.length > 0 && <li><Badge tone="warn">MIC</Badge> {d.mic_withdrawn.join(', ')}</li>}
              </ul>
            </Section>}

            {zonesInfo && <Section title={t('zone_prices')}>
              <table><thead><tr><th>{t('zone')}</th><th className="text-right">{t('avg24')} ({cur}/MWh)</th><th className="text-right">{t('position')} (MWh)</th></tr></thead><tbody>
                {Object.entries(zonesInfo).map(([z, zi]: [string, any]) => <tr key={z}>
                  <td className="font-medium">{z}</td><td className="num">{fmt.n(zi.avg_price, 1)}</td>
                  <td className={`num ${zi.net_position >= 0 ? 'text-up' : 'text-down'}`}>{zi.net_position >= 0 ? '+' : ''}{fmt.n(zi.net_position)}</td>
                </tr>)}
              </tbody></table>
            </Section>}
          </div>
        </div>
      </main>
    </div>
  )
}
