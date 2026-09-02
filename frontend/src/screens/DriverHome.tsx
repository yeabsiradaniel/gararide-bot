import { useState } from 'react'
import { api } from '../api'
import type { DriverRoute } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { Screen, useAsync } from '../ui'
import { fmtDays, fmtHHMM } from '../fmt'
import { confirmDialog, haptic, notify } from '../telegram'

export default function DriverHome() {
  const nav = useNav()
  const go = (s: Parameters<typeof nav.go>[0]) => { haptic(); nav.go(s) }
  const routes = useAsync(() => api.routes(), [])
  const [busy, setBusy] = useState<number>()

  async function postTomorrow(r: DriverRoute) {
    setBusy(r.id)
    try {
      const res = await api.postRoute(r.id)
      notify(res.already ? 'warning' : 'success')
      nav.go({ name: 'myTrips' })
    } catch {
      notify('error')
    } finally { setBusy(undefined) }
  }

  async function remove(r: DriverRoute) {
    if (!(await confirmDialog(`${r.dest_name_am} — ${fmtHHMM(r.depart_time)}?`))) return
    setBusy(r.id)
    try { await api.deleteRoute(r.id); routes.reload() }
    finally { setBusy(undefined) }
  }

  return (
    <Screen eyebrow={S.appName} title={S.driverHome}>
      {routes.data?.length ? (
        <div className="stack">
          <div className="eyebrow" style={{ margin: 0 }}>{S.myRoutes}</div>
          {routes.data.map((r) => (
            <div key={r.id} className="card stack" style={{ gap: 10 }}>
              <div className="spread">
                <div className="stack" style={{ gap: 2, minWidth: 0 }}>
                  <span><b>{r.dest_name_am}</b></span>
                  <span className="muted tiny">{fmtHHMM(r.depart_time)} · {r.seats} {S.seatsWord}{r.days_mask ? ` · ${fmtDays(r.days_mask)}` : ''}</span>
                </div>
                <button className="icon-btn" aria-label="remove" disabled={busy === r.id}
                        onClick={() => remove(r)}>🗑</button>
              </div>
              <button className="btn btn--grad" disabled={busy === r.id}
                      onClick={() => postTomorrow(r)}>{S.postTomorrow}</button>
            </div>
          ))}
        </div>
      ) : null}

      <div className="stack">
        <button className="tile tile--primary" onClick={() => go({ name: 'postTrip' })}>
          <span className="tile__icon">🚗</span>
          <span className="tile__body">
            <div className="tile__title">{S.postTrip}</div>
            <div className="tile__sub">{S.postTripSub}</div>
          </span>
        </button>
        <button className="tile" onClick={() => go({ name: 'requestsNear' })}>
          <span className="tile__icon">📋</span>
          <span className="tile__body">
            <div className="tile__title">{S.requestsNear}</div>
            <div className="tile__sub">{S.requestsNearSub}</div>
          </span>
        </button>
        <button className="tile" onClick={() => go({ name: 'myTrips' })}>
          <span className="tile__icon">🗓</span>
          <span className="tile__body"><div className="tile__title">{S.myTrips}</div></span>
        </button>
        {nav.isAdmin && (
          <button className="tile" onClick={() => go({ name: 'admin' })}>
            <span className="tile__icon">📊</span>
            <span className="tile__body"><div className="tile__title">Ops</div></span>
          </button>
        )}
      </div>
      <button className="btn btn--quiet" onClick={() => go({ name: 'riderHome' })}>
        {S.iNeedARide} →
      </button>
    </Screen>
  )
}
