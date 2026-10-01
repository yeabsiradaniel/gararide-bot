# Gara Ride — open discussion (not a plan / not a todo)

Running notes from the 2026-10-01 review. These are things we're still TALKING
about, not committed work. Nothing here is scheduled.

## Where we actually are
Features A–D are built + unit-tested (happy path). The app is NOT production
ready. What's built proves the flows; what's missing is the hard part: trust,
robustness, real-world behaviour, ops. Beta is intended for ONE community
(limited users), which lowers — but doesn't remove — the bar on some of this.

## Biggest gap: robustness & real-world (was section F, under-rated)
- This is probably the MOST important work, not a tail item. It's the difference
  between a demo and something real people move through. Promote it.
- Known: the overbooking race (check-then-insert not atomic).
- Stale vs live screens (results list is a snapshot; more).
- Full edge-case sweep: double-taps, expiry boundaries, concurrency, error/empty
  states, permission checks, every user flow walked deliberately.
- **Spam / abuse / server load (NEW):** users can hammer actions (reports,
  support messages, bookings, broadcasts, on-my-way). Need rate limiting,
  dedupe, and abuse controls — both UX and server protection.

## Notification audit
Who gets notified on what is currently ad-hoc (added per feature). Needs a
deliberate map: every event → who's told, in what language, via what channel,
and when NOT to notify (avoid spam). Do this as its own pass.

## Trust (beta-calibrated, don't over-engineer)
- This is a single trusted community beta, so some safety is "socially
  understood" and we won't gold-plate identity now.
- Still thin: strangers share a car with just a name; riders have no photo and
  no location/tower. Revisit for a wider launch, not for this beta.

## Pickup pin + live location ("I'm coming") — tie to driver actions
- Static pickup pin: surface it when the driver taps **"I've arrived"** (and/or
  at booking). Needs Bay Alpha coords.
- Live location: pair with the **"on my way"** flow — driver shares live
  location, rider watches it approach. Free via Telegram, driver-initiated.
- Both carry real edge cases (stale/last-known location, driver forgets to share
  or to stop sharing, permission denied, battery, privacy window). Treat as its
  own hardening effort, not a quick add.

## Driver edit restrictions (confirm)
Edit-a-trip only exposes time / offered-seats / note. Desk-registration fields
(car, plate, capacity, tower) stay locked by design. Confirm nothing desk-set
leaks into an editable field anywhere.

## Payments / pricing
- No reconciliation/dispute flow for now — fine for beta (money never touches
  the platform; "paid" is a driver tap).
- SOON: tune per-distance fares from real-world data (the corridor fares are
  placeholders).

## Polish
- No AI-tell em dashes in user copy (done 2026-10-01). Keep it that way.
- Replace native `alert()` popups (they show the tunnel/host domain) with
  Telegram-native popups or inline toasts.
- Empty + error states on every screen.

## Legal
Consent is one tap today. Needs a real terms/data-use document behind it before
anything beyond a trusted beta.

## Ops before a real launch (from the plan's pre-launch section)
Turso wiring, real driver roster + photos, Bay Alpha coords, corridor/fares
confirmation, BotFather menu button + deep links, monitoring/logging/backups.
