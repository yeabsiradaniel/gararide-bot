import { useState } from 'react'
import type { TripCard as Card } from '../api'
import { api } from '../api'
import { useNav } from '../nav'
import { S, loc } from '../strings'
import { Countdown, Screen } from '../ui'
import { Icon } from '../icons'
import { fmtMoney, fmtWhen } from '../fmt'
import { callPhone, haptic, notify, shareText } from '../telegram'

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

  function share() {
    haptic()
    const car = `${card.car_model || '—'}${card.car_color ? ` · ${card.car_color}` : ''}`
    shareText(S.shareRideMsg({
      driver: card.driver_name, car, plate: card.plate || '—',
      dest: loc(card.dest_name_am, card.dest_name_en), when: fmtWhen(card.depart_at), bay: card.bay,
    }))
  }

  const boardEnd = card.arrived_at ? new Date(card.arrived_at).getTime() + card.dwell_minutes * 60000 : 0
  const boarding = !!card.arrived_at && Date.now() < boardEnd
  const onWayEnd = card.otw_at ? new Date(card.otw_at).getTime() + (card.otw_eta || 0) * 60000 : 0
  const onWay = !card.arrived_at && !!card.otw_at
  const initial = (card.driver_name || '?').trim().charAt(0)

  return (
    <Screen eyebrow={fmtWhen(card.depart_at)} title={card.bay}>
      {onWay && (
        <div className="card spread" style={{ background: 'var(--surface)', borderColor: 'transparent' }}>
          <span className="row" style={{ gap: 8 }}><Icon name="steering" size={18} /> <b>{S.onTheWay}</b></span>
          <span className="price">{S.arrivesIn} <Countdown until={onWayEnd} /></span>
        </div>
      )}
      {boarding && (
        <div className="card spread" style={{ background: 'var(--surface)', borderColor: 'transparent' }}>
          <span className="row" style={{ gap: 8 }}><Icon name="car" size={18} /> <b>{S.driverHere}</b></span>
          <span className="price">{S.boardWithin.replace(':', '')} <Countdown until={boardEnd} /></span>
        </div>
      )}

      <div className="card card--lift stack">
        <div className="row" style={{ gap: 14 }}>
          <span className="avatar avatar--ring"><span>{initial}</span></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontWeight: 800, fontSize: 18 }}>{card.driver_name}</div>
            <div className="row" style={{ gap: 8, marginTop: 4 }}>
              <span className="badge badge--verified"><Icon name="check" size={12} /> {S.verified}</span>
              {card.driver_tower && <span className="muted tiny">{S.towerWord} {card.driver_tower}</span>}
            </div>
          </div>
        </div>

        <div className="row muted" style={{ gap: 8, borderTop: '1px solid var(--line-soft)', paddingTop: 14 }}>
          <Icon name="car" size={18} /><span>{card.car_model || '—'}{card.car_color ? ` · ${card.car_color}` : ''} · <b style={{ color: 'var(--ink)' }}>{card.plate || '—'}</b></span>
        </div>

        <div className="spread">
          <span className="row" style={{ gap: 8 }}><Icon name="pin" size={18} style={{ color: 'var(--green)' }} /> {loc(card.dest_name_am, card.dest_name_en)}</span>
          <span className="price price--xl" style={{ fontSize: 26 }}>{fmtMoney(card.fare)}</span>
        </div>
        <div className="tiny muted">{S.payInCar('')}</div>
      </div>

      <div className="stack">
        <button className="btn btn--grad" onClick={() => callPhone(card.phone)}><Icon name="phone" size={18} /> {S.call}</button>
        <button className="btn btn--ghost" onClick={share}><Icon name="shield" size={18} /> {S.shareRide}</button>
        <button className="btn btn--ghost" disabled={busy} onClick={cancel}>{S.cancelBooking}</button>
        <button className="btn btn--danger"
                disabled={busy} onClick={() => { haptic(); nav.go({ name: 'report', trip_id: card.trip_id, driver_name: card.driver_name }) }}><Icon name="alert" size={17} /> {S.reportProblem}</button>
        <button className="btn btn--quiet"
                disabled={busy} onClick={block}>{S.notThisDriver}</button>
      </div>
    </Screen>
  )
}
