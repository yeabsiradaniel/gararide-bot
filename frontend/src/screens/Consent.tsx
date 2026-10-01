import { useState } from 'react'
import { S } from '../strings'
import { Screen } from '../ui'
import { Icon } from '../icons'
import { haptic } from '../telegram'

// One-time rules + data-use acknowledgement, shown before the home on first use.
export default function Consent({ onAgree }: { onAgree: () => Promise<void> }) {
  const [busy, setBusy] = useState(false)
  async function agree() {
    if (busy) return
    setBusy(true); haptic()
    try { await onAgree() } finally { setBusy(false) }
  }
  return (
    <Screen eyebrow={S.appName} title={S.consentTitle}>
      <div className="card" style={{ whiteSpace: 'pre-line', lineHeight: 1.6 }}>{S.consentBody}</div>
      <div className="sticky-actions">
        <button className="btn btn--grad" disabled={busy} onClick={agree}>
          <Icon name="check" size={18} /> {S.agree}
        </button>
      </div>
    </Screen>
  )
}
