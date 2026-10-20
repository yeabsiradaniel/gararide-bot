import { useNav } from '../nav'
import { S } from '../strings'
import { Screen } from '../ui'
import { Icon } from '../icons'
import { haptic } from '../telegram'

export default function RiderHome() {
  const nav = useNav()
  const go = (s: Parameters<typeof nav.go>[0]) => { haptic(); nav.go(s) }
  const first = (nav.me.full_name || '').split(' ')[0]

  return (
    <Screen>
      <div className="stack-lg reveal">
        <header className="stack" style={{ gap: 10 }}>
          <span className="brand">
            <img className="brand__logo" src="/logo.png" alt="" />
            <span className="brand__name">{S.appName}</span>
          </span>
          <h1>{S.riderHome}</h1>
          {first && <div className="muted">{S.hi(first)}</div>}
        </header>

        {/* 1. Primary Hero Action */}
        <button className="act act--hero" onClick={() => go({ name: 'findRide', mode: 'search' })}>
          <span className="act__bubble"><Icon name="search" size={26} /></span>
          <span className="act__body">
            <div className="act__title">{S.findRide}</div>
            <div className="act__sub">{S.findRideSub}</div>
          </span>
          <span className="act__go"><Icon name="chevronRight" size={20} /></span>
        </button>

        {/* 2. Core Rider Tasks */}
        <button className="act" onClick={() => go({ name: 'findRide', mode: 'request' })}>
          <span className="act__bubble"><Icon name="megaphone" size={24} /></span>
          <span className="act__body">
            <div className="act__title">{S.postRequest}</div>
            <div className="act__sub">{S.postRequestSub}</div>
          </span>
          <span className="act__go"><Icon name="chevronRight" size={20} /></span>
        </button>

        <button className="act" onClick={() => go({ name: 'myBookings' })}>
          <span className="act__bubble"><Icon name="ticket" size={24} /></span>
          <span className="act__body"><div className="act__title">{S.myBookings}</div></span>
          <span className="act__go"><Icon name="chevronRight" size={20} /></span>
        </button>

        {/* 3. Quick Preferences & Commute Shortcuts Strip */}
        <div className="pill-strip">
          <button className="pill" onClick={() => go({ name: 'saved' })}>
            <Icon name="repeat" size={15} />
            <span>{S.saved}</span>
          </button>
          <button className="pill pill--sunset" onClick={() => go({ name: 'womenOnly' })}>
            <Icon name="heart" size={15} />
            <span>{S.womenOnly}</span>
          </button>
        </div>

        {/* 4. Account & Tools */}
        <button className="act" onClick={() => go({ name: 'profile' })}>
          <span className="act__bubble"><Icon name="user" size={24} /></span>
          <span className="act__body"><div className="act__title">{S.profile}</div></span>
          <span className="act__go"><Icon name="chevronRight" size={20} /></span>
        </button>

        {nav.isAdmin && (
          <button className="act" onClick={() => go({ name: 'admin' })}>
            <span className="act__bubble"><Icon name="chart" size={24} /></span>
            <span className="act__body"><div className="act__title">{S.opsTitle}</div></span>
            <span className="act__go"><Icon name="chevronRight" size={20} /></span>
          </button>
        )}

        {nav.me.role === 'driver' && (
          <button className="btn btn--quiet" onClick={() => go({ name: 'driverHome' })}>
            ← {S.postRideInstead}
          </button>
        )}
      </div>
    </Screen>
  )
}
