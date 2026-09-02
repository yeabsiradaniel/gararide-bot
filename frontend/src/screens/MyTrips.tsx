import { api } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { EmptyState, ErrorView, Loader, Screen, useAsync } from '../ui'
import { fmtMoney, fmtPerson, fmtWhen } from '../fmt'
import { callPhone, haptic, notify } from '../telegram'

export default function MyTrips() {
  const nav = useNav()
  const trips = useAsync(() => api.myTrips(), [])

  if (trips.loading) return <Loader />
  if (trips.error) return <ErrorView msg={trips.error} onRetry={trips.reload} />
  if (!trips.data?.length) return <Screen eyebrow={S.myTrips}><EmptyState icon="🗓" text={S.noneYet} /></Screen>

  async function paid(id: number) { haptic(); await api.markPaid(id); notify('success'); trips.reload() }
  async function noShow(id: number) { haptic(); await api.markNoShow(id); trips.reload() }
  async function cancel(id: number) { haptic(); await api.cancelTrip(id); trips.reload() }

  return (
    <Screen eyebrow={S.appName} title={S.myTrips}>
      <div className="stack-lg">
        {trips.data.map((t) => (
          <div key={t.trip_id} className="card stack">
            <div className="spread">
              <div>
                <div style={{ fontWeight: 700 }}>→ {t.dest_name_am}</div>
                <div className="clock2">{fmtWhen(t.depart_at)}</div>
              </div>
              <span className="pill pill--on">{t.passengers.length}/{t.seats_total}</span>
            </div>
            {t.passengers.map((p) => (
              <div key={p.booking_id} className="spread" style={{ borderTop: '1px solid var(--line)', paddingTop: 10 }}>
                <div>
                  <div>{fmtPerson(p.name, p.tower)}</div>
                  <div className="tiny muted">→ {p.to_name_am} · <span className="price">{fmtMoney(p.fare)}</span></div>
                </div>
                <div className="row">
                  <button className="pill" onClick={() => callPhone(p.phone)}>📞</button>
                  {p.paid
                    ? <span className="pill pill--on">✓ {S.paid}</span>
                    : <button className="pill" onClick={() => paid(p.booking_id)}>{S.paid}</button>}
                  <button className="btn--quiet" style={{ border: 'none', background: 'none' }}
                          onClick={() => noShow(p.booking_id)}>{S.noShow}</button>
                </div>
              </div>
            ))}
            <button className="btn--danger" style={{ border: 'none', background: 'none', textAlign: 'start' }}
                    onClick={() => cancel(t.trip_id)}>{S.cantDrive}</button>
          </div>
        ))}
      </div>
    </Screen>
  )
}
