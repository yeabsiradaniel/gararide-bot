import { useState } from 'react'
import { api } from '../api'
import type { RosterDriver } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { ErrorView, Loader, Screen, useAsync } from '../ui'
import { Icon } from '../icons'
import { confirmDialog, haptic, notify } from '../telegram'

export default function Admin() {
  const nav = useNav()
  const ops = useAsync(() => api.ops(), [])
  const unmatched = useAsync(() => api.unmatched(), [])
  const drivers = useAsync(() => api.drivers(), [])
  const reports = useAsync(() => api.reports(), [])
  const [busy, setBusy] = useState<string>()  // phone being removed
  const [resolving, setResolving] = useState<number>()
  const reasonLabel = (k: string) => S.reportReasons.find((r) => r.key === k)?.label ?? k
  if (ops.loading) return <Loader />
  if (ops.error) return <ErrorView msg={ops.error} onRetry={ops.reload} />
  const o = ops.data!

  const stats: [string, number][] = [
    ['Trips today', o.trips], ['Seats filled', o.seats], ['No-shows', o.no_shows],
    ['Open requests', o.open_requests], ['Registered', o.users],
  ]

  async function remove(d: RosterDriver) {
    if (!(await confirmDialog(S.removeDriverConfirm(d.full_name)))) return
    setBusy(d.phone)
    try {
      await api.removeDriver(d.phone)
      notify('success'); drivers.reload(); ops.reload()
    } catch {
      notify('error')
    } finally { setBusy(undefined) }
  }

  async function resolveReport(id: number) {
    setResolving(id)
    try { await api.resolveReport(id); notify('success'); reports.reload() }
    catch { notify('error') }
    finally { setResolving(undefined) }
  }

  return (
    <Screen eyebrow={S.appName} title="Ops">
      <div className="stack">
        {stats.map(([label, n]) => (
          <div key={label} className="spread card" style={{ padding: '12px 16px' }}>
            <span className="muted">{label}</span>
            <span className="price" style={{ fontSize: 20 }}>{n}</span>
          </div>
        ))}
      </div>

      {reports.data?.length ? (
        <>
          <div className="eyebrow">Reports</div>
          <div className="stack">
            {reports.data.map((r) => (
              <div key={r.id} className="card stack" style={{ gap: 8, borderColor: 'var(--sunset)' }}>
                <div className="spread">
                  <span><b>{r.reported_name}</b>{r.reported_tower ? ` · ${r.reported_tower}` : ''}</span>
                  <span className="pill" style={{ background: 'var(--sunset)', color: '#fff', border: 'none' }}>{reasonLabel(r.reason)}</span>
                </div>
                {r.note && <div className="muted tiny">“{r.note}”</div>}
                <div className="spread">
                  <span className="muted tiny">by {r.reporter_name}</span>
                  <button className="btn btn--ghost" style={{ width: 'auto', padding: '6px 14px' }}
                          disabled={resolving === r.id} onClick={() => resolveReport(r.id)}>
                    <Icon name="check" size={16} /> Resolve
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : null}

      <button className="tile" onClick={() => { haptic(); nav.go({ name: 'broadcast' }) }}>
        <span className="tile__icon"><Icon name="megaphone" size={22} /></span>
        <span className="tile__body">
          <div className="tile__title">Broadcast</div>
          <div className="tile__sub">Message everyone / drivers / riders</div>
        </span>
      </button>

      <button className="tile tile--primary" onClick={() => { haptic(); nav.go({ name: 'addDriver' }) }}>
        <span className="tile__icon"><Icon name="plus" size={22} /></span>
        <span className="tile__body">
          <div className="tile__title">{S.addDriver}</div>
          <div className="tile__sub">{S.addDriverSub}</div>
        </span>
      </button>

      <div className="eyebrow">{S.driverRoster}</div>
      {drivers.loading && <div className="muted tiny">{S.loading}</div>}
      {drivers.data?.length
        ? (
          <div className="stack">
            {drivers.data.map((d) => (
              <div key={d.phone} className="spread card" style={{ padding: '12px 16px' }}>
                <div className="stack" style={{ gap: 2, minWidth: 0 }}>
                  <span><b>{d.full_name}</b>{d.is_female ? ' ♀' : ''}</span>
                  <span className="muted tiny">
                    {d.tower} · {d.car_model || '—'}{d.car_color ? ` · ${d.car_color}` : ''}{d.car_seats ? ` · ${d.car_seats} ${S.seatsWord}` : ''}
                  </span>
                  {d.ratings && (d.ratings.up > 0 || d.ratings.down > 0) && (
                    <span className="row tiny" style={{ gap: 10, marginTop: 2 }}>
                      <span className="row" style={{ gap: 3, color: 'var(--green)' }}><Icon name="thumbsUp" size={13} /> {d.ratings.up}</span>
                      <span className="row" style={{ gap: 3, color: 'var(--sunset)' }}><Icon name="thumbsDown" size={13} /> {d.ratings.down}</span>
                    </span>
                  )}
                </div>
                <div className="row" style={{ gap: 8, flexShrink: 0 }}>
                  <span className="pill" style={d.onboarded
                    ? { background: 'var(--green)', color: '#fff', border: 'none' }
                    : undefined}>{d.onboarded ? S.onboarded : S.pending}</span>
                  <button className="icon-btn" aria-label="edit"
                          onClick={() => { haptic(); nav.go({ name: 'addDriver', edit: d }) }}><Icon name="edit" size={15} /></button>
                  <button className="icon-btn" aria-label="remove" disabled={busy === d.phone}
                          onClick={() => remove(d)}><Icon name="trash" size={16} /></button>
                </div>
              </div>
            ))}
          </div>
        )
        : (!drivers.loading && <div className="muted tiny">{S.noDriversYet}</div>)}

      <div className="eyebrow">Recruit drivers for</div>
      {unmatched.data?.length
        ? (
          <div className="stack">
            {unmatched.data.map((u) => (
              <div key={u.dest_name} className="spread card" style={{ padding: '12px 16px' }}>
                <span>{u.dest_name}</span>
                <span className="pill" style={{ background: 'var(--sunset)', color: '#fff', border: 'none' }}>{u.riders} waiting</span>
              </div>
            ))}
          </div>
        )
        : <div className="muted tiny">No unmatched searches this week.</div>}
    </Screen>
  )
}
