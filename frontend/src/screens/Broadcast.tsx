import { useState } from 'react'
import { api, ApiError } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { Screen } from '../ui'
import { Icon } from '../icons'
import { haptic, notify, showAlert } from '../telegram'

type Audience = 'all' | 'drivers' | 'riders'

// Admin-only. Sends one announcement to everyone / drivers / riders.
export default function Broadcast() {
  const nav = useNav()
  const [audience, setAudience] = useState<Audience>('all')
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)
  const audiences: { key: Audience; label: string }[] = [
    { key: 'all', label: S.audEveryone },
    { key: 'drivers', label: S.audDrivers },
    { key: 'riders', label: S.audRiders },
  ]

  async function send() {
    if (!msg.trim() || busy) return
    setBusy(true); haptic()
    try {
      const { sent } = await api.broadcast(audience, msg.trim())
      notify('success'); await showAlert(S.sentTo(sent)); nav.back()
    } catch (e) {
      notify('error')
      if (e instanceof ApiError && e.status === 429) showAlert(S.rateLimited)
    } finally { setBusy(false) }
  }

  return (
    <Screen eyebrow={S.appName} title={S.broadcastTitle}>
      <div className="muted tiny">{S.broadcastHint}</div>
      <div className="row" style={{ gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
        {audiences.map((a) => (
          <button key={a.key} className={`pill ${audience === a.key ? 'pill--on' : ''}`}
                  style={{ minWidth: 90, justifyContent: 'center' }}
                  onClick={() => { haptic(); setAudience(a.key) }}>{a.label}</button>
        ))}
      </div>
      <textarea className="field" rows={5} style={{ marginTop: 12, resize: 'none' }}
                placeholder={S.broadcastPlaceholder} value={msg}
                onChange={(e) => setMsg(e.target.value)} />
      <div className="sticky-actions">
        <button className="btn btn--grad" disabled={!msg.trim() || busy} onClick={send}>
          <Icon name="megaphone" size={18} /> {S.sendBroadcast}
        </button>
      </div>
    </Screen>
  )
}
