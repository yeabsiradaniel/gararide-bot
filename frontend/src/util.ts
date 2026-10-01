// Client-side window computation for rider requests (mirrors the backend
// _window() mapping used by /trips/search).
const pad = (n: number) => String(n).padStart(2, '0')
const iso = (d: Date) =>
  `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:00`

export function windowFor(when: string): [string, string] {
  const now = new Date()
  if (when === 'today') {
    const e = new Date(now); e.setHours(23, 59, 0, 0)
    return [iso(now), iso(e)]
  }
  if (when === 'weekend') {
    const days = (6 - now.getDay() + 7) % 7   // getDay: Sun=0..Sat=6
    const sat = new Date(now); sat.setDate(now.getDate() + days); sat.setHours(0, 0, 0, 0)
    const sun = new Date(sat); sun.setDate(sat.getDate() + 1); sun.setHours(23, 59, 0, 0)
    return [iso(sat), iso(sun)]
  }
  const b = new Date(now); b.setDate(now.getDate() + 1)
  const s = new Date(b); s.setHours(6, 0, 0, 0)
  const e = new Date(b); e.setHours(9, 0, 0, 0)
  return [iso(s), iso(e)]
}

export const WHENS = [
  { key: 'tomorrow_morning', icon: 'sunrise' },
  { key: 'today', icon: 'sun' },
  { key: 'weekend', icon: 'calendar' },
] as const
