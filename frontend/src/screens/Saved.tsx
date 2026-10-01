import { api } from '../api'
import { useNav } from '../nav'
import { S } from '../strings'
import { EmptyState, ErrorView, Loader, Screen, useAsync } from '../ui'
import { Icon } from '../icons'
import { haptic } from '../telegram'

// Saved trips = one-tap repeats. Tapping one re-runs the search for that
// destination tomorrow morning (the "riding tomorrow?" confirm, in-app).
export default function Saved() {
  const nav = useNav()
  const saved = useAsync(() => api.saved(), [])
  if (saved.loading) return <Loader />
  if (saved.error) return <ErrorView msg={saved.error} onRetry={saved.reload} />
  if (!saved.data?.length) return <Screen eyebrow={S.saved}><EmptyState icon="repeat" text={S.noneYet} /></Screen>

  async function remove(id: number) { haptic(); await api.deactivateSaved(id); saved.reload() }

  return (
    <Screen eyebrow={S.appName} title={S.saved}>
      <div className="stack">
        {saved.data.map((s) => (
          <div key={s.id} className="card">
            <div className="spread">
              <button style={{ background: 'none', border: 'none', textAlign: 'start', font: 'inherit', cursor: 'pointer', flex: 1 }}
                      onClick={() => { haptic(); nav.go({ name: 'results', destId: s.dest_place_id, destName: s.dest_name_am, when: 'tomorrow_morning' }) }}>
                <div className="row" style={{ gap: 8, fontWeight: 700 }}><Icon name="repeat" size={18} style={{ color: 'var(--green)' }} /> {s.dest_name_am}</div>
                <div className="tiny muted">{s.depart_time}</div>
              </button>
              <button className="icon-btn" aria-label="remove" onClick={() => remove(s.id)}><Icon name="x" size={16} /></button>
            </div>
          </div>
        ))}
      </div>
    </Screen>
  )
}
