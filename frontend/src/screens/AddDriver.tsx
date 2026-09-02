import { useState } from 'react'
import { api, ApiError } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { Screen } from '../ui'
import { haptic, notify } from '../telegram'

export default function AddDriver() {
  const nav = useNav()
  const [phone, setPhone] = useState('')
  const [name, setName] = useState('')
  const [tower, setTower] = useState('')
  const [car, setCar] = useState('')
  const [plate, setPlate] = useState('')
  const [seats, setSeats] = useState<number>()
  const [female, setFemale] = useState(false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string>()
  const [done, setDone] = useState<string>()

  const ready = phone.trim() && name.trim() && tower.trim() && seats

  async function submit() {
    if (!ready || busy) return
    setBusy(true); setErr(undefined)
    try {
      const d = await api.addDriver({
        phone: phone.trim(), full_name: name.trim(), tower: tower.trim(),
        car_model: car.trim() || null, plate: plate.trim() || null,
        car_seats: seats!, is_female: female,
      })
      notify('success'); setDone(d.full_name)
    } catch (e) {
      notify('error')
      setErr(e instanceof ApiError ? (e.detail || `HTTP ${e.status}`) : 'ስህተት ተፈጥሯል')
    } finally { setBusy(false) }
  }

  function again() {
    haptic()
    setPhone(''); setName(''); setTower(''); setCar(''); setPlate('')
    setSeats(undefined); setFemale(false); setDone(undefined); setErr(undefined)
  }

  if (done) {
    return (
      <Screen eyebrow={S.appName} title={S.driverAdded}>
        <div className="card stack">
          <div><b>{done}</b> — {S.pending}</div>
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
    <Screen eyebrow={S.addDriverSub} title={S.addDriver}>
      <div className="stack">
        <label className="stack">
          <div className="tiny muted">{S.fldPhone}</div>
          <input className="field" type="tel" inputMode="tel" placeholder="09…"
                 value={phone} onChange={(e) => setPhone(e.target.value)} />
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
          <span className="check__box">{female ? '☑' : '☐'}</span>
          <span>{S.fldWomanDriver} ♀</span>
        </button>
      </div>

      {err && <div className="card" style={{ color: 'var(--sunset)' }}>{err}</div>}

      <div className="sticky-actions">
        <button className="btn btn--grad" disabled={!ready || busy} onClick={submit}>
          {busy ? S.loading : S.saveDriver}
        </button>
      </div>
    </Screen>
  )
}
