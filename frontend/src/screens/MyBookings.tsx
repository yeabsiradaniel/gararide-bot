import { api } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { EmptyState, ErrorView, Loader, Screen, useAsync } from '../ui'
import { fmtMoney, fmtWhen } from '../fmt'
import { haptic } from '../telegram'

export default function MyBookings() {
  const nav = useNav()
  const bookings = useAsync(() => api.myBookings(), [])
  if (bookings.loading) return <Loader />
  if (bookings.error) return <ErrorView msg={bookings.error} onRetry={bookings.reload} />
  if (!bookings.data?.length) return <Screen eyebrow={S.myBookings}><EmptyState icon="🎫" text={S.noneYet} /></Screen>

  return (
    <Screen eyebrow={S.appName} title={S.myBookings}>
      <div className="stack">
        {bookings.data.map((c) => (
          <button key={c.booking_id} className="card" style={{ textAlign: 'start', cursor: 'pointer' }}
                  onClick={() => { haptic(); nav.go({ name: 'tripCard', card: c }) }}>
            <div className="spread">
              <div>
                <div style={{ fontWeight: 700 }}>{c.driver_name} · → {c.dest_name_am}</div>
                <div className="clock2">{fmtWhen(c.depart_at)}</div>
              </div>
              <span className="price">{fmtMoney(c.fare)}</span>
            </div>
          </button>
        ))}
      </div>
    </Screen>
  )
}
