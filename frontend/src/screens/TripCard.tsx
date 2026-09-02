import { useState } from 'react'
import type { TripCard as Card } from '../api'
import { api } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { Screen } from '../ui'
import { fmtMoney, fmtWhen } from '../fmt'
import { callPhone, haptic, notify } from '../telegram'

// Shown after booking, and reused to render an upcoming booking.
export default function TripCard({ card, onGone }: { card: Card; onGone?: () => void }) {
  const nav = useNav()
  const [busy, setBusy] = useState(false)

  async function cancel() {
    setBusy(true); haptic()
    try { await api.cancelBooking(card.booking_id); notify('warning'); done() }
    finally { setBusy(false) }
  }
  async function block() {
    setBusy(true); haptic()
    try { await api.block(card.trip_id); await api.cancelBooking(card.booking_id); done() }
    finally { setBusy(false) }
  }
  function done() { onGone ? onGone() : nav.reset({ name: 'riderHome' }) }

  return (
    <Screen eyebrow={fmtWhen(card.depart_at)} title={card.bay}>
      <div className="card stack">
        <div className="spread">
          <div>
            <div style={{ fontWeight: 800, fontSize: 18 }}>👤 {card.driver_name}
              {card.driver_tower ? ` · Tower ${card.driver_tower}` : ''}</div>
            <div className="muted">🚗 {card.car_model || '—'} · <b>{card.plate || '—'}</b></div>
          </div>
        </div>
        <div className="spread" style={{ borderTop: '1px solid var(--line)', paddingTop: 12 }}>
          <div>📍 → {card.dest_name_am}</div>
          <div className="price" style={{ fontSize: 18 }}>{fmtMoney(card.fare)}</div>
        </div>
        <div className="tiny muted">{S.payInCar('')}</div>
      </div>

      <div className="stack">
        <button className="btn btn--grad" onClick={() => callPhone(card.phone)}>📞 {S.call}</button>
        <button className="btn btn--ghost" disabled={busy} onClick={cancel}>{S.cancelBooking}</button>
        <button className="btn--quiet" style={{ border: 'none', background: 'none' }}
                disabled={busy} onClick={block}>{S.notThisDriver}</button>
      </div>
    </Screen>
  )
}
