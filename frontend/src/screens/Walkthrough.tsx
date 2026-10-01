import { S } from '../strings'
import { Screen } from '../ui'
import { Icon } from '../icons'
import { haptic } from '../telegram'

// Role-specific "how it works", shown once on first open (after consent).
export default function Walkthrough({ role, onDone }: { role: 'driver' | 'rider'; onDone: () => void }) {
  const steps = role === 'driver' ? S.driverSteps : S.riderSteps
  return (
    <Screen eyebrow={S.appName} title={S.howItWorks}>
      <div className="stack-lg reveal">
        {steps.map((s, i) => (
          <div key={i} className="act" style={{ cursor: 'default' }}>
            <span className="act__bubble"><Icon name={s.icon} size={24} /></span>
            <span className="act__body">
              <div className="act__title">{s.title}</div>
              <div className="act__sub">{s.sub}</div>
            </span>
          </div>
        ))}
      </div>
      <div className="sticky-actions">
        <button className="btn btn--grad" onClick={() => { haptic(); onDone() }}>{S.getStarted}</button>
      </div>
    </Screen>
  )
}
