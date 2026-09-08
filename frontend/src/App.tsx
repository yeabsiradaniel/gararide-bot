import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, ApiError } from './api'
import type { Me } from './api'
import { backButton, haptic, initTelegram } from './telegram'
import { NavCtx } from './nav'
import type { Nav, Screen } from './nav'
import { ErrorView, Loader, Screen as ScreenWrap } from './ui'
import { S, setActiveLang } from './strings'
import type { Lang } from './strings'

const LANG_KEY = 'gararide_lang'

function LangFab({ lang, onToggle }: { lang: Lang; onToggle: () => void }) {
  // Shows the language you'd switch TO.
  return (
    <button className="lang-fab" onClick={onToggle} aria-label="Change language">
      🌐 {lang === 'am' ? 'EN' : 'አማ'}
    </button>
  )
}
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
  const [lang, setLangState] = useState<Lang>(() => {
    const saved = (localStorage.getItem(LANG_KEY) as Lang) || 'am'
    setActiveLang(saved)  // apply before first paint
    return saved
  })

  const applyLang = useCallback((next: Lang, persist: boolean) => {
    setActiveLang(next)
    localStorage.setItem(LANG_KEY, next)
    setLangState(next)
    if (persist) api.setLang(next).catch(() => { /* not registered yet — ignore */ })
  }, [])

  const toggleLang = useCallback(() => {
    haptic()
    applyLang(lang === 'am' ? 'en' : 'am', true)
  }, [lang, applyLang])

  const boot = useCallback(() => {
    setPhase('loading')
    api.me()
      .then((m) => {
        setMe(m)
        // The server-stored preference wins on load, so a returning user keeps it.
        if (m.lang && m.lang !== (localStorage.getItem(LANG_KEY) as Lang)) {
          applyLang(m.lang, false)
        }
        setStack([{ name: m.role === 'driver' ? 'driverHome' : 'riderHome' }])
        setPhase('ready')
      })
      .catch((e) => {
        if (e instanceof ApiError && e.status === 404) setPhase('register')
        else { setErr(e?.message); setPhase('error') }
      })
  }, [applyLang])

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

  const fab = <LangFab lang={lang} onToggle={toggleLang} />

  if (phase === 'loading') return <div className="app">{fab}<Loader /></div>
  if (phase === 'error') return <div className="app">{fab}<ErrorView msg={err} onRetry={boot} /></div>
  if (phase === 'register') return <div className="app">{fab}<Register /></div>

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
      <div className="app">{fab}{render(current)}</div>
    </NavCtx.Provider>
  )
}
