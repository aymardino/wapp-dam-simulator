import { useEffect, useRef } from 'react'
import { api } from './api'

export type RoomState = { code: string; phase: string; counts: Record<string, number>; n_participants: number; last_run_id: number | null; last_run_at: string | null; settings: any }

/** Abonnement au flux d'événements de la salle (Server-Sent Events), avec repli sur un sondage toutes les 10 s. */
export function useRoomEvents(code: string, onState: (s: RoomState) => void) {
  const cb = useRef(onState); cb.current = onState
  useEffect(() => {
    if (!code) return
    let es: EventSource | null = null; let timer: any = null; let poll: any = null; let closed = false
    const connect = () => {
      if (closed) return
      es = new EventSource(api.eventsUrl(code))
      es.addEventListener('state', (e: MessageEvent) => { try { cb.current(JSON.parse(e.data)) } catch {} })
      es.onerror = () => { es?.close(); es = null; if (!closed) timer = setTimeout(connect, 5000) }
    }
    if (typeof EventSource !== 'undefined') connect()
    else poll = setInterval(() => api.state(code).then(s => cb.current(s as unknown as RoomState)).catch(() => {}), 10000)
    return () => { closed = true; es?.close(); clearTimeout(timer); clearInterval(poll) }
  }, [code])
}
