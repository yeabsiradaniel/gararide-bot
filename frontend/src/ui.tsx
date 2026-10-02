import { useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { S } from './strings'
import { Icon } from './icons'

export function Loader() {
  return <div className="center"><div className="spinner" /><div className="muted tiny">{S.loading}</div></div>
}

export function ErrorView({ msg, onRetry }: { msg?: string; onRetry?: () => void }) {
  return (
    <div className="center">
      <span className="empty-ic"><Icon name="alert" size={34} /></span>
      <div className="muted">{msg || S.errorGeneric}</div>
      {onRetry && <button className="btn btn--ghost" style={{ width: 'auto' }} onClick={onRetry}>{S.retry}</button>}
    </div>
  )
}

export function EmptyState({ icon = 'leaf', text }: { icon?: string; text: string }) {
  return <div className="center"><span className="empty-ic"><Icon name={icon} size={34} /></span><div className="muted">{text}</div></div>
}

export function Screen({ eyebrow, title, children }: { eyebrow?: string; title?: string; children: ReactNode }) {
  return (
    <div className="screen stack-lg">
      {(eyebrow || title) && (
        <div>
          {eyebrow && <div className="eyebrow">{eyebrow}</div>}
          {title && <h1>{title}</h1>}
        </div>
      )}
      {children}
    </div>
  )
}

// Ticking mm:ss until `until` (epoch ms). Fires onDone once when it reaches zero.
export function Countdown({ until, onDone }: { until: number; onDone?: () => void }) {
  const [left, setLeft] = useState(() => Math.max(0, until - Date.now()))
  useEffect(() => {
    const id = setInterval(() => {
      const rem = Math.max(0, until - Date.now())
      setLeft(rem)
      if (rem <= 0) { clearInterval(id); onDone?.() }
    }, 1000)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [until])
  const secs = Math.ceil(left / 1000)
  return <span className="price">{Math.floor(secs / 60)}:{String(secs % 60).padStart(2, '0')}</span>
}

interface AsyncState<T> { data?: T; loading: boolean; error?: string }

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [state, setState] = useState<AsyncState<T>>({ loading: true })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const load = useCallback((silent = false) => {
    if (!silent) setState({ loading: true })
    fn().then((data) => setState({ data, loading: false }))
      .catch((e) => { if (!silent) setState({ loading: false, error: e?.message || S.errorGeneric }) })
  }, deps)
  useEffect(() => { load() }, [load])
  // reload() shows the loader; refresh() updates in place (for background polling).
  const reload = useCallback(() => load(false), [load])
  const refresh = useCallback(() => load(true), [load])
  return { ...state, reload, refresh }
}

// Silently re-fetch on an interval while mounted — keeps a list live without flicker.
export function usePoll(refresh: () => void, ms = 15000) {
  useEffect(() => {
    const id = setInterval(refresh, ms)
    return () => clearInterval(id)
  }, [refresh, ms])
}
