import { useMemo, useState } from 'react'
import { api } from '../api'
import type { DropoffOptions, PostedTrip } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { Loader, Screen, useAsync } from '../ui'
import { fmtMoney, fmtWhen } from '../fmt'
import { haptic, notify } from '../telegram'

const SLOTS = ['06:45', '07:00', '07:15']
const pad = (n: number) => String(n).padStart(2, '0')

function tomorrowAt(hhmm: string): string {
  const [h, m] = hhmm.split(':').map(Number)
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(h)}:${pad(m)}:00`
}

type Step = 'dest' | 'drops' | 'when' | 'seats' | 'confirm' | 'done'

export default function PostTrip() {
  const nav = useNav()
  const cap = nav.me.car_seats || 3
  const places = useAsync(() => api.places(), [])
  const [step, setStep] = useState<Step>('dest')
  const [destId, setDestId] = useState<number>()
  const [opts, setOpts] = useState<DropoffOptions>()
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [departAt, setDepartAt] = useState<string>()
  const [seats, setSeats] = useState<number>()
  const [note, setNote] = useState('')
  const [posted, setPosted] = useState<PostedTrip>()
  const [busy, setBusy] = useState(false)
  const [daysMask, setDaysMask] = useState(0b0011111)  // Mon–Fri
  const [routeState, setRouteState] = useState<'idle' | 'picking' | 'saved'>('idle')

  const destinations = useMemo(
    () => (places.data || []).filter((p) => p.sort_order !== 0),
    [places.data],
  )

  async function pickDest(id: number) {
    haptic()
    setDestId(id)
    const o = await api.dropoffOptions(id)
    setOpts(o)
    setSelected(new Set(o.intermediate.map((p) => p.id)))  // pre-tick common stops
    setStep('drops')
  }

  function toggle(id: number) {
    haptic()
    setSelected((s) => {
      const n = new Set(s)
      n.has(id) ? n.delete(id) : n.add(id)
      return n
    })
  }

  function pickSlot(hhmm: string) { haptic(); setDepartAt(tomorrowAt(hhmm)); setStep('seats') }

  async function submit(n: number) {
    setSeats(n); setBusy(true)
    try {
      const t = await api.postTrip({
        dest_place_id: destId!, dropoff_place_ids: [...selected],
        depart_at: departAt!, seats: n, note: note || null,
      })
      notify('success'); setPosted(t); setStep('done')
    } finally { setBusy(false) }
  }

  if (places.loading) return <Loader />

  if (step === 'dest') {
    return (
      <Screen eyebrow={S.postTrip} title={S.whereTo}>
        <div className="stack">
          {destinations.map((p) => (
            <button key={p.id} className="tile" onClick={() => pickDest(p.id)}>
              <span className="tile__icon">📍</span>
              <span className="tile__body"><div className="tile__title">{p.name_am}</div></span>
            </button>
          ))}
        </div>
      </Screen>
    )
  }

  if (step === 'drops' && opts) {
    return (
      <Screen eyebrow={S.postTrip} title={S.dropoffsTitle}>
        <div className="muted tiny">{S.dropoffsHint}</div>
        <div className="stack">
          {opts.intermediate.map((p) => {
            const on = selected.has(p.id)
            return (
              <button key={p.id} className={`check ${on ? 'check--on' : ''}`} onClick={() => toggle(p.id)}>
                <span className="check__box">{on ? '☑' : '☐'}</span>
                <span>{p.name_am}</span>
              </button>
            )
          })}
          <div className="check check--fixed">
            <span className="check__box">📍</span>
            <span>{S.destinationLabel}: <b>{opts.destination.name_am}</b></span>
          </div>
        </div>
        <div className="sticky-actions">
          <button className="btn" onClick={() => { haptic(); setStep('when') }}>→</button>
        </div>
      </Screen>
    )
  }

  if (step === 'when') {
    return (
      <Screen eyebrow={S.postTrip} title={S.whenLeave}>
        <div className="stack">
          {SLOTS.map((slot) => (
            <button key={slot} className="tile" onClick={() => pickSlot(slot)}>
              <span className="tile__icon">🕖</span>
              <span className="tile__body"><div className="tile__title">{slot}</div></span>
            </button>
          ))}
          <label className="card stack">
            <div className="tiny muted">{S.anotherTime}</div>
            <input className="field" type="datetime-local"
                   onChange={(e) => e.target.value && setDepartAt(e.target.value + ':00')} />
            <button className="btn btn--ghost" disabled={!departAt}
                    onClick={() => setStep('seats')}>→</button>
          </label>
        </div>
      </Screen>
    )
  }

  if (step === 'seats') {
    return (
      <Screen eyebrow={S.postTrip} title={S.freeSeats}>
        <div className="row" style={{ flexWrap: 'wrap' }}>
          {Array.from({ length: cap }, (_, i) => i + 1).map((n) => (
            <button key={n} className="pill" style={{ minWidth: 56, justifyContent: 'center' }}
                    disabled={busy} onClick={() => submit(n)}>{n}</button>
          ))}
        </div>
        <label className="stack">
          <div className="tiny muted">{S.noteLabel}</div>
          <input className="field" placeholder={S.notePlaceholder}
                 value={note} onChange={(e) => setNote(e.target.value)} />
        </label>
      </Screen>
    )
  }

  async function saveRoute() {
    setBusy(true)
    try {
      await api.saveRoute({
        dest_place_id: destId!, dropoff_place_ids: [...selected],
        depart_time: departAt!.slice(11, 16), seats: seats!, days_mask: daysMask,
      })
      notify('success'); setRouteState('saved')
    } finally { setBusy(false) }
  }

  if (step === 'done' && posted) {
    return (
      <Screen eyebrow={S.posted} title={opts?.destination.name_am}>
        <div className="card stack">
          <div className="spread"><span className="muted">{fmtWhen(posted.depart_at)}</span>
            <span className="pill pill--on">{posted.seats} {S.seatsWord}</span></div>
          <div className="tiny muted">{S.ridersPay}</div>
          {posted.fares.map((f) => (
            <div key={f.place_id} className="spread">
              <span>{f.name_am}</span><span className="price">{fmtMoney(f.fare)}</span>
            </div>
          ))}
        </div>

        {routeState === 'saved'
          ? <div className="card" style={{ color: 'var(--green)' }}>{S.routeSaved}</div>
          : routeState === 'idle'
            ? <button className="btn btn--ghost" onClick={() => { haptic(); setRouteState('picking') }}>{S.saveRoute}</button>
            : (
              <div className="card stack">
                <div className="tiny muted">{S.myRoutes}</div>
                <div className="row" style={{ flexWrap: 'wrap' }}>
                  {S.dayShort.map((d, i) => (
                    <button key={i} className={`pill ${daysMask & (1 << i) ? 'pill--on' : ''}`}
                            style={{ minWidth: 46, justifyContent: 'center' }}
                            onClick={() => { haptic(); setDaysMask((m) => m ^ (1 << i)) }}>{d}</button>
                  ))}
                </div>
                <button className="btn btn--grad" disabled={busy || !daysMask} onClick={saveRoute}>{S.save}</button>
              </div>
            )}

        <div className="sticky-actions">
          <button className="btn btn--grad" onClick={() => nav.reset({ name: 'driverHome' })}>{S.home}</button>
        </div>
      </Screen>
    )
  }

  return <Loader />
}
