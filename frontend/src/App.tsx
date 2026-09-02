import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, ApiError } from './api'
import type { Me } from './api'
import { backButton, initTelegram } from './telegram'
import { NavCtx } from './nav'
import type { Nav, Screen } from './nav'
import { ErrorView, Loader, Screen as ScreenWrap } from './ui'
import { S } from './strings'
import DriverHome from './screens/DriverHome'
import RiderHome from './screens/RiderHome'
import PostTrip from './screens/PostTrip'
import MyTrips from './screens/MyTrips'
import RequestsNear from './screens/RequestsNear'
import FindRide from './screens/FindRide'
import Results from './screens/Results'
import TripCard from './screens/TripCard'
import MyBookings from './screens/MyBookings'
import WomenOnly from './screens/WomenOnly'
import Saved from './screens/Saved'
import Admin from './screens/Admin'
import AddDriver from './screens/AddDriver'

function Placeholder({ title }: { title: string }) {
  return <ScreenWrap title={title}><div className="muted">በቅርቡ…</div></ScreenWrap>
}

function Register() {
  return (
    <ScreenWrap eyebrow={S.appName} title={S.notRegisteredTitle}>
      <div className="card">{S.notRegisteredBody}</div>
    </ScreenWrap>
  )
}

export default function App() {
  const [me, setMe] = useState<Me | null>(null)
  const [phase, setPhase] = useState<'loading' | 'ready' | 'register' | 'error'>('loading')
  const [err, setErr] = useState<string>()
  const [stack, setStack] = useState<Screen[]>([])

  const boot = useCallback(() => {
    setPhase('loading')
    api.me()
      .then((m) => {
        setMe(m)
        setStack([{ name: m.role === 'driver' ? 'driverHome' : 'riderHome' }])
        setPhase('ready')
      })
      .catch((e) => {
        if (e instanceof ApiError && e.status === 404) setPhase('register')
        else { setErr(e?.message); setPhase('error') }
      })
  }, [])

  useEffect(() => { initTelegram(); boot() }, [boot])

  const back = useCallback(() => setStack((s) => (s.length > 1 ? s.slice(0, -1) : s)), [])
  const nav = useMemo<Nav>(() => ({
    me: me as Me,
    isAdmin: !!me?.is_admin,
    go: (s) => setStack((st) => [...st, s]),
    back,
    reset: (s) => setStack([s]),
  }), [me, back])

  // Telegram hardware back button follows the stack depth.
  const canBack = stack.length > 1
  useEffect(() => {
    if (canBack) { backButton.show(back); return () => backButton.hide(back) }
  }, [canBack, back])

  if (phase === 'loading') return <div className="app"><Loader /></div>
  if (phase === 'error') return <div className="app"><ErrorView msg={err} onRetry={boot} /></div>
  if (phase === 'register') return <div className="app"><Register /></div>

  const current = stack[stack.length - 1]
  const render = (s: Screen) => {
    switch (s.name) {
      case 'driverHome': return <DriverHome />
      case 'riderHome': return <RiderHome />
      case 'postTrip': return <PostTrip />
      case 'myTrips': return <MyTrips />
      case 'requestsNear': return <RequestsNear />
      case 'findRide': return <FindRide mode={s.mode} />
      case 'results': return <Results screen={s} />
      case 'tripCard': return <TripCard card={s.card} />
      case 'myBookings': return <MyBookings />
      case 'womenOnly': return <WomenOnly />
      case 'saved': return <Saved />
      case 'admin': return <Admin />
      case 'addDriver': return <AddDriver />
      default: return <Placeholder title={s.name} />
    }
  }

  return (
    <NavCtx.Provider value={nav}>
      <div className="app">{render(current)}</div>
    </NavCtx.Provider>
  )
}
