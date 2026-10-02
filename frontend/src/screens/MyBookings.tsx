import { useState } from 'react'
import { api } from '../api'
import { useNav } from '../nav'
import { S, loc } from '../strings'
import { EmptyState, ErrorView, Loader, Screen, useAsync } from '../ui'
import { Icon } from '../icons'
import { fmtMoney, fmtWhen } from '../fmt'
import { haptic } from '../telegram'

export default function MyBookings() {
  const nav = useNav()
  const [tab, setTab] = useState<'upcoming' | 'history'>('upcoming')
  const bookings = useAsync(() => api.myBookings(), [])
  const history = useAsync(() => api.history(), [])

  const statusLabel = (s: string) =>
    s === 'no_show' ? S.statusNoShow : s === 'cancelled' ? S.cancelledBadge : S.statusCompleted
  const statusWarm = (s: string) => s === 'no_show' || s === 'cancelled'

  return (
    <Screen eyebrow={S.appName} title={S.myBookings}>
      <div className="row" style={{ gap: 8 }}>
        <button className={`pill ${tab === 'upcoming' ? 'pill--on' : ''}`}
                onClick={() => { haptic(); setTab('upcoming') }}>{S.tabUpcoming}</button>
        <button className={`pill ${tab === 'history' ? 'pill--on' : ''}`}
                onClick={() => { haptic(); setTab('history') }}>{S.tabHistory}</button>
      </div>

      {tab === 'upcoming' && (
        bookings.loading ? <Loader />
          : bookings.error ? <ErrorView msg={bookings.error} onRetry={bookings.reload} />
            : !bookings.data?.length ? <EmptyState icon="ticket" text={S.noneYet} />
              : (
                <div className="stack">
                  {bookings.data.map((c) => {
                    if (c.cancelled) {
                      return (
                        <div key={c.booking_id} className="card" style={{ opacity: 0.65 }}>
                          <div className="spread">
                            <div>
                              <div style={{ fontWeight: 700, textDecoration: 'line-through' }}>{c.driver_name} · → {loc(c.dest_name_am, c.dest_name_en)}</div>
                              <div className="clock2">{fmtWhen(c.depart_at)}</div>
                            </div>
                            <span className="pill" style={{ background: 'var(--sunset)', color: '#fff', border: 'none' }}>{S.cancelledBadge}</span>
                          </div>
                        </div>
                      )
                    }
                    const boarding = !!c.arrived_at && Date.now() < new Date(c.arrived_at).getTime() + c.dwell_minutes * 60000
                    return (
                      <button key={c.booking_id} className="card" style={{ textAlign: 'start', cursor: 'pointer', width: '100%' }}
                              onClick={() => { haptic(); nav.go({ name: 'tripCard', card: c }) }}>
                        <div className="spread">
                          <div>
                            <div style={{ fontWeight: 700 }}>{c.driver_name} · → {loc(c.dest_name_am, c.dest_name_en)}</div>
                            <div className="clock2">{fmtWhen(c.depart_at)}</div>
                          </div>
                          {boarding
                            ? <span className="pill pill--on"><Icon name="car" size={15} /> {S.driverHere}</span>
                            : <span className="price">{fmtMoney(c.fare)}</span>}
                        </div>
                      </button>
                    )
                  })}
                </div>
              )
      )}

      {tab === 'history' && (
        history.loading ? <Loader />
          : history.error ? <ErrorView msg={history.error} onRetry={history.reload} />
            : !history.data?.length ? <EmptyState icon="ticket" text={S.noHistory} />
              : (
                <div className="stack">
                  {history.data.map((h) => (
                    <button key={h.booking_id} className="card" style={{ textAlign: 'start', cursor: 'pointer', width: '100%' }}
                            onClick={() => { haptic(); nav.go({ name: 'receipt', ride: h }) }}>
                      <div className="spread">
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontWeight: 700 }}>{h.driver_name} · → {loc(h.dest_name_am, h.dest_name_en)}</div>
                          <div className="clock2">{fmtWhen(h.depart_at)}</div>
                        </div>
                        <div style={{ textAlign: 'end', flexShrink: 0 }}>
                          <div className="price">{fmtMoney(h.fare)}</div>
                          <span className="badge" style={statusWarm(h.status)
                            ? { background: '#FFE9DE', color: 'var(--sunset)' } : undefined}>{statusLabel(h.status)}</span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )
      )}
    </Screen>
  )
}
