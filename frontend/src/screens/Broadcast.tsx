import { useState } from 'react'
import { api } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { Screen } from '../ui'
import { Icon } from '../icons'
import { haptic, notify } from '../telegram'

type Audience = 'all' | 'drivers' | 'riders'
const AUDIENCES: { key: Audience; label: string }[] = [
  { key: 'all', label: 'Everyone' },
  { key: 'drivers', label: 'Drivers' },
  { key: 'riders', label: 'Riders' },
]

// Admin-only. Sends one announcement to everyone / drivers / riders.
export default function Broadcast() {
  const nav = useNav()
  const [audience, setAudience] = useState<Audience>('all')
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)

  async function send() {
    if (!msg.trim() || busy) return
    setBusy(true); haptic()
    try {
      const { sent } = await api.broadcast(audience, msg.trim())
      notify('success'); alert(`Sent to ${sent}.`); nav.back()
    } catch { notify('error') } finally { setBusy(false) }
  }

  return (
    <Screen eyebrow={S.appName} title="Broadcast">
      <div className="muted tiny">Send an announcement. It reaches people in the bot chat.</div>
      <div className="row" style={{ gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
        {AUDIENCES.map((a) => (
          <button key={a.key} className={`pill ${audience === a.key ? 'pill--on' : ''}`}
                  style={{ minWidth: 90, justifyContent: 'center' }}
                  onClick={() => { haptic(); setAudience(a.key) }}>{a.label}</button>
        ))}
      </div>
      <textarea className="field" rows={5} style={{ marginTop: 12, resize: 'none' }}
                placeholder="Your message…" value={msg}
                onChange={(e) => setMsg(e.target.value)} />
      <div className="sticky-actions">
        <button className="btn btn--grad" disabled={!msg.trim() || busy} onClick={send}>
          <Icon name="megaphone" size={18} /> Send broadcast
        </button>
      </div>
    </Screen>
  )
}
