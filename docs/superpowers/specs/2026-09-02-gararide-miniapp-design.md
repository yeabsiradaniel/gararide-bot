# Gara Ride Mini App — Design

**Date:** 2026-09-02
**Supersedes:** the Phase-1 bot-only scope in `2026-09-02-gararide-bot-rewrite.md` (that plan's *domain logic* is kept and reused; its inline-keyboard bot UI is retired).

---

## 0. The main goal (everything below serves this)

> **Your neighbour is already driving where you're going. Share the empty seat.**

Gara Ride connects verified neighbours who are already making a trip with people
going the same way. It is **not** a taxi, **not** a commuter shuttle, **not**
ride-hailing. Trust comes from the gated compound — desk-verified drivers and
"I know where you live" — not from ratings or surveillance.

The hard problem is **manufacturing matches in a thin market** (12 drivers): both
sides can post, one trip serves four destinations via segment matching, and a
search never shows an empty result.

**The test for every screen and feature:** *does it help someone find a seat, or
trust the person in it?* If neither, it is cut. This governs the whole build.

---

## 1. What changes and what stays

**Stays (reused as-is):** the entire tested domain core in `gararide/` — `config`,
`db`, `places`, `fares`, `users`, `trips`, `requests`, `bookings`, `matching`,
`blocks`, `fmt`, `strings_am`, plus `notify` and `scheduler`. 88 passing tests
remain the safety net. The corridor, fare ladder, segment matching, drop-off
rules, allowlist/self-register split, dual-clock formatting — all unchanged.

**Retired:** the interactive inline-keyboard bot UI (`handlers/driver.py`,
`handlers/rider.py`, `keyboards.py`, and the callback handlers in `handlers/home.py`).
Replaced by the Mini App.

**Slimmed:** the bot keeps three jobs only — (a) three-tap **registration**
(`request_contact`, allowlist vs self-register), (b) a **launcher** button that
opens the Mini App, (c) **push notifications** (trip cards, T-30 reminders, 20:00
confirm) via `notify`/`scheduler`, because those must work on a lock screen.

**New:** a FastAPI **API** over the domain core, and the **Mini App** web frontend.

---

## 2. Architecture

```
Telegram client
  ├─ Bot (python-telegram-bot)         → register (request_contact), launch button, notifications
  └─ Mini App (React WebView)          → all interactive screens
         │  HTTPS + Telegram initData (HMAC-validated → telegram_id)
         ▼
   FastAPI service  ──────────────►  gararide/ domain core (reused)  ──►  SQLite
   (JSON API; also serves the built static frontend)
```

- **Backend:** FastAPI. An `initData` auth dependency validates the Telegram
  WebApp signature against the bot token and resolves the caller's `telegram_id`;
  every endpoint receives an authenticated user. The domain functions are called
  exactly as the bot handlers called them — `conn` + typed args.
- **Frontend:** React + Vite + TypeScript, `@telegram-apps/sdk` for WebApp
  integration (theme, viewport, back button, `requestContact` fallback,
  `openTelegramLink` for the call button). Split driver/rider by the role returned
  from `GET /me`. Amharic-first copy from a shared strings module (mirrors
  `strings_am`).
- **Hosting:** one Render **web service** over HTTPS (Telegram requires HTTPS for
  Mini Apps). FastAPI serves the API and the built static assets. Reuses the
  existing Render instance + bot token. Resolves the earlier polling-vs-webservice
  problem — a Mini App backend *is* a web service.
- **Auth model:** registration (phone) happens in the **bot** (proven 3-tap flow).
  The Mini App reads identity from `initData`; if `GET /me` 404s (not registered),
  the app shows a "tap here to register" bounce back to the bot.

---

## 3. Domain changes (small, tested additions to the reused core)

These four come directly from pilot feedback and are the only logic changes:

1. **Seats from the car's capacity.** Add `car_seats INTEGER` to `allowlist` and
   `users`. The desk records the car's passenger capacity; the driver, when
   posting, chooses free seats `1..car_seats` (replaces the hardcoded 1–3).
2. **Exclude own trips from search.** `matching.find_trips` / `near_misses` skip
   trips where `driver_id == rider_id`. A driver using "I need a ride" never sees
   their own post.
3. **Drop-off list omits the destination.** A new read helper returns only the
   *intermediate* stops (origin < stop < destination) for the checklist UI; the
   destination is still stored as a drop-off automatically and shown as a fixed
   "→ destination" label, not a toggle.
4. **Saved / repeat trips.** Implement `saved.py` on the existing `saved_trips`
   table: offer to save after N identical trips (`CONFIG.save_prompt_threshold`),
   list saved trips as one-tap repeats on the home, and the 20:00 daily one-tap
   confirm (never auto-book).

Each change ships with pytest coverage before the UI consumes it.

---

## 4. Screens (built with the Impeccable `frontend-design` skill + brand)

Role decides the home; one app, two front doors.

**Shared:** splash/launch → `GET /me` → driver home or rider home (or register bounce).

**Driver**
- **Home:** primary *Post a trip*; *Requests near me* (with live count); *My trips*;
  a quiet *I need a ride today* switch to the rider side; saved-trip repeats.
- **Post a trip:** destination → drop-offs (**intermediate stops only**, common ones
  pre-ticked) → departure (3 fixed slots + a real time picker for other trips) →
  free seats (`1..car_seats`) → optional route note → **confirm** (fares per stop,
  both clocks).
- **My trips:** each trip with its passenger list (name · tower · → stop · fare ·
  call · `Paid`/`No-show`).
- **Requests near me:** open rider requests the driver could carry.
- **Trip card (driver view):** passenger list, total, `Call`, `I can't drive`.

**Rider**
- **Home:** primary *Find a ride*; *Post a request*; *My trips*; saved/repeat trips;
  women-only preference entry.
- **Find a ride:** destination → rough time → **results**, or the **never-empty**
  screen (near-misses, "N neighbours also want this", *Post my request*, *Notify me*).
- **Trip card (rider view):** driver name · tower · car · plate · **phone**, price,
  both clocks, *Bay Alpha*, `Call`, `Cancel`, **`Not this driver`** (safety valve).
- **Post a request; My bookings; Women-only preferences.**

**Both:** the **4-minute dwell countdown** as a live shared screen from T-3, plus a
bot push.

**Admin (restricted to `GARARIDE_ADMINS`):** today's trips / seats filled /
no-shows, and **unmatched searches as a dated driver-recruitment list**; allowlist import.

**Design language:** brand green primary with the sunset accent used sparingly;
light theme; Noto Sans Ethiopic + a warm grotesque; personality *trusted ·
neighbourly · effortless*; **price and both clocks on every trip view; tower shown
for drivers only; never an empty result.** Anti-slop rules from the Impeccable
skill apply (no generic card grids, no neon, purposeful motion only).

---

## 5. API surface (all require valid initData)

- **Identity/reference:** `GET /me`, `GET /places`, `GET /me/saved`.
- **Driver:** `POST /trips`, `GET /trips/mine`, `POST /trips/{id}/cancel`,
  `GET /trips/{id}/dropoff-options`, `GET /requests/near`,
  `POST /bookings/{id}/paid`, `POST /bookings/{id}/no-show`.
- **Rider:** `GET /trips/search`, `POST /bookings`, `POST /bookings/{id}/cancel`,
  `GET /bookings/mine`, `POST /requests`, `POST /blocks`, `POST /me/women-only`.
- **Saved:** `POST /me/saved`, `POST /me/saved/{id}/confirm`.
- **Admin:** `GET /admin/ops`, `GET /admin/unmatched`, `POST /admin/import`.

Every trip/search/booking response embeds the fare (price on every view).

---

## 6. Testing

- **Domain core:** existing 88 pytest tests stay green; add tests for the four
  §3 changes.
- **API:** pytest + FastAPI `TestClient` — endpoint behaviour and `initData` auth
  (valid, tampered, missing).
- **Frontend:** manual testing inside Telegram against the test bot; light
  component tests only where they earn their place.

---

## 7. Delivery order (for the plan that follows)

1. Domain changes (§3) + tests. 2. FastAPI skeleton + initData auth + `/me`,
`/places`. 3. Driver endpoints + screens. 4. Rider endpoints + screens (incl.
never-empty). 5. Trip card + safety valve + women-only. 6. Saved/repeat + daily
confirm + dwell countdown. 7. Admin. 8. Slim the bot to launcher + notifications;
retire the keyboard UI. 9. Render deployment (health, static serving, HTTPS).

---

## 8. Explicitly out of scope (Phase 2)

Open destinations beyond the Ayat 49 corridor, beacon mode, evening GPS
location-sharing, in-app payments, star ratings, live tracking, map route-drawing.
Unchanged from the spec's "not building" list.
