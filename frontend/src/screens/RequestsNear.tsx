import { api } from '../api'
import { S } from '../strings'
import { EmptyState, ErrorView, Loader, Screen, useAsync } from '../ui'
import { fmtWhen } from '../fmt'

export default function RequestsNear() {
  const reqs = useAsync(() => api.requestsNear(), [])
  if (reqs.loading) return <Loader />
  if (reqs.error) return <ErrorView msg={reqs.error} onRetry={reqs.reload} />
  if (!reqs.data?.length) return <Screen eyebrow={S.requestsNear}><EmptyState icon="📋" text={S.noRequestsYet} /></Screen>

  return (
    <Screen eyebrow={S.appName} title={S.requestsNear}>
      <div className="stack">
        {reqs.data.map((r) => (
          <div key={r.request_id} className="card">
            <div className="spread">
              <div>
                <div style={{ fontWeight: 700 }}>{r.rider_name}</div>
                <div className="tiny muted">→ {r.dest_name_am}</div>
              </div>
              <div className="clock2">{fmtWhen(r.window_start)}</div>
            </div>
          </div>
        ))}
      </div>
    </Screen>
  )
}
