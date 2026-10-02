import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, session, type Reference } from '../api'
import { useT, useLang } from '../i18n'
import { Button, Field, ErrorBox, LangToggle, Panel, Badge } from '../components/ui'

export default function Hall() {
  const t = useT(); const { lang } = useLang(); const nav = useNavigate(); const [params] = useSearchParams()
  const [ref, setRef] = useState<Reference | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [roomName, setRoomName] = useState('Formation'); const [trainer, setTrainer] = useState('')
  const [code, setCode] = useState(params.get('code') || ''); const [name, setName] = useState(''); const [zone, setZone] = useState('SEN'); const [role, setRole] = useState('trader')
  const [rooms, setRooms] = useState(session.rooms())
  useEffect(() => { api.reference().then(setRef).catch(e => setErr(String(e.message))) }, [])

  const create = async (e: FormEvent) => {
    e.preventDefault(); setErr(null)
    try { const r = await api.createRoom(roomName, trainer || 'Formateur', lang); session.save(r.code, r.trainer_token, 'trainer', r.name); nav(`/desk/${r.code}`) }
    catch (ex: any) { setErr(ex.message) }
  }
  const join = async (e: FormEvent) => {
    e.preventDefault(); setErr(null)
    try {
      const c = code.trim().toUpperCase(); const p = await api.join(c, name, role === 'trader' ? zone : null, role)
      const info = await api.room(c).catch(() => null)
      session.save(c, p.token, role, info?.name); session.addMember(c, { id: p.id, name: p.name, zone: p.zone, role: p.role, token: p.token }); nav(`/room/${c}`)
    } catch (ex: any) { setErr(ex.message) }
  }

  return (
    <div className="min-h-screen">
      <header className="bg-brand text-white"><div className="max-w-6xl mx-auto flex items-center justify-between px-6 h-16"><Link to="/" className="flex items-center gap-3"><img src="/mark.svg" alt="" className="h-9 w-9" /><span className="font-semibold text-lg">WAPP DAM Simulator</span></Link><div className="flex items-center gap-5 text-sm"><Link to="/" className="text-brand-ink hover:text-white">{t('about')}</Link><Link to="/guide/formateur" className="text-brand-ink hover:text-white">{t('guide_trainer')}</Link><Link to="/guide/trader" className="text-brand-ink hover:text-white">{t('guide_trader')}</Link><LangToggle dark /></div></div></header>
      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="max-w-3xl mb-10">
          <h1 className="text-3xl">{t('app_title')}</h1>
          <p className="text-ink-2 text-lg mt-3">{t('hero_1')}</p>
        </div>
        <ErrorBox message={err} />
        <div className="grid lg:grid-cols-2 gap-6">
          <Panel title={t('create_room')}>
            <form onSubmit={create} className="flex flex-col gap-4">
              <Field label={t('room_name')}><input value={roomName} onChange={e => setRoomName(e.target.value)} required /></Field>
              <Field label={t('trainer_name')}><input value={trainer} onChange={e => setTrainer(e.target.value)} placeholder="SENELEC" /></Field>
              <div><Button primary type="submit">{t('create')}</Button></div>
            </form>
          </Panel>
          <Panel title={t('join_room')}>
            <form onSubmit={join} className="flex flex-col gap-4">
              <Field label={t('room_code')}><input value={code} onChange={e => setCode(e.target.value)} placeholder="ABC123" required className="font-mono uppercase tracking-widest" /></Field>
              <Field label={t('your_name')} hint={t('name_hint')}><input value={name} onChange={e => setName(e.target.value)} placeholder="SENELEC" required list="orgs" /><datalist id="orgs">{(role === 'trader' ? (ref?.organisations?.[zone] || []) : []).map(o => <option key={o} value={o} />)}</datalist></Field>
              <div className="grid grid-cols-2 gap-4">
                <Field label={t('role')}><select value={role} onChange={e => setRole(e.target.value)}><option value="trader">{t('trader')}</option><option value="observer">{t('observer')}</option></select></Field>
                {role === 'trader' && <Field label={t('zone')}><select value={zone} onChange={e => setZone(e.target.value)}>{(ref?.zones || ['SEN']).map(z => <option key={z}>{z}</option>)}</select></Field>}
              </div>
              <div><Button type="submit">{t('join')}</Button></div>
            </form>
          </Panel>
        </div>
        {rooms.length > 0 && (
          <Panel title={t('my_rooms')} className="mt-6">
            <table><thead><tr><th>{t('room_name')}</th><th>{t('room_code')}</th><th>{t('role')}</th><th /></tr></thead><tbody>
              {rooms.map(r => <tr key={r.code}>
                <td className="font-medium">{r.name}</td><td className="font-mono tracking-wider">{r.code}</td>
                <td className="py-2"><div className="flex flex-wrap gap-2">{r.trainer && <Badge tone="brand">{t('as_trainer')}</Badge>}{session.members(r.code).map(m => <Badge key={m.id} tone="accent">{m.name}{m.zone ? ` · ${m.zone}` : ''}</Badge>)}</div></td>
                <td className="text-right whitespace-nowrap">
                  {r.trainer && <Link className="text-accent font-medium mr-4" to={`/desk/${r.code}`}>{t('as_trainer')} →</Link>}
                  {r.member && <Link className="text-accent font-medium mr-4" to={`/room/${r.code}`}>{t('as_member')} →</Link>}
                  <button className="text-ink-3 text-sm" onClick={() => { session.forget(r.code); setRooms(session.rooms()) }}>{t('forget')}</button>
                </td>
              </tr>)}
            </tbody></table>
          </Panel>
        )}
      </main>
    </div>
  )
}
