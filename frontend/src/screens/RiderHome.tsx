import { useNav } from '../nav'
import { S } from '../strings'
import { Screen } from '../ui'
import { Icon } from '../icons'
import { haptic } from '../telegram'

export default function RiderHome() {
  const nav = useNav()
  const go = (s: Parameters<typeof nav.go>[0]) => { haptic(); nav.go(s) }
  const first = (nav.me.full_name || '').split(' ')[0]

  const actions = [
    { name: 'findRide', icon: 'search', title: S.findRide, sub: S.findRideSub, hero: true, on: () => go({ name: 'findRide', mode: 'search' }) },
    { name: 'postReq', icon: 'megaphone', title: S.postRequest, sub: S.postRequestSub, on: () => go({ name: 'findRide', mode: 'request' }) },
    { name: 'bookings', icon: 'ticket', title: S.myBookings, on: () => go({ name: 'myBookings' }) },
    { name: 'saved', icon: 'repeat', title: S.saved, on: () => go({ name: 'saved' }) },
    { name: 'women', icon: 'heart', title: S.womenOnly, warm: true, on: () => go({ name: 'womenOnly' }) },
  ]

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

        {actions.map((a) => (
          <button key={a.name} className={`act${a.hero ? ' act--hero' : ''}${a.warm ? ' act--warm' : ''}`} onClick={a.on}>
            <span className="act__bubble"><Icon name={a.icon} size={a.hero ? 26 : 24} /></span>
            <span className="act__body">
              <div className="act__title">{a.title}</div>
              {a.sub && <div className="act__sub">{a.sub}</div>}
            </span>
            <span className="act__go"><Icon name="chevronRight" size={20} /></span>
          </button>
        ))}

        <button className="act" onClick={() => go({ name: 'profile' })}>
          <span className="act__bubble"><Icon name="user" size={24} /></span>
          <span className="act__body"><div className="act__title">{S.profile}</div></span>
          <span className="act__go"><Icon name="chevronRight" size={20} /></span>
        </button>

        {nav.isAdmin && (
          <button className="act" onClick={() => go({ name: 'admin' })}>
            <span className="act__bubble"><Icon name="chart" size={24} /></span>
            <span className="act__body"><div className="act__title">Ops</div></span>
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
