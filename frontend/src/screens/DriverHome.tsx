import { useState } from 'react'
import { api } from '../api'
import type { DriverRoute } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { Screen, useAsync } from '../ui'
import { Icon } from '../icons'
import { fmtDays, fmtHHMM } from '../fmt'
import { confirmDialog, haptic, notify } from '../telegram'

export default function DriverHome() {
  const nav = useNav()
  const go = (s: Parameters<typeof nav.go>[0]) => { haptic(); nav.go(s) }
  const routes = useAsync(() => api.routes(), [])
  const [busy, setBusy] = useState<number>()
  const first = (nav.me.full_name || '').split(' ')[0]

  async function postTomorrow(r: DriverRoute) {
    setBusy(r.id)
    try {
      const res = await api.postRoute(r.id)
      notify(res.already ? 'warning' : 'success')
      nav.go({ name: 'myTrips' })
    } catch { notify('error') } finally { setBusy(undefined) }
  }

  async function remove(r: DriverRoute) {
    if (!(await confirmDialog(`${r.dest_name_am} · ${fmtHHMM(r.depart_time)}?`))) return
    setBusy(r.id)
    try { await api.deleteRoute(r.id); routes.reload() } finally { setBusy(undefined) }
  }

  return (
    <Screen>
      <div className="stack-lg reveal">
        <header className="stack" style={{ gap: 10 }}>
          <span className="brand">
            <img className="brand__logo" src="/logo.png" alt="" />
            <span className="brand__name">{S.appName}</span>
          </span>
          <h1>{S.driverHome}</h1>
          {first && <div className="muted">{S.hi(first)}</div>}
        </header>

        {routes.data?.length ? (
          <div className="stack">
            <div className="section-label">{S.myRoutes}</div>
            {routes.data.map((r) => (
              <div key={r.id} className="card card--flat stack" style={{ gap: 12 }}>
                <div className="spread">
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 700 }}>{r.dest_name_am}</div>
                    <div className="muted tiny">{fmtHHMM(r.depart_time)} · {r.seats} {S.seatsWord}{r.days_mask ? ` · ${fmtDays(r.days_mask)}` : ''}</div>
                  </div>
                  <button className="icon-btn" aria-label="remove" disabled={busy === r.id} onClick={() => remove(r)}><Icon name="trash" size={17} /></button>
                </div>
                <button className="btn btn--grad" disabled={busy === r.id} onClick={() => postTomorrow(r)}>{S.postTomorrow}</button>
              </div>
            ))}
          </div>
        ) : null}

        <button className="act act--hero" onClick={() => go({ name: 'postTrip' })}>
          <span className="act__bubble"><Icon name="car" size={26} /></span>
          <span className="act__body">
            <div className="act__title">{S.postTrip}</div>
            <div className="act__sub">{S.postTripSub}</div>
          </span>
          <span className="act__go"><Icon name="chevronRight" size={20} /></span>
        </button>

        <button className="act" onClick={() => go({ name: 'requestsNear' })}>
          <span className="act__bubble"><Icon name="clipboard" size={24} /></span>
          <span className="act__body">
            <div className="act__title">{S.requestsNear}</div>
            <div className="act__sub">{S.requestsNearSub}</div>
          </span>
          <span className="act__go"><Icon name="chevronRight" size={20} /></span>
        </button>

        <button className="act" onClick={() => go({ name: 'myTrips' })}>
          <span className="act__bubble"><Icon name="calendar" size={24} /></span>
          <span className="act__body"><div className="act__title">{S.myTrips}</div></span>
          <span className="act__go"><Icon name="chevronRight" size={20} /></span>
        </button>

        <button className="act" onClick={() => go({ name: 'profile' })}>
          <span className="act__bubble"><Icon name="user" size={24} /></span>
          <span className="act__body"><div className="act__title">{S.profile}</div></span>
          <span className="act__go"><Icon name="chevronRight" size={20} /></span>
        </button>

        {nav.isAdmin && (
          <button className="act" onClick={() => go({ name: 'admin' })}>
            <span className="act__bubble"><Icon name="chart" size={24} /></span>
            <span className="act__body"><div className="act__title">Ops</div></span>
            <span className="act__go"><Icon name="chevronRight" size={20} /></span>
          </button>
        )}

        <button className="btn btn--quiet" onClick={() => go({ name: 'riderHome' })}>{S.iNeedARide} →</button>
      </div>
    </Screen>
  )
}
