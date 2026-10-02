import { useState } from 'react'
import { api, ApiError } from '../api'
import type { MyTrip } from '../api'
import { useNav } from '../nav'
import { S, postErrorMsg } from '../strings'
import { Screen } from '../ui'
import { Icon } from '../icons'
import { haptic, notify } from '../telegram'

// Driver edits a posted trip: time, seats, note. Destination/route stay fixed
// (that's a cancel + repost). Can't drop seats below riders already booked.
export default function EditTrip({ trip }: { trip: MyTrip }) {
  const nav = useNav()
  const cap = nav.me.car_seats || trip.seats_total
  const booked = trip.passengers.length
  const [departAt, setDepartAt] = useState(trip.depart_at.slice(0, 16))
  const [seats, setSeats] = useState(trip.seats_total)
  const [note, setNote] = useState(trip.note || '')
  const [busy, setBusy] = useState(false)

  async function save() {
    if (busy) return
    setBusy(true); haptic()
    try {
      await api.editTrip(trip.trip_id, {
        depart_at: departAt.length === 16 ? departAt + ':00' : departAt,
        seats, note: note.trim() || null,
      })
      notify('success'); alert(S.tripUpdated); nav.back()
    } catch (e) {
      notify('error')
      if (e instanceof ApiError && e.detail) alert(postErrorMsg(e.detail))
    } finally { setBusy(false) }
  }

  return (
    <Screen eyebrow={`→ ${trip.dest_name_am}`} title={S.editTripTitle}>
      <label className="stack">
        <div className="tiny muted">{S.whenLeave}</div>
        <input className="field" type="datetime-local" value={departAt}
               onChange={(e) => setDepartAt(e.target.value)} />
      </label>

      <label className="stack" style={{ marginTop: 14 }}>
        <div className="tiny muted">{S.freeSeats}</div>
        <div className="row" style={{ flexWrap: 'wrap' }}>
          {Array.from({ length: cap }, (_, i) => i + 1).map((n) => (
            <button key={n} className={`pill ${seats === n ? 'pill--on' : ''}`}
                    style={{ minWidth: 56, justifyContent: 'center', opacity: n < booked ? 0.4 : 1 }}
                    disabled={n < booked} onClick={() => { haptic(); setSeats(n) }}>{n}</button>
          ))}
        </div>
      </label>

      <label className="stack" style={{ marginTop: 14 }}>
        <div className="tiny muted">{S.noteLabel}</div>
        <input className="field" placeholder={S.notePlaceholder}
               value={note} onChange={(e) => setNote(e.target.value)} />
      </label>

      <div className="sticky-actions">
        <button className="btn btn--grad" disabled={busy} onClick={save}>
          <Icon name="check" size={18} /> {S.saveChanges}
        </button>
      </div>
    </Screen>
  )
}
