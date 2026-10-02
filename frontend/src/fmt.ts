// Display helpers — mirror gararide/fmt.py.
import { S, activeLang } from './strings'

function ethiopian(d: Date): string {
  let hour = (d.getHours() - 6) % 12
  if (hour <= 0) hour += 12
  const word = d.getHours() >= 0 && d.getHours() < 12 ? S.morning : S.afternoon
  return `${hour}:${String(d.getMinutes()).padStart(2, '0')} ${word}`
}

const pad = (n: number) => String(n).padStart(2, '0')

export function fmtTime(iso: string): string {
  const d = new Date(iso)
  const clock = `${pad(d.getHours())}:${pad(d.getMinutes())}`
  // Amharic shows the dual clock (Gregorian + Ethiopian); English just the 24h time.
  return activeLang === 'en' ? clock : `${clock} (${ethiopian(d)})`
}

export function fmtDay(iso: string): string {
  const d = new Date(iso)
  const today = new Date()
  const a = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const b = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const days = Math.round((a.getTime() - b.getTime()) / 86400000)
  if (days === 0) return S.today
  if (days === 1) return S.tomorrow
  return d.toLocaleDateString(activeLang === 'en' ? 'en-US' : 'en-GB', { month: 'short', day: '2-digit' })
}

export function fmtWhen(iso: string): string {
  return `${fmtDay(iso)} ${fmtTime(iso)}`
}

export function fmtMoney(amount: number): string {
  return `${amount} ${S.birr}`
}

export function fmtPerson(name: string, tower?: string | null): string {
  return tower ? `${name} · ${S.towerWord} ${tower}` : name
}

// 'HH:MM' local time -> dual clock, e.g. '07:00 (1:00 ጠዋት)'.
export function fmtHHMM(hhmm: string): string {
  const [h, m] = hhmm.split(':').map(Number)
  const d = new Date()
  d.setHours(h, m, 0, 0)
  return fmtTime(d.toISOString())
}

// days_mask (bit i = weekday i, Mon=0) -> Amharic label.
export function fmtDays(mask: number): string {
  if (mask === 0b1111111) return S.daysEveryday
  if (mask === 0b0011111) return S.daysWeekdays
  const days = S.dayShort.filter((_, i) => mask & (1 << i))
  return days.length ? days.join(' ') : ''
}
