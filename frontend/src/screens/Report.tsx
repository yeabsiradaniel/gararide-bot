import { useState } from 'react'
import { api } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { Screen } from '../ui'
import { Icon } from '../icons'
import { haptic, notify } from '../telegram'

// Rider reports the driver of a booked trip. Reaches an admin; the driver is
// never told. Separate from the silent block ("Not this person").
export default function Report({ trip_id, driverName }: { trip_id: number; driverName: string }) {
  const nav = useNav()
  const [reason, setReason] = useState<string>()
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)

  async function send() {
    if (!reason || busy) return
    setBusy(true); haptic()
    try {
      await api.report(trip_id, reason, note.trim() || undefined)
      notify('success')
      alert(S.reportSent)
      nav.back()
    } finally { setBusy(false) }
  }

  return (
    <Screen eyebrow={driverName} title={S.reportTitle}>
      <div className="card muted" style={{ fontSize: 14 }}>{S.reportSub}</div>

      <div className="stack" style={{ marginTop: 4 }}>
        {S.reportReasons.map((r) => {
          const on = reason === r.key
          return (
            <button key={r.key} className="card spread"
                    style={{
                      textAlign: 'start', width: '100%', cursor: 'pointer',
                      borderColor: on ? 'var(--green)' : undefined,
                      background: on ? 'var(--surface)' : undefined,
                    }}
                    onClick={() => { haptic(); setReason(r.key) }}>
              <span style={{ fontWeight: on ? 700 : 500 }}>{r.label}</span>
              {on && <Icon name="check" size={18} style={{ color: 'var(--green)' }} />}
            </button>
          )
        })}
      </div>

      <textarea className="field" rows={3} style={{ marginTop: 12, resize: 'none' }}
                placeholder={S.reportNotePlaceholder}
                value={note} onChange={(e) => setNote(e.target.value)} />

      <div className="sticky-actions">
        <button className="btn btn--grad" disabled={!reason || busy} onClick={send}>
          <Icon name="shield" size={18} /> {S.sendReport}
        </button>
      </div>
    </Screen>
  )
}
