import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useLang, useT } from '../i18n'

export function Button({ children, onClick, primary, disabled, type = 'button', small }: { children: ReactNode; onClick?: () => void; primary?: boolean; disabled?: boolean; type?: 'button' | 'submit'; small?: boolean }) {
  const size = small ? 'h-8 px-3 text-sm' : 'h-10 px-4 text-base'
  const look = primary ? 'bg-accent text-white border-accent hover:bg-accent-hover' : 'bg-surface text-ink border-line-strong hover:bg-panel'
  return <button type={type} onClick={onClick} disabled={disabled} className={`${size} ${look} rounded font-medium border transition-colors disabled:opacity-50`}>{children}</button>
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return <div className="flex flex-col gap-1.5"><label>{label}</label>{children}{hint && <span className="text-xs text-ink-3">{hint}</span>}</div>
}

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'up' | 'down' | 'warn' | 'accent' | 'brand' }) {
  const tones: Record<string, string> = { neutral: 'bg-panel text-ink-2 border border-line', up: 'bg-up-soft text-up', down: 'bg-down-soft text-down', warn: 'bg-warn-soft text-warn', accent: 'bg-accent-soft text-accent-ink', brand: 'bg-brand-2 text-brand-ink' }
  return <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium ${tones[tone]}`}>{children}</span>
}

export function Kpi({ label, value, sub, tone }: { label: string; value: ReactNode; sub?: ReactNode; tone?: 'up' | 'down' }) {
  const color = tone === 'up' ? 'text-up' : tone === 'down' ? 'text-down' : 'text-ink'
  return (
    <div className="bg-panel rounded-lg px-4 py-3 min-w-0">
      <div className="text-xs uppercase tracking-wide text-ink-3 mb-1">{label}</div>
      <div className={`kpi-value ${color}`}>{value}</div>
      {sub && <div className="text-sm text-ink-2 mt-0.5">{sub}</div>}
    </div>
  )
}

export function Panel({ title, right, children, className = '' }: { title?: ReactNode; right?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`bg-surface border border-line rounded-lg shadow-panel ${className}`}>
      {(title || right) && <div className="flex items-center justify-between px-5 h-14 border-b border-line"><h2 className="truncate">{title}</h2><div className="flex items-center gap-2">{right}</div></div>}
      <div className="p-5">{children}</div>
    </section>
  )
}

export function Tabs<T extends string>({ tabs, active, onChange }: { tabs: { key: T; label: string; count?: number }[]; active: T; onChange: (k: T) => void }) {
  return (
    <div className="flex gap-1 border-b border-line mb-4">
      {tabs.map(tb => (
        <button key={tb.key} onClick={() => onChange(tb.key)}
          className={`px-3 pb-2.5 pt-1 text-base border-b-2 -mb-px transition-colors ${active === tb.key ? 'border-accent text-ink font-medium' : 'border-transparent text-ink-2 hover:text-ink'}`}>
          {tb.label}{tb.count != null && <span className="ml-1.5 text-xs text-ink-3 font-mono">{tb.count}</span>}
        </button>
      ))}
    </div>
  )
}

export function Empty({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return <div className="rounded-lg border border-dashed border-line-strong px-5 py-8 text-center text-ink-2">{children}{action && <div className="mt-3">{action}</div>}</div>
}

export function ErrorBox({ message }: { message: string | null }) {
  if (!message) return null
  return <div className="text-base text-down bg-down-soft rounded px-4 py-2.5 mb-4">{message}</div>
}

export function LangToggle({ dark }: { dark?: boolean }) {
  const { lang, setLang } = useLang()
  const on = dark ? 'text-white font-semibold' : 'text-ink font-semibold'; const off = dark ? 'text-brand-ink/70 hover:text-white' : 'text-ink-3 hover:text-ink'
  return (
    <div className="text-sm flex items-center gap-1">
      <button className={lang === 'fr' ? on : off} onClick={() => setLang('fr')}>FR</button>
      <span className={dark ? 'text-brand-ink/40' : 'text-ink-3'}>·</span>
      <button className={lang === 'en' ? on : off} onClick={() => setLang('en')}>EN</button>
    </div>
  )
}

export function Header({ title, code, meta, phase, switchTo }: { title: string; code?: string; meta?: ReactNode; phase?: 'submission' | 'cleared'; switchTo?: { label: string; to: string } }) {
  const t = useT()
  return (
    <header className="bg-brand text-white">
      <div className="flex items-center justify-between px-6 h-16">
        <div className="flex items-center gap-4 min-w-0">
          <Link to="/" className="flex items-center gap-3 shrink-0"><img src="/wapp_logo.png" alt="" className="h-9 w-9 rounded-full bg-white/90 p-0.5" /><span className="hidden md:inline text-brand-ink text-sm">WAPP · Day-Ahead</span></Link>
          <span className="text-brand-ink/40">|</span>
          <div className="min-w-0">
            <div className="font-semibold text-lg truncate">{title}{code && <span className="ml-3 font-mono text-base text-brand-ink/90 tracking-wider">{code}</span>}</div>
            {meta && <div className="text-sm text-brand-ink/80 truncate">{meta}</div>}
          </div>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          {switchTo && <Link to={switchTo.to} className="text-sm text-brand-ink hover:text-white underline underline-offset-4">{switchTo.label}</Link>}
          {phase && <Badge tone={phase === 'submission' ? 'up' : 'neutral'}>{phase === 'submission' ? t('phase_submission') : t('phase_cleared')}</Badge>}
          <LangToggle dark />
        </div>
      </div>
    </header>
  )
}

/** Mini graphique en barres sans dépendance. */
export function Bars({ values, labels, height = 48 }: { values: number[]; labels: (string | number)[]; height?: number }) {
  const max = Math.max(1, ...values)
  return (
    <svg width="100%" viewBox={`0 0 ${values.length * 10} ${height}`} preserveAspectRatio="none" className="block">
      {values.map((v, i) => (
        <rect key={i} x={i * 10 + 1.5} y={height - (v / max) * height} width={7} height={(v / max) * height} rx={1} fill="#0F6E56" opacity={0.8}>
          <title>{`${labels[i]} : ${Math.round(v)}`}</title>
        </rect>
      ))}
    </svg>
  )
}
