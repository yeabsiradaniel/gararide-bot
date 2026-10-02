import { useState } from 'react'
import type { HistoryRide } from '../api'
import { api, ApiError } from '../api'
import { S, loc } from '../strings'
import { Screen } from '../ui'
import { Icon } from '../icons'
import { fmtMoney, fmtWhen } from '../fmt'
import { confirmDialog, haptic, notify, showAlert } from '../telegram'

// Receipt for a past ride (opened from My seats -> History). Completed rides can
// be rated 👍/👎 — an admin-only signal the driver never sees.
export default function Receipt({ ride }: { ride: HistoryRide }) {
  const warm = ride.status === 'no_show' || ride.status === 'cancelled'
  const statusLabel = ride.status === 'no_show' ? S.statusNoShow
    : ride.status === 'cancelled' ? S.cancelledBadge : S.statusCompleted
  const initial = (ride.driver_name || '?').trim().charAt(0)

  const [rating, setRating] = useState<1 | -1 | null>(ride.rating)
  const [busy, setBusy] = useState(false)
  async function rate(value: 1 | -1) {
    if (busy) return
    setBusy(true); haptic()
    const prev = rating
    setRating(value)                           // optimistic
    try { await api.rate(ride.booking_id, value); notify('success') }
    catch { setRating(prev); notify('error') }
    finally { setBusy(false) }
  }

  const [reported, setReported] = useState(false)
  async function flagNoShow() {
    if (!(await confirmDialog(S.driverNoShowConfirm))) return
    haptic()
    try { await api.driverNoShow(ride.booking_id); setReported(true); notify('success'); showAlert(S.driverNoShowSent) }
    catch (e) { notify('error'); if (e instanceof ApiError && e.status === 429) showAlert(S.rateLimited) }
  }

  return (
    <Screen eyebrow={fmtWhen(ride.depart_at)} title={ride.bay}>
      <div className="card card--lift stack">
        <div className="row" style={{ gap: 14 }}>
          <span className="avatar avatar--ring"><span>{initial}</span></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontWeight: 800, fontSize: 18 }}>{ride.driver_name}</div>
            {ride.driver_tower && <div className="muted tiny">{S.towerWord} {ride.driver_tower}</div>}
          </div>
          <span className="badge" style={warm ? { background: '#FFE9DE', color: 'var(--sunset)' } : undefined}>{statusLabel}</span>
        </div>

        <div className="row muted" style={{ gap: 8, borderTop: '1px solid var(--line-soft)', paddingTop: 14 }}>
          <Icon name="car" size={18} /><span>{ride.car_model || '—'}{ride.car_color ? ` · ${ride.car_color}` : ''} · <b style={{ color: 'var(--ink)' }}>{ride.plate || '—'}</b></span>
        </div>

        <div className="spread">
          <span className="row" style={{ gap: 8 }}><Icon name="pin" size={18} style={{ color: 'var(--green)' }} /> {loc(ride.dest_name_am, ride.dest_name_en)}</span>
          <span className="price price--xl" style={{ fontSize: 26 }}>{fmtMoney(ride.fare)}</span>
        </div>
        {ride.paid && <div className="row tiny" style={{ gap: 6, color: 'var(--green)' }}><Icon name="check" size={14} /> {S.paid}</div>}
      </div>

      {ride.status === 'completed' && (
        <div className="card stack" style={{ gap: 12, alignItems: 'center' }}>
          <span className="muted">{rating ? S.rateThanks : S.rateRide}</span>
          <div className="row" style={{ gap: 14 }}>
            <button className="rate-btn" aria-label="good" disabled={busy}
                    data-on={rating === 1} onClick={() => rate(1)}>
              <Icon name="thumbsUp" size={24} />
            </button>
            <button className="rate-btn rate-btn--down" aria-label="bad" disabled={busy}
                    data-on={rating === -1} onClick={() => rate(-1)}>
              <Icon name="thumbsDown" size={24} />
            </button>
          </div>
        </div>
      )}

      {ride.status === 'completed' && !reported && (
        <button className="btn btn--danger" onClick={flagNoShow}>
          <Icon name="alert" size={17} /> {S.driverNoShow}
        </button>
      )}
    </Screen>
  )
}
