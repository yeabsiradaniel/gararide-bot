// Thin wrapper over Telegram's WebApp global (telegram-web-app.js).
// No SDK dependency — just typed access to what the Mini App needs.

interface BackButton {
  show(): void
  hide(): void
  onClick(cb: () => void): void
  offClick(cb: () => void): void
}
interface Haptic {
  impactOccurred(style: 'light' | 'medium' | 'heavy'): void
  notificationOccurred(type: 'error' | 'success' | 'warning'): void
}
interface TgWebApp {
  initData: string
  initDataUnsafe: { user?: { id: number; first_name?: string } }
  colorScheme: 'light' | 'dark'
  ready(): void
  expand(): void
  close(): void
  openLink(url: string): void
  openTelegramLink(url: string): void
  setHeaderColor?(color: string): void
  setBackgroundColor?(color: string): void
  showConfirm?(message: string, callback: (ok: boolean) => void): void
  BackButton: BackButton
  HapticFeedback?: Haptic
}
declare global {
  interface Window { Telegram?: { WebApp: TgWebApp } }
}

export const tg = window.Telegram?.WebApp

export function initTelegram(): void {
  try {
    tg?.ready()
    tg?.expand()
    tg?.setHeaderColor?.('#0DA200')
    tg?.setBackgroundColor?.('#FBFEF9')
  } catch { /* running outside Telegram */ }
}

// initData for auth. In a browser (dev) it is empty; VITE_DEV_INITDATA lets you
// paste a real one for local testing outside Telegram.
export function initData(): string {
  return tg?.initData || (import.meta.env.VITE_DEV_INITDATA as string) || ''
}

export function haptic(style: 'light' | 'medium' | 'heavy' = 'light'): void {
  try { tg?.HapticFeedback?.impactOccurred(style) } catch { /* noop */ }
}

export function notify(type: 'error' | 'success' | 'warning'): void {
  try { tg?.HapticFeedback?.notificationOccurred(type) } catch { /* noop */ }
}

// Native Telegram confirm dialog; falls back to the browser confirm outside Telegram.
export function confirmDialog(message: string): Promise<boolean> {
  return new Promise((resolve) => {
    if (tg?.showConfirm) tg.showConfirm(message, (ok) => resolve(ok))
    else resolve(window.confirm(message))
  })
}

export function callPhone(phone: string): void {
  const url = `tel:${phone}`
  if (tg) tg.openLink(url)
  else window.location.href = url
}

// Opens Telegram's "send to…" picker so the rider can forward ride details to
// family. Outside Telegram (dev) falls back to the Web Share sheet, then clipboard.
export function shareText(text: string): void {
  if (tg) {
    tg.openTelegramLink(`https://t.me/share/url?url=&text=${encodeURIComponent(text)}`)
    return
  }
  if (navigator.share) { navigator.share({ text }).catch(() => { /* cancelled */ }); return }
  try { navigator.clipboard.writeText(text) } catch { /* noop */ }
}

export const backButton = {
  show(cb: () => void) {
    if (!tg) return
    tg.BackButton.onClick(cb)
    tg.BackButton.show()
  },
  hide(cb: () => void) {
    if (!tg) return
    tg.BackButton.offClick(cb)
    tg.BackButton.hide()
  },
}
