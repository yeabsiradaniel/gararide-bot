import { useState } from 'react'
import { api, ApiError } from '../api'
import type { RosterDriver } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { Screen } from '../ui'
import { Icon } from '../icons'
import { haptic, notify } from '../telegram'

export default function AddDriver({ edit }: { edit?: RosterDriver }) {
  const nav = useNav()
  const isEdit = !!edit
  const [phone, setPhone] = useState(edit?.phone ?? '')
  const [name, setName] = useState(edit?.full_name ?? '')
  const [tower, setTower] = useState(edit?.tower ?? '')
  const [car, setCar] = useState(edit?.car_model ?? '')
  const [color, setColor] = useState(edit?.car_color ?? '')
  const [plate, setPlate] = useState(edit?.plate ?? '')
  const [seats, setSeats] = useState<number | undefined>(edit?.car_seats ?? undefined)
  const [female, setFemale] = useState(edit?.is_female ?? false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string>()
  const [done, setDone] = useState<string>()

  const ready = phone.trim() && name.trim() && tower.trim() && seats

  async function submit() {
    if (!ready || busy) return
    setBusy(true); setErr(undefined)
    const body = {
      phone: phone.trim(), full_name: name.trim(), tower: tower.trim(),
      car_model: car.trim() || null, car_color: color.trim() || null,
      plate: plate.trim() || null, car_seats: seats!, is_female: female,
    }
    try {
      if (isEdit) {
        await api.updateDriver(edit!.phone, body)
        notify('success'); nav.back()  // Admin remounts on back -> fresh roster
      } else {
        const d = await api.addDriver(body)
        notify('success'); setDone(d.full_name)
      }
    } catch (e) {
      notify('error')
      setErr(e instanceof ApiError ? (e.detail || `HTTP ${e.status}`) : S.errorGeneric)
    } finally { setBusy(false) }
  }

  function again() {
    haptic()
    setPhone(''); setName(''); setTower(''); setCar(''); setColor(''); setPlate('')
    setSeats(undefined); setFemale(false); setDone(undefined); setErr(undefined)
  }

  if (done) {
    return (
      <Screen eyebrow={S.appName} title={S.driverAdded}>
        <div className="card stack">
          <div><b>{done}</b> · {S.pending}</div>
          <div className="tiny muted">{S.notRegisteredBody}</div>
        </div>
        <div className="sticky-actions stack">
          <button className="btn btn--grad" onClick={again}>{S.addDriver}</button>
          <button className="btn btn--ghost" onClick={() => nav.back()}>{S.driverRoster}</button>
        </div>
      </Screen>
    )
  }

  const SEATS = [2, 3, 4, 5, 6, 7, 12]

  return (
    <Screen eyebrow={isEdit ? S.driverRoster : S.addDriverSub} title={isEdit ? S.editDriver : S.addDriver}>
      <div className="stack">
        <label className="stack">
          <div className="tiny muted">{S.fldPhone}</div>
          <input className="field" type="tel" inputMode="tel" placeholder="09…"
                 value={phone} disabled={isEdit} readOnly={isEdit}
                 style={isEdit ? { opacity: 0.6 } : undefined}
                 onChange={(e) => setPhone(e.target.value)} />
        </label>
        <label className="stack">
          <div className="tiny muted">{S.fldName}</div>
          <input className="field" value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label className="stack">
          <div className="tiny muted">{S.fldTower}</div>
          <input className="field" placeholder="B4" value={tower}
                 onChange={(e) => setTower(e.target.value)} />
        </label>
        <label className="stack">
          <div className="tiny muted">{S.fldCar}</div>
          <input className="field" placeholder="Toyota Corolla" value={car}
                 onChange={(e) => setCar(e.target.value)} />
        </label>
        <label className="stack">
          <div className="tiny muted">{S.fldColor}</div>
          <input className="field" placeholder="White" value={color}
                 onChange={(e) => setColor(e.target.value)} />
        </label>
        <label className="stack">
          <div className="tiny muted">{S.fldPlate}</div>
          <input className="field" placeholder="3-AA 21457" value={plate}
                 onChange={(e) => setPlate(e.target.value)} />
        </label>
        <div className="stack">
          <div className="tiny muted">{S.fldSeats}</div>
          <div className="row" style={{ flexWrap: 'wrap' }}>
            {SEATS.map((n) => (
              <button key={n} className={`pill ${seats === n ? 'pill--on' : ''}`}
                      style={{ minWidth: 52, justifyContent: 'center' }}
                      onClick={() => { haptic(); setSeats(n) }}>{n}</button>
            ))}
          </div>
        </div>
        <button className={`check ${female ? 'check--on' : ''}`}
                onClick={() => { haptic(); setFemale((v) => !v) }}>
          <span className="check__box"><Icon name={female ? 'checkSquare' : 'square'} size={22} /></span>
          <span>{S.fldWomanDriver}</span>
        </button>
      </div>

      {err && <div className="card" style={{ color: 'var(--sunset)' }}>{err}</div>}

      <div className="sticky-actions">
        <button className="btn btn--grad" disabled={!ready || busy} onClick={submit}>
          {busy ? S.loading : isEdit ? S.saveChanges : S.saveDriver}
        </button>
      </div>
    </Screen>
  )
}
