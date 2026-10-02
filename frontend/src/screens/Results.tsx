import { useState } from 'react'
import { api } from '../api'
import { useNav } from '../nav'
import type { Screen as Scr } from '../nav'
import { S, loc } from '../strings'
import { ErrorView, Loader, Screen, useAsync, usePoll } from '../ui'
import { Icon } from '../icons'
import { fmtMoney, fmtWhen } from '../fmt'
import { windowFor } from '../util'
import { haptic, notify } from '../telegram'

export default function Results({ screen }: { screen: Extract<Scr, { name: 'results' }> }) {
  const nav = useNav()
  const { destId, destNameAm, destNameEn, when } = screen
  const destName = loc(destNameAm, destNameEn)
  const res = useAsync(() => api.search(destId, when), [destId, when])
  usePoll(res.refresh)   // keep the list live so filled/expired rides drop off
  const [busy, setBusy] = useState(false)

  if (res.loading) return <Loader />
  if (res.error) return <ErrorView msg={res.error} onRetry={res.reload} />
  const data = res.data!

  async function postRequest() {
    setBusy(true); haptic()
    const [ws, we] = windowFor(when)
    try { await api.postRequest(destId, ws, we); notify('success'); nav.reset({ name: 'riderHome' }) }
    finally { setBusy(false) }
  }

  if (data.matches.length) {
    return (
      <Screen eyebrow={S.neighboursGoing} title={destName}>
        <div className="stack reveal">
          {data.matches.map((m) => (
            <button key={m.trip_id} className="card card--lift"
                    style={{ textAlign: 'start', cursor: 'pointer', width: '100%' }}
                    onClick={() => { haptic(); nav.go({ name: 'ridePreview', trip_id: m.trip_id, to_place_id: destId, dest_name_am: destNameAm, dest_name_en: destNameEn, driver_name: m.driver_name, driver_tower: m.driver_tower, car_model: m.car_model, car_color: m.car_color, plate: m.plate, depart_at: m.depart_at, fare: m.fare, seats_left: m.seats_left }) }}>
              <div className="row" style={{ gap: 13 }}>
                <span className="avatar avatar--ring"><span>{(m.driver_name || '?').trim().charAt(0)}</span></span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="row" style={{ gap: 7 }}>
                    <span style={{ fontWeight: 700 }}>{m.driver_name}</span>
                    <span className="badge badge--verified"><Icon name="check" size={11} /> {S.verified}</span>
                  </div>
                  <div className="clock2" style={{ marginTop: 3 }}>
                    {fmtWhen(m.depart_at)}{m.driver_tower ? ` · ${S.towerWord} ${m.driver_tower}` : ''}
                  </div>
                  <div className="tiny" style={{ marginTop: 2, color: 'var(--green)' }}>{m.seats_left} {S.seatsWord}</div>
                </div>
                <div style={{ textAlign: 'end', flexShrink: 0 }}>
                  <div className="price" style={{ fontSize: 19 }}>{fmtMoney(m.fare)}</div>
                  <span className="tiny muted">{S.takeSeat}</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      </Screen>
    )
  }

  // never-empty: near-misses + social proof + post request
  return (
    <Screen title={destName}>
      <div className="card muted">{S.noExact(destName)}</div>
      {data.near_misses.length > 0 && (
        <>
          <div className="eyebrow">{S.closeToWhat}</div>
          <div className="stack">
            {data.near_misses.map((m) => (
              <button key={m.trip_id} className="card"
                      style={{ textAlign: 'start', cursor: 'pointer', width: '100%' }}
                      onClick={() => { haptic(); nav.go({ name: 'ridePreview', trip_id: m.trip_id, to_place_id: m.dest_place_id, dest_name_am: m.dest_name_am, dest_name_en: m.dest_name_en, driver_name: m.driver_name, driver_tower: m.driver_tower, car_model: m.car_model, car_color: m.car_color, plate: m.plate, depart_at: m.depart_at, fare: m.fare }) }}>
                <div className="row" style={{ gap: 13 }}>
                  <span className="avatar avatar--ring"><span>{(m.driver_name || '?').trim().charAt(0)}</span></span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 700 }}>{m.driver_name}</div>
                    <div className="clock2 row" style={{ gap: 6, marginTop: 3 }}>
                      <Icon name="pin" size={14} style={{ color: 'var(--green)' }} /> {loc(m.dest_name_am, m.dest_name_en)} · {fmtWhen(m.depart_at)}
                    </div>
                  </div>
                  <div style={{ textAlign: 'end', flexShrink: 0 }}>
                    <div className="price" style={{ fontSize: 18 }}>{fmtMoney(m.fare)}</div>
                    <span className="tiny muted">{S.partway}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </>
      )}
      {data.demand_count > 0 && (
        <div className="card row" style={{ background: 'var(--surface)', border: 'none', gap: 10, color: 'var(--green)' }}>
          <Icon name="users" size={20} /> <span style={{ color: 'var(--ink)' }}>{S.demandLine(data.demand_count)}</span>
        </div>
      )}
      <div className="sticky-actions stack">
        <button className="btn btn--sunset" disabled={busy} onClick={postRequest}><Icon name="megaphone" size={18} /> {S.postMyRequest}</button>
      </div>
    </Screen>
  )
}
