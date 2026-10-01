import { useNav } from '../nav'
import { S } from '../strings'
import { Screen } from '../ui'
import { Icon } from '../icons'
import { haptic } from '../telegram'

// View your details; edit language + women preference. (Photo edit is deferred
// until photo storage — cPanel.)
export default function Profile() {
  const nav = useNav()
  const me = nav.me
  const initial = (me.full_name || '?').trim().charAt(0)

  return (
    <Screen eyebrow={S.appName} title={S.profileTitle}>
      <div className="card card--lift stack">
        <div className="row" style={{ gap: 14 }}>
          <span className="avatar avatar--ring"><span>{initial}</span></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontWeight: 800, fontSize: 18 }}>{me.full_name}</div>
            <div className="row" style={{ gap: 8, marginTop: 4 }}>
              <span className="badge badge--verified"><Icon name="check" size={12} /> {me.role === 'driver' ? S.roleDriver : S.roleRider}</span>
              {me.role === 'driver' && me.tower && <span className="muted tiny">Tower {me.tower}</span>}
            </div>
          </div>
        </div>
        <div className="row muted" style={{ gap: 8, borderTop: '1px solid var(--line-soft)', paddingTop: 14 }}>
          <Icon name="phone" size={16} /> <span>{me.phone}</span>
        </div>
        {me.role === 'driver' && me.car_model && (
          <div className="row muted" style={{ gap: 8 }}>
            <Icon name="car" size={16} /> <span>{me.car_model} · <b style={{ color: 'var(--ink)' }}>{me.plate || '—'}</b></span>
          </div>
        )}
      </div>

      <div className="stack" style={{ marginTop: 6 }}>
        <button className="act" onClick={() => { haptic(); nav.toggleLang() }}>
          <span className="act__bubble"><Icon name="globe" size={22} /></span>
          <span className="act__body"><div className="act__title">{S.langRow}</div></span>
          <span className="act__go muted">{nav.lang === 'am' ? 'አማርኛ' : 'English'}</span>
        </button>
        <button className="act act--warm" onClick={() => { haptic(); nav.go({ name: 'womenOnly' }) }}>
          <span className="act__bubble"><Icon name="heart" size={22} /></span>
          <span className="act__body"><div className="act__title">{S.womenOnly}</div></span>
          <span className="act__go"><Icon name="chevronRight" size={20} /></span>
        </button>
        <button className="act" onClick={() => { haptic(); nav.go({ name: 'support' }) }}>
          <span className="act__bubble"><Icon name="alert" size={22} /></span>
          <span className="act__body"><div className="act__title">{S.contactSupport}</div></span>
          <span className="act__go"><Icon name="chevronRight" size={20} /></span>
        </button>
      </div>
    </Screen>
  )
}
