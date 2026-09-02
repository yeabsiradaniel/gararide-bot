import { useMemo, useState } from 'react'
import { api } from '../api'
import type { Place } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { Loader, Screen, useAsync } from '../ui'
import { WHENS, windowFor } from '../util'
import { haptic, notify } from '../telegram'

const whenLabel: Record<string, string> = {
  tomorrow_morning: S.tomorrowMorning, today: S.today, weekend: S.weekend,
}

export default function FindRide({ mode }: { mode: 'search' | 'request' }) {
  const nav = useNav()
  const places = useAsync(() => api.places(), [])
  const [dest, setDest] = useState<Place>()
  const [busy, setBusy] = useState(false)

  const destinations = useMemo(
    () => (places.data || []).filter((p) => p.sort_order !== 0),
    [places.data],
  )

  if (places.loading) return <Loader />

  if (!dest) {
    return (
      <Screen eyebrow={mode === 'search' ? S.findRide : S.postRequest} title={S.whereTo}>
        <div className="stack">
          {destinations.map((p) => (
            <button key={p.id} className="tile" onClick={() => { haptic(); setDest(p) }}>
              <span className="tile__icon">📍</span>
              <span className="tile__body"><div className="tile__title">{p.name_am}</div></span>
            </button>
          ))}
        </div>
      </Screen>
    )
  }

  async function pickWhen(when: string) {
    haptic()
    if (mode === 'search') {
      nav.go({ name: 'results', destId: dest!.id, destName: dest!.name_am, when })
      return
    }
    setBusy(true)
    const [ws, we] = windowFor(when)
    try {
      await api.postRequest(dest!.id, ws, we)
      notify('success')
      nav.reset({ name: 'riderHome' })
    } finally { setBusy(false) }
  }

  return (
    <Screen eyebrow={dest.name_am} title={S.when}>
      <div className="stack">
        {WHENS.map((w) => (
          <button key={w.key} className="tile" disabled={busy} onClick={() => pickWhen(w.key)}>
            <span className="tile__icon">{w.icon}</span>
            <span className="tile__body"><div className="tile__title">{whenLabel[w.key]}</div></span>
          </button>
        ))}
      </div>
    </Screen>
  )
}
