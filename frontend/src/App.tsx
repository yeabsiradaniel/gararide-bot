import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, ApiError } from './api'
import type { Me } from './api'
import { backButton, haptic, initTelegram } from './telegram'
import { NavCtx } from './nav'
import type { Nav, Screen } from './nav'
import { ErrorView, Loader, Screen as ScreenWrap } from './ui'
import { S, setActiveLang } from './strings'
import type { Lang } from './strings'
import { Icon } from './icons'

const LANG_KEY = 'gararide_lang'
const INTRO_KEY = 'gararide_intro_seen'

function LangFab({ lang, onToggle }: { lang: Lang; onToggle: () => void }) {
  // Shows the language you'd switch TO.
  return (
    <button className="lang-fab" onClick={onToggle} aria-label="Change language">
      <Icon name="globe" size={15} /> {lang === 'am' ? 'EN' : 'አማ'}
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
import Receipt from './screens/Receipt'
import RidePreview from './screens/RidePreview'
import Report from './screens/Report'
import EditTrip from './screens/EditTrip'
import Profile from './screens/Profile'
import Support from './screens/Support'
import Broadcast from './screens/Broadcast'
import Consent from './screens/Consent'
import Walkthrough from './screens/Walkthrough'

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
  const [introSeen, setIntroSeen] = useState(() => {
    try { return localStorage.getItem(INTRO_KEY) === '1' } catch { return false }
  })
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
    lang,
    toggleLang,
  }), [me, back, lang, toggleLang])

  // Telegram hardware back button. Register the handler ONCE (so taps never
  // stack up and pop multiple levels), and only toggle its visibility with depth.
  useEffect(() => {
    backButton.onClick(back)
    return () => backButton.offClick(back)
  }, [back])
  const canBack = stack.length > 1
  useEffect(() => {
    if (canBack) backButton.show()
    else backButton.hide()
  }, [canBack])

  const fab = <LangFab lang={lang} onToggle={toggleLang} />

  if (phase === 'loading') return <div className="app">{fab}<Loader /></div>
  if (phase === 'error') return <div className="app">{fab}<ErrorView msg={err} onRetry={boot} /></div>
  if (phase === 'register') return <div className="app">{fab}<Register /></div>

  // One-time consent gate before anything else.
  if (me && !me.consented) {
    return (
      <div className="app">{fab}
        <Consent onAgree={async () => { await api.consent(); setMe({ ...me, consented: true }) }} />
      </div>
    )
  }

  // First-open "how it works", once per device (after consent).
  if (me && !introSeen) {
    return (
      <div className="app">{fab}
        <Walkthrough role={me.role} onDone={() => {
          try { localStorage.setItem(INTRO_KEY, '1') } catch { /* private mode */ }
          setIntroSeen(true)
        }} />
      </div>
    )
  }

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
      case 'addDriver': return <AddDriver edit={s.edit} />
      case 'receipt': return <Receipt ride={s.ride} />
      case 'ridePreview': return <RidePreview p={s} />
      case 'report': return <Report trip_id={s.trip_id} driverName={s.driver_name} />
      case 'editTrip': return <EditTrip trip={s.trip} />
      case 'profile': return <Profile />
      case 'support': return <Support />
      case 'broadcast': return <Broadcast />
      default: return <Placeholder title={s.name} />
    }
  }

  return (
    <NavCtx.Provider value={nav}>
      <div className="app">{fab}{render(current)}</div>
    </NavCtx.Provider>
  )
}
