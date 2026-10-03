import { useState } from 'react'
import { api, ApiError } from '../api'
import { useNav } from '../nav'
import type { Screen as Scr } from '../nav'
import { S, loc } from '../strings'
import { Screen } from '../ui'
import { Icon } from '../icons'
import { fmtMoney, fmtWhen } from '../fmt'
import { confirmDialog, haptic, notify, showAlert } from '../telegram'

// Shown when a rider taps a driver in the results — driver + car, NO phone.
// The seat is only taken (and the phone revealed) after "Take a seat".
export default function RidePreview({ p }: { p: Extract<Scr, { name: 'ridePreview' }> }) {
  const nav = useNav()
  const [busy, setBusy] = useState(false)
  const initial = (p.driver_name || '?').trim().charAt(0)

  async function take() {
    if (busy) return
    setBusy(true); haptic()
    try {
      const card = await api.book(p.trip_id, p.to_place_id)
      notify('success')
      // Land the booked card on top of home, so back goes Home (not the old
      // search/preview, which is now stale after the seat is taken).
      nav.reset({ name: nav.me.role === 'driver' ? 'driverHome' : 'riderHome' })
      nav.go({ name: 'tripCard', card })
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        const d = e.detail
        if (d === 'booking_closed') { await showAlert(S.bookingClosed); nav.back() }
        else if (d === 'time_conflict') { await showAlert(S.timeConflict) }
        else {
          // Seat filled under them — offer the waitlist, then bounce to the list.
          if (await confirmDialog(S.waitlistAsk)) {
            try { await api.joinWaitlist(p.trip_id, p.to_place_id); await showAlert(S.waitlistJoined) } catch { /* noop */ }
          }
          nav.back()
        }
      }
    } finally { setBusy(false) }
  }

  return (
    <Screen eyebrow={fmtWhen(p.depart_at)} title={loc(p.dest_name_am, p.dest_name_en)}>
      <div className="card card--lift stack">
        <div className="row" style={{ gap: 14 }}>
          <span className="avatar avatar--ring"><span>{initial}</span></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontWeight: 800, fontSize: 18 }}>{p.driver_name}</div>
            <div className="row" style={{ gap: 8, marginTop: 4 }}>
              <span className="badge badge--verified"><Icon name="check" size={12} /> {S.verified}</span>
              {p.driver_tower && <span className="muted tiny">{S.towerWord} {p.driver_tower}</span>}
            </div>
          </div>
        </div>

        <div className="row muted" style={{ gap: 8, borderTop: '1px solid var(--line-soft)', paddingTop: 14 }}>
          <Icon name="car" size={18} /><span>{p.car_model || '—'}{p.car_color ? ` · ${p.car_color}` : ''} · <b style={{ color: 'var(--ink)' }}>{p.plate || '—'}</b></span>
        </div>

        <div className="spread">
          <span className="row" style={{ gap: 8 }}><Icon name="pin" size={18} style={{ color: 'var(--green)' }} /> {loc(p.dest_name_am, p.dest_name_en)}</span>
          <span className="price price--xl" style={{ fontSize: 26 }}>{fmtMoney(p.fare)}</span>
        </div>
        {typeof p.seats_left === 'number' && <div className="tiny" style={{ color: 'var(--green)' }}>{p.seats_left} {S.seatsWord}</div>}
      </div>

      <div className="sticky-actions">
        <button className="btn btn--grad" disabled={busy} onClick={take}>{S.takeSeat}</button>
      </div>
    </Screen>
  )
}
