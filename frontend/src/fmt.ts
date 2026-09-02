// Display helpers — mirror gararide/fmt.py. Every time shows both clocks.
import { S } from './strings'

const MORNING = 'ጠዋት'
const AFTERNOON = 'ከሰዓት'

function ethiopian(d: Date): string {
  let hour = (d.getHours() - 6) % 12
  if (hour <= 0) hour += 12
  const word = d.getHours() >= 0 && d.getHours() < 12 ? MORNING : AFTERNOON
  return `${hour}:${String(d.getMinutes()).padStart(2, '0')} ${word}`
}

const pad = (n: number) => String(n).padStart(2, '0')

export function fmtTime(iso: string): string {
  const d = new Date(iso)
  return `${pad(d.getHours())}:${pad(d.getMinutes())} (${ethiopian(d)})`
}

export function fmtDay(iso: string): string {
  const d = new Date(iso)
  const today = new Date()
  const a = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const b = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const days = Math.round((a.getTime() - b.getTime()) / 86400000)
  if (days === 0) return 'ዛሬ'
  if (days === 1) return 'ነገ'
  return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit' })
}

export function fmtWhen(iso: string): string {
  return `${fmtDay(iso)} ${fmtTime(iso)}`
}

export function fmtMoney(birr: number): string {
  return `${birr} ብር`
}

export function fmtPerson(name: string, tower?: string | null): string {
  return tower ? `${name} · Tower ${tower}` : name
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
