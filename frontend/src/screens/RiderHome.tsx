import { useNav } from '../nav'
import { S } from '../strings'
import { Screen } from '../ui'
import { haptic } from '../telegram'

export default function RiderHome() {
  const nav = useNav()
  const go = (s: Parameters<typeof nav.go>[0]) => { haptic(); nav.go(s) }
  return (
    <Screen eyebrow={S.appName} title={S.riderHome}>
      <div className="stack">
        <button className="tile tile--primary" onClick={() => go({ name: 'findRide', mode: 'search' })}>
          <span className="tile__icon">🔍</span>
          <span className="tile__body">
            <div className="tile__title">{S.findRide}</div>
            <div className="tile__sub">{S.findRideSub}</div>
          </span>
        </button>
        <button className="tile" onClick={() => go({ name: 'findRide', mode: 'request' })}>
          <span className="tile__icon">✋</span>
          <span className="tile__body">
            <div className="tile__title">{S.postRequest}</div>
            <div className="tile__sub">{S.postRequestSub}</div>
          </span>
        </button>
        <button className="tile" onClick={() => go({ name: 'myBookings' })}>
          <span className="tile__icon">🎫</span>
          <span className="tile__body"><div className="tile__title">{S.myBookings}</div></span>
        </button>
        <div className="row" style={{ gap: 10 }}>
          <button className="tile" style={{ flex: 1 }} onClick={() => go({ name: 'saved' })}>
            <span className="tile__icon">🔁</span>
            <span className="tile__body"><div className="tile__title">{S.saved}</div></span>
          </button>
          <button className="tile" style={{ flex: 1 }} onClick={() => go({ name: 'womenOnly' })}>
            <span className="tile__icon">💜</span>
            <span className="tile__body"><div className="tile__title">{S.womenOnly}</div></span>
          </button>
        </div>
        {nav.isAdmin && (
          <button className="tile" onClick={() => go({ name: 'admin' })}>
            <span className="tile__icon">📊</span>
            <span className="tile__body"><div className="tile__title">Ops</div></span>
          </button>
        )}
      </div>
    </Screen>
  )
}
