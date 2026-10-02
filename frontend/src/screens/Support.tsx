import { useState } from 'react'
import { api, ApiError } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { Screen } from '../ui'
import { Icon } from '../icons'
import { haptic, notify, showAlert } from '../telegram'

// Message the admin/support account from inside the app.
export default function Support() {
  const nav = useNav()
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)

  async function send() {
    if (!msg.trim() || busy) return
    setBusy(true); haptic()
    try { await api.support(msg.trim()); notify('success'); await showAlert(S.supportSent); nav.back() }
    catch (e) { notify('error'); if (e instanceof ApiError && e.status === 429) showAlert(S.rateLimited) }
    finally { setBusy(false) }
  }

  return (
    <Screen eyebrow={S.appName} title={S.supportTitle}>
      <div className="card muted" style={{ fontSize: 14 }}>{S.supportHint}</div>
      <textarea className="field" rows={5} style={{ marginTop: 12, resize: 'none' }}
                placeholder={S.supportPlaceholder} value={msg}
                onChange={(e) => setMsg(e.target.value)} />
      <div className="sticky-actions">
        <button className="btn btn--grad" disabled={!msg.trim() || busy} onClick={send}>
          <Icon name="megaphone" size={18} /> {S.sendMessage}
        </button>
      </div>
    </Screen>
  )
}
