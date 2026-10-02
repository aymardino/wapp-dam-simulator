import type { ReactNode } from 'react'
import { useLang, useT } from '../i18n'

export function Button({ children, onClick, primary, disabled, type = 'button' }: { children: ReactNode; onClick?: () => void; primary?: boolean; disabled?: boolean; type?: 'button' | 'submit' }) {
  const base = 'h-8 px-3 rounded text-sm font-medium border transition-colors disabled:opacity-50'
  const look = primary ? 'bg-accent text-white border-accent hover:bg-accent-ink' : 'bg-surface text-ink border-line-strong hover:bg-panel'
  return <button type={type} onClick={onClick} disabled={disabled} className={`${base} ${look}`}>{children}</button>
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return <div className="flex flex-col gap-1"><label>{label}</label>{children}</div>
}

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'up' | 'down' | 'warn' | 'accent' }) {
  const tones: Record<string, string> = { neutral: 'bg-panel text-ink-2', up: 'bg-up-soft text-up', down: 'bg-down-soft text-down', warn: 'bg-warn-soft text-warn', accent: 'bg-accent-soft text-accent-ink' }
  return <span className={`inline-block px-2 py-0.5 rounded text-xs ${tones[tone]}`}>{children}</span>
}

export function Stat({ label, value, sub }: { label: string; value: ReactNode; sub?: ReactNode }) {
  return (
    <div className="bg-panel rounded p-3">
      <div className="text-xs text-ink-2">{label}</div>
      <div className="text-xl font-medium font-mono tabular-nums">{value}</div>
      {sub && <div className="text-xs text-ink-3 mt-0.5">{sub}</div>}
    </div>
  )
}

export function Section({ title, right, children }: { title: string; right?: ReactNode; children: ReactNode }) {
  return (
    <section className="mb-6">
      <div className="flex items-center justify-between mb-2"><h2>{title}</h2>{right}</div>
      {children}
    </section>
  )
}

export function ErrorBox({ message }: { message: string | null }) {
  if (!message) return null
  return <div className="text-sm text-down bg-down-soft rounded px-3 py-2 mb-3">{message}</div>
}

export function LangToggle() {
  const { lang, setLang } = useLang()
  return (
    <div className="text-xs text-ink-2">
      <button className={lang === 'fr' ? 'text-ink font-medium' : ''} onClick={() => setLang('fr')}>FR</button>
      <span className="mx-1">·</span>
      <button className={lang === 'en' ? 'text-ink font-medium' : ''} onClick={() => setLang('en')}>EN</button>
    </div>
  )
}

export function TopBar({ title, meta, phase }: { title: string; meta?: ReactNode; phase?: 'submission' | 'cleared' }) {
  const t = useT()
  return (
    <header className="flex items-center justify-between px-5 h-12 border-b border-line bg-surface">
      <div className="flex items-center gap-4">
        <a href="/" className="text-ink-3 text-xs">{t('back')}</a>
        <span className="font-medium">{title}</span>
        {meta && <span className="text-ink-2 text-sm">{meta}</span>}
      </div>
      <div className="flex items-center gap-4">
        {phase && <Badge tone={phase === 'submission' ? 'up' : 'neutral'}>{phase === 'submission' ? t('phase_submission') : t('phase_cleared')}</Badge>}
        <LangToggle />
      </div>
    </header>
  )
}

/** Mini graphique en barres sans dépendance : prix par heure d'une zone. */
export function Bars({ values, labels, height = 60 }: { values: number[]; labels: (string | number)[]; height?: number }) {
  const max = Math.max(1, ...values)
  return (
    <svg width="100%" viewBox={`0 0 ${values.length * 10} ${height}`} preserveAspectRatio="none" className="block">
      {values.map((v, i) => (
        <rect key={i} x={i * 10 + 1} y={height - (v / max) * height} width={8} height={(v / max) * height} fill="#0F6E56" opacity={0.75}>
          <title>{`${labels[i]} : ${Math.round(v)}`}</title>
        </rect>
      ))}
    </svg>
  )
}
