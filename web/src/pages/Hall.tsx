import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, session, type Reference } from '../api'
import { useT, useLang } from '../i18n'
import { Button, Field, ErrorBox, LangToggle } from '../components/ui'

export default function Hall() {
  const t = useT(); const { lang } = useLang(); const nav = useNavigate()
  const [ref, setRef] = useState<Reference | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [roomName, setRoomName] = useState('Formation'); const [trainer, setTrainer] = useState('')
  const [code, setCode] = useState(''); const [name, setName] = useState(''); const [zone, setZone] = useState('SEN'); const [role, setRole] = useState('trader')
  useEffect(() => { api.reference().then(setRef).catch(e => setErr(String(e.message))) }, [])

  const create = async (e: FormEvent) => {
    e.preventDefault(); setErr(null)
    try {
      const r = await api.createRoom(roomName, trainer || 'Formateur', lang)
      session.save(r.code, r.trainer_token, 'trainer'); nav(`/desk/${r.code}`)
    } catch (ex: any) { setErr(ex.message) }
  }
  const join = async (e: FormEvent) => {
    e.preventDefault(); setErr(null)
    try {
      const c = code.trim().toUpperCase()
      const p = await api.join(c, name, role === 'trader' ? zone : null, role)
      session.save(c, p.token, role); nav(`/room/${c}`)
    } catch (ex: any) { setErr(ex.message) }
  }

  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between px-5 h-12 border-b border-line bg-surface"><span className="font-medium">WAPP · Day-Ahead</span><LangToggle /></header>
      <main className="max-w-4xl mx-auto px-5 py-10">
        <h1>{t('app_title')}</h1>
        <p className="text-ink-2 mt-1 mb-8">{t('app_tagline')}</p>
        <ErrorBox message={err} />
        <div className="grid md:grid-cols-2 gap-10">
          <form onSubmit={create} className="flex flex-col gap-3">
            <h2>{t('create_room')}</h2>
            <Field label={t('room_name')}><input value={roomName} onChange={e => setRoomName(e.target.value)} required /></Field>
            <Field label={t('trainer_name')}><input value={trainer} onChange={e => setTrainer(e.target.value)} placeholder="SENELEC" /></Field>
            <div><Button primary type="submit">{t('create')}</Button></div>
          </form>
          <form onSubmit={join} className="flex flex-col gap-3">
            <h2>{t('join_room')}</h2>
            <Field label={t('room_code')}><input value={code} onChange={e => setCode(e.target.value)} placeholder="ABC123" required className="font-mono uppercase" /></Field>
            <Field label={t('your_name')}><input value={name} onChange={e => setName(e.target.value)} placeholder="SENELEC" required /></Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label={t('role')}>
                <select value={role} onChange={e => setRole(e.target.value)}><option value="trader">{t('trader')}</option><option value="observer">{t('observer')}</option></select>
              </Field>
              {role === 'trader' && <Field label={t('zone')}>
                <select value={zone} onChange={e => setZone(e.target.value)}>{(ref?.zones || ['SEN']).map(z => <option key={z}>{z}</option>)}</select>
              </Field>}
            </div>
            <div><Button type="submit">{t('join')}</Button></div>
          </form>
        </div>
      </main>
    </div>
  )
}
