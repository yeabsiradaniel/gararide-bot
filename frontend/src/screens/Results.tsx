import { useState } from 'react'
import { api, ApiError } from '../api'
import { useNav } from '../nav'
import type { Screen as Scr } from '../nav'
import { S } from '../strings'
import { ErrorView, Loader, Screen, useAsync } from '../ui'
import { fmtMoney, fmtPerson, fmtWhen } from '../fmt'
import { windowFor } from '../util'
import { haptic, notify } from '../telegram'

export default function Results({ screen }: { screen: Extract<Scr, { name: 'results' }> }) {
  const nav = useNav()
  const { destId, destName, when } = screen
  const res = useAsync(() => api.search(destId, when), [destId, when])
  const [busy, setBusy] = useState(false)

  if (res.loading) return <Loader />
  if (res.error) return <ErrorView msg={res.error} onRetry={res.reload} />
  const data = res.data!

  async function book(tripId: number, toPlaceId: number) {
    if (busy) return
    setBusy(true); haptic()
    try {
      const card = await api.book(tripId, toPlaceId)
      notify('success')
      nav.go({ name: 'tripCard', card })
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) alert(S.seatTaken)
    } finally { setBusy(false) }
  }

  async function postRequest() {
    setBusy(true); haptic()
    const [ws, we] = windowFor(when)
    try { await api.postRequest(destId, ws, we); notify('success'); nav.reset({ name: 'riderHome' }) }
    finally { setBusy(false) }
  }

  if (data.matches.length) {
    return (
      <Screen eyebrow={S.neighboursGoing} title={destName}>
        <div className="stack">
          {data.matches.map((m) => (
            <button key={m.trip_id} className="card" disabled={busy}
                    style={{ textAlign: 'start', cursor: 'pointer' }}
                    onClick={() => book(m.trip_id, destId)}>
              <div className="spread">
                <div>
                  <div style={{ fontWeight: 700 }}>{fmtPerson(m.driver_name, m.driver_tower)}</div>
                  <div className="clock2">{fmtWhen(m.depart_at)} · {m.seats_left} {S.seatsWord}</div>
                </div>
                <span className="price">{fmtMoney(m.fare)}</span>
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
              <button key={m.trip_id} className="card" disabled={busy}
                      style={{ textAlign: 'start', cursor: 'pointer' }}
                      onClick={() => book(m.trip_id, m.dest_place_id)}>
                <div className="spread">
                  <div>
                    <div style={{ fontWeight: 700 }}>{m.driver_name} · → {m.dest_name_am}</div>
                    <div className="clock2">{fmtWhen(m.depart_at)} · {S.partway}</div>
                  </div>
                  <span className="price">{fmtMoney(m.fare)}</span>
                </div>
              </button>
            ))}
          </div>
        </>
      )}
      {data.demand_count > 0 && (
        <div className="card" style={{ background: 'var(--surface)', border: 'none' }}>
          🌱 {S.demandLine(data.demand_count)}
        </div>
      )}
      <div className="sticky-actions stack">
        <button className="btn btn--sunset" disabled={busy} onClick={postRequest}>✋ {S.postMyRequest}</button>
      </div>
    </Screen>
  )
}
