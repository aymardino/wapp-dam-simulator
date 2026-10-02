/** Client de l'API REST (voir api/main.py). Le jeton du participant est conservé par salle dans localStorage. */
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) || '/api/v1'

export type Participant = { id: string; name: string; zone: string | null; role: 'trainer' | 'trader' | 'observer'; joined_at: string }
export type Settings = { hours: number[]; pricing: string; pab_rule: string; tie_rule: string; fill_missing: boolean; currency: string; lang: 'fr' | 'en'; market_date: string; scenario: string }
export type Scenario = { key: string; name: string; description: string }
export type Counts = { supply: number; demand: number; blocks: number; mic: number }
export type RoomInfo = { code: string; name: string; phase: 'submission' | 'cleared'; settings: Settings; ntc: Record<string, number>; participants: Participant[]; counts: Counts; last_run_id: number | null; created_at: string }
export type Supply = { actor: string; segment: number; quantity: number; price: number; profile: string }
export type Demand = { actor: string; segment: number; quantity: number; price: number }
export type Block = { name: string; side: 'S' | 'D'; quantity: number; price: number; h_start: number; h_end: number; parent_name?: string | null; excl_group?: string | null }
export type Mic = { actor: string; fixed_term: number; variable_term: number }
export type OrderBook = { supply: Supply[]; demand: Demand[]; blocks: Block[]; mic: Mic[] }
export type Run = { id: number; run_at: string; welfare: number; volume: number; settings: Settings; result: any }
export type MyResult = { run_id: number; run_at: string; participant: Participant; zone_prices: Record<string, number>; actors: any[]; blocks: any[]; mic: any[]; hours: number[]; currency: string }
export type RefRow = { zone: string; actor: string; segment: number; quantity: number; price: number; profile?: string }
export type Reference = { zones: string[]; lines: { from: string; to: string; ntc: number }[]; profiles: Record<string, number[]>; price_bounds: number[]; rules: Record<string, string[]>; reference_supply: RefRow[]; reference_demand: RefRow[] }

/** Valeurs par défaut d'un nouvel ordre, tirées des tailles types de la zone dans les données de référence. */
export function zoneDefaults(ref: Reference | null, zone: string | null) {
  const med = (xs: number[]) => { if (!xs.length) return null; const s = [...xs].sort((a, b) => a - b); return s[Math.floor(s.length / 2)] }
  const sup = ref && zone ? ref.reference_supply.filter(r => r.zone === zone) : []
  const dem = ref && zone ? ref.reference_demand.filter(r => r.zone === zone) : []
  const q = med(sup.map(r => r.quantity)); const p = med(sup.map(r => r.price))
  const dq = dem.length ? Math.max(...dem.map(r => r.quantity)) : null; const dp = med(dem.map(r => r.price))
  const round = (x: number) => Math.max(5, Math.round(x / 5) * 5)
  return { supplyQty: q ? round(q) : 50, supplyPrice: p ? Math.round(p) : 50, demandQty: dq ? round(dq * 0.6) : 100, demandPrice: dp ? Math.round(dp) : 150, blockQty: q ? round(q / 2) : 25 }
}

/** Un jeton par salle et par rôle : un formateur peut aussi rejoindre sa propre salle comme trader depuis le même navigateur. */
export type Role2 = 'trainer' | 'member'
export const session = {
  token: (code: string, role: Role2) => localStorage.getItem(`wapp:${code}:${role}:token`),
  save: (code: string, token: string, role: string, name?: string) => {
    localStorage.setItem(`wapp:${code}:${role === 'trainer' ? 'trainer' : 'member'}:token`, token)
    if (name) localStorage.setItem(`wapp:${code}:name`, name)
  },
  rooms: (): { code: string; name: string; trainer: boolean; member: boolean }[] => {
    const out: Record<string, { code: string; name: string; trainer: boolean; member: boolean }> = {}
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i) || ''; const m = k.match(/^wapp:([A-Z0-9]{4,8}):(trainer|member):token$/)
      if (!m) continue
      const r = (out[m[1]] ||= { code: m[1], name: localStorage.getItem(`wapp:${m[1]}:name`) || m[1], trainer: false, member: false })
      if (m[2] === 'trainer') r.trainer = true; else r.member = true
    }
    return Object.values(out)
  },
  forget: (code: string) => ['trainer', 'member'].forEach(r => localStorage.removeItem(`wapp:${code}:${r}:token`)),
}

async function call<T>(path: string, init: RequestInit = {}, token?: string | null): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json', ...(init.headers as Record<string, string> || {}) }
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(BASE + path, { ...init, headers })
  if (res.status === 204) return undefined as T
  const body = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail || res.statusText))
  return body as T
}

export const api = {
  reference: () => call<Reference>('/reference'),
  scenarios: (lang: string) => call<Scenario[]>(`/scenarios?lang=${lang}`),
  eventsUrl: (code: string) => `${BASE}/rooms/${code}/events`,
  csvUrl: (code: string, runId: number) => `${BASE}/rooms/${code}/results/${runId}/prices.csv`,
  jsonUrl: (code: string, runId: number) => `${BASE}/rooms/${code}/results/${runId}`,
  createRoom: (name: string, trainer_name: string, lang: string) => call<RoomInfo & { trainer_token: string }>('/rooms', { method: 'POST', body: JSON.stringify({ name, trainer_name, lang }) }),
  room: (code: string) => call<RoomInfo>(`/rooms/${code}`),
  state: (code: string) => call<{ phase: string; counts: Counts; n_participants: number; last_run_id: number | null }>(`/rooms/${code}/state`),
  join: (code: string, name: string, zone: string | null, role: string) => call<Participant & { token: string }>(`/rooms/${code}/join`, { method: 'POST', body: JSON.stringify({ name, zone, role }) }),
  me: (code: string, token: string) => call<Participant>(`/rooms/${code}/me`, {}, token),
  myOrders: (code: string, token: string) => call<OrderBook & { participant: Participant }>(`/rooms/${code}/orders/me`, {}, token),
  putOrders: (code: string, token: string, book: OrderBook) => call<OrderBook>(`/rooms/${code}/orders/me`, { method: 'PUT', body: JSON.stringify(book) }, token),
  allOrders: (code: string, token: string) => call<(OrderBook & { participant: Participant })[]>(`/rooms/${code}/orders`, {}, token),
  settings: (code: string, token: string, patch: Partial<Settings>) => call<Settings>(`/rooms/${code}/settings`, { method: 'PUT', body: JSON.stringify(patch) }, token),
  phase: (code: string, token: string, phase: string) => call<RoomInfo>(`/rooms/${code}/phase`, { method: 'PUT', body: JSON.stringify({ phase }) }, token),
  ntc: (code: string, token: string, values: Record<string, number>) => call<Record<string, number>>(`/rooms/${code}/ntc`, { method: 'PUT', body: JSON.stringify({ values }) }, token),
  resetNtc: (code: string, token: string) => call<Record<string, number>>(`/rooms/${code}/ntc`, { method: 'DELETE' }, token),
  clear: (code: string, token: string) => call<Run>(`/rooms/${code}/clearing`, { method: 'POST' }, token),
  latest: (code: string) => call<Run>(`/rooms/${code}/results/latest`),
  myResult: (code: string, token: string) => call<MyResult>(`/rooms/${code}/results/latest/me`, {}, token),
}

export const fmt = {
  n: (x: number | null | undefined, d = 0) => (x == null ? '—' : x.toLocaleString('fr-FR', { maximumFractionDigits: d, minimumFractionDigits: d })),
  money: (x: number | null | undefined, cur: string) => (x == null ? '—' : `${fmt.n(x)} ${cur}`),
}
