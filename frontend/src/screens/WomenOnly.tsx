import { useState } from 'react'
import { api } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { Screen } from '../ui'
import { haptic, notify } from '../telegram'

export default function WomenOnly() {
  const nav = useNav()
  const [wo, setWo] = useState(nav.me.women_only)
  const [wp, setWp] = useState(nav.me.women_present)
  const [busy, setBusy] = useState(false)

  const Toggle = ({ on, set, label }: { on: boolean; set: (v: boolean) => void; label: string }) => (
    <button className={`check ${on ? 'check--on' : ''}`} onClick={() => { haptic(); set(!on) }}>
      <span className="check__box">{on ? '☑' : '☐'}</span>
      <span>{label}</span>
    </button>
  )

  async function save() {
    setBusy(true); haptic()
    try { await api.setWomenOnly(wo, wp); notify('success'); nav.back() }
    finally { setBusy(false) }
  }

  return (
    <Screen eyebrow="💜" title={S.womenOnly}>
      <div className="stack">
        <Toggle on={wo} set={setWo} label={S.womenDriversOnly} />
        <Toggle on={wp} set={setWp} label={S.womenPresent} />
      </div>
      <div className="sticky-actions">
        <button className="btn" disabled={busy} onClick={save}>{S.save}</button>
      </div>
    </Screen>
  )
}
