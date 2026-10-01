import { useState } from 'react'
import { api } from '../api'
import type { MyTrip } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { Countdown, EmptyState, ErrorView, Loader, Screen, useAsync } from '../ui'
import { Icon } from '../icons'
import { fmtMoney, fmtPerson, fmtWhen } from '../fmt'
import { callPhone, haptic, notify } from '../telegram'

const ETA_CHOICES = [5, 10, 15]

// When the boarding grace ends (epoch ms): from arrival if tapped, else departure.
function boardingEnds(t: MyTrip): number {
  const base = t.arrived_at || t.depart_at
  return new Date(base).getTime() + t.dwell_minutes * 60000
}

// When the driver expects to reach pickup (epoch ms), from the 'on my way' tap.
function arrivesAt(t: MyTrip): number {
  return t.otw_at ? new Date(t.otw_at).getTime() + (t.otw_eta || 0) * 60000 : 0
}

export default function MyTrips() {
  const nav = useNav()
  const trips = useAsync(() => api.myTrips(), [])
  const [picking, setPicking] = useState<number | null>(null)  // trip_id choosing an ETA

  if (trips.loading) return <Loader />
  if (trips.error) return <ErrorView msg={trips.error} onRetry={trips.reload} />
  if (!trips.data?.length) return <Screen eyebrow={S.myTrips}><EmptyState icon="calendar" text={S.noneYet} /></Screen>

  async function paid(id: number) { haptic(); await api.markPaid(id); notify('success'); trips.reload() }
  async function noShow(id: number) { haptic(); await api.markNoShow(id); trips.reload() }
  async function cancel(id: number) { haptic(); await api.cancelTrip(id); trips.reload() }
  async function arrived(id: number) { haptic(); await api.markArrived(id); notify('success'); trips.reload() }
  async function onWay(id: number, eta: number) {
    haptic(); await api.onMyWay(id, eta); notify('success'); setPicking(null); trips.reload()
  }

  return (
    <Screen eyebrow={S.appName} title={S.myTrips}>
      <div className="stack-lg">
        {trips.data.map((t) => {
          const now = Date.now()
          const boarding = !!t.arrived_at && now < boardingEnds(t)
          const canNoShow = now >= boardingEnds(t)
          return (
            <div key={t.trip_id} className="card stack">
              <div className="spread">
                <div>
                  <div style={{ fontWeight: 700 }}>→ {t.dest_name_am}</div>
                  <div className="clock2">{fmtWhen(t.depart_at)}</div>
                </div>
                <div className="row" style={{ gap: 8, flexShrink: 0 }}>
                  <span className="pill pill--on">{t.passengers.length}/{t.seats_total}</span>
                  {!t.arrived_at && (
                    <button className="icon-btn" aria-label="edit"
                            onClick={() => { haptic(); nav.go({ name: 'editTrip', trip: t }) }}><Icon name="edit" size={15} /></button>
                  )}
                </div>
              </div>

              {t.passengers.map((p) => (
                <div key={p.booking_id} className="spread" style={{ borderTop: '1px solid var(--line)', paddingTop: 10 }}>
                  <div>
                    <div>{fmtPerson(p.name, p.tower)}</div>
                    <div className="tiny muted">→ {p.to_name_am} · <span className="price">{fmtMoney(p.fare)}</span></div>
                  </div>
                  <div className="row">
                    <button className="pill" aria-label="call" onClick={() => callPhone(p.phone)}><Icon name="phone" size={16} /></button>
                    {p.paid
                      ? <span className="pill pill--on"><Icon name="check" size={14} /> {S.paid}</span>
                      : <button className="pill" onClick={() => paid(p.booking_id)}>{S.paid}</button>}
                    <button className="btn--quiet" style={{ border: 'none', background: 'none', opacity: canNoShow ? 1 : 0.4 }}
                            disabled={!canNoShow} onClick={() => noShow(p.booking_id)}>{S.noShow}</button>
                  </div>
                </div>
              ))}

              {t.passengers.length > 0 && (() => {
                const collected = t.passengers.filter((p) => p.paid).reduce((s, p) => s + p.fare, 0)
                const paidCount = t.passengers.filter((p) => p.paid).length
                return (
                  <div className="spread" style={{ borderTop: '1px solid var(--line)', paddingTop: 10 }}>
                    <span className="row" style={{ gap: 7, color: 'var(--green)' }}><Icon name="chart" size={16} /> {S.collected}</span>
                    <span><span className="price">{fmtMoney(collected)}</span> <span className="tiny muted">· {S.ofPaid(paidCount, t.passengers.length)}</span></span>
                  </div>
                )
              })()}

              {/* On-the-way + boarding controls */}
              {!t.arrived_at && t.passengers.length > 0 && (
                <>
                  {t.otw_at && (
                    <div className="spread" style={{ background: 'var(--surface)', borderRadius: 12, padding: '10px 14px' }}>
                      <span className="row" style={{ gap: 8 }}><Icon name="steering" size={18} /> {S.onTheWay}</span>
                      <span className="price">{S.arrivesIn} <Countdown until={arrivesAt(t)} onDone={() => trips.reload()} /></span>
                    </div>
                  )}
                  {picking === t.trip_id ? (
                    <div className="stack" style={{ gap: 8 }}>
                      <div className="muted tiny">{S.howFarOut}</div>
                      <div className="row" style={{ gap: 8 }}>
                        {ETA_CHOICES.map((m) => (
                          <button key={m} className="btn btn--ghost" onClick={() => onWay(t.trip_id, m)}>{S.minsOut(m)}</button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <button className="btn btn--ghost" onClick={() => { haptic(); setPicking(t.trip_id) }}>
                      <Icon name="steering" size={18} /> {S.onMyWay}
                    </button>
                  )}
                  <button className="btn btn--grad" onClick={() => arrived(t.trip_id)}><Icon name="car" size={18} /> {S.iveArrived}</button>
                </>
              )}
              {boarding && (
                <div className="spread" style={{ background: 'var(--surface)', borderRadius: 12, padding: '10px 14px' }}>
                  <span>{S.driverHere} · {S.boardWithin}</span>
                  <Countdown until={boardingEnds(t)} onDone={() => trips.reload()} />
                </div>
              )}

              <button className="btn--danger" style={{ border: 'none', background: 'none', textAlign: 'start' }}
                      onClick={() => cancel(t.trip_id)}>{S.cantDrive}</button>
            </div>
          )
        })}
      </div>
    </Screen>
  )
}
