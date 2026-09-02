import { useState } from 'react'
import { api } from '../api'
import type { RosterDriver } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { ErrorView, Loader, Screen, useAsync } from '../ui'
import { confirmDialog, haptic, notify } from '../telegram'

export default function Admin() {
  const nav = useNav()
  const ops = useAsync(() => api.ops(), [])
  const unmatched = useAsync(() => api.unmatched(), [])
  const drivers = useAsync(() => api.drivers(), [])
  const [busy, setBusy] = useState<string>()  // phone being removed
  if (ops.loading) return <Loader />
  if (ops.error) return <ErrorView msg={ops.error} onRetry={ops.reload} />
  const o = ops.data!

  const stats: [string, number][] = [
    ['Trips today', o.trips], ['Seats filled', o.seats], ['No-shows', o.no_shows],
    ['Open requests', o.open_requests], ['Registered', o.users],
  ]

  async function remove(d: RosterDriver) {
    if (!(await confirmDialog(S.removeDriverConfirm(d.full_name)))) return
    setBusy(d.phone)
    try {
      await api.removeDriver(d.phone)
      notify('success'); drivers.reload(); ops.reload()
    } catch {
      notify('error')
    } finally { setBusy(undefined) }
  }

  return (
    <Screen eyebrow={S.appName} title="Ops">
      <div className="stack">
        {stats.map(([label, n]) => (
          <div key={label} className="spread card" style={{ padding: '12px 16px' }}>
            <span className="muted">{label}</span>
            <span className="price" style={{ fontSize: 20 }}>{n}</span>
          </div>
        ))}
      </div>

      <button className="tile tile--primary" onClick={() => { haptic(); nav.go({ name: 'addDriver' }) }}>
        <span className="tile__icon">➕</span>
        <span className="tile__body">
          <div className="tile__title">{S.addDriver}</div>
          <div className="tile__sub">{S.addDriverSub}</div>
        </span>
      </button>

      <div className="eyebrow">{S.driverRoster}</div>
      {drivers.loading && <div className="muted tiny">{S.loading}</div>}
      {drivers.data?.length
        ? (
          <div className="stack">
            {drivers.data.map((d) => (
              <div key={d.phone} className="spread card" style={{ padding: '12px 16px' }}>
                <div className="stack" style={{ gap: 2, minWidth: 0 }}>
                  <span><b>{d.full_name}</b>{d.is_female ? ' ♀' : ''}</span>
                  <span className="muted tiny">
                    {d.tower} · {d.car_model || '—'}{d.car_seats ? ` · ${d.car_seats} ${S.seatsWord}` : ''}
                  </span>
                </div>
                <div className="row" style={{ gap: 8, flexShrink: 0 }}>
                  <span className="pill" style={d.onboarded
                    ? { background: 'var(--primary)', color: '#fff', border: 'none' }
                    : undefined}>{d.onboarded ? S.onboarded : S.pending}</span>
                  <button className="icon-btn" aria-label="remove" disabled={busy === d.phone}
                          onClick={() => remove(d)}>🗑</button>
                </div>
              </div>
            ))}
          </div>
        )
        : (!drivers.loading && <div className="muted tiny">{S.noDriversYet}</div>)}

      <div className="eyebrow">Recruit drivers for</div>
      {unmatched.data?.length
        ? (
          <div className="stack">
            {unmatched.data.map((u) => (
              <div key={u.dest_name} className="spread card" style={{ padding: '12px 16px' }}>
                <span>{u.dest_name}</span>
                <span className="pill" style={{ background: 'var(--sunset)', color: '#fff', border: 'none' }}>{u.riders} waiting</span>
              </div>
            ))}
          </div>
        )
        : <div className="muted tiny">No unmatched searches this week.</div>}
    </Screen>
  )
}
