import { useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { S } from './strings'

export function Loader() {
  return <div className="center"><div className="spinner" /><div className="muted tiny">{S.loading}</div></div>
}

export function ErrorView({ msg, onRetry }: { msg?: string; onRetry?: () => void }) {
  return (
    <div className="center">
      <div style={{ fontSize: 30 }}>😕</div>
      <div className="muted">{msg || 'ስህተት ተፈጥሯል'}</div>
      {onRetry && <button className="btn btn--ghost" style={{ width: 'auto' }} onClick={onRetry}>{S.retry}</button>}
    </div>
  )
}

export function EmptyState({ icon = '🌱', text }: { icon?: string; text: string }) {
  return <div className="center"><div style={{ fontSize: 30 }}>{icon}</div><div className="muted">{text}</div></div>
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

interface AsyncState<T> { data?: T; loading: boolean; error?: string }

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [state, setState] = useState<AsyncState<T>>({ loading: true })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const load = useCallback(() => {
    setState({ loading: true })
    fn().then((data) => setState({ data, loading: false }))
      .catch((e) => setState({ loading: false, error: e?.message || 'ስህተት' }))
  }, deps)
  useEffect(() => { load() }, [load])
  return { ...state, reload: load }
}
