# Gara Ride — V2 build backlog

Status: **scope agreed, NOT sequenced, NOT built.** Founder has more to add first.
Then we sequence into a build order and knock out one at a time — local + dev-bot
tested each, per usual. Ratings are ADMIN-ONLY everywhere — never shown to users.

---

## A. Trust & safety
- Driver photo: captured at DESK registration, REQUIRED for a driver to be active.
  **DEFERRED until cPanel hosting is live (decided 2026-10-01).** No Cloudinary —
  cPanel gives real file storage + MySQL, so photos become trivial then (store file,
  serve off own domain). Turso is temporary; don't build throwaway photo plumbing now.
  NOTE: cPanel shared hosting likely can't run our long-lived Python bot process —
  realistic shape is app stays on Render, cPanel used for photo files (+ maybe DB).
  Confirm what the cPanel plan allows once it's live.
- Rider photo: optional, auto-pulled from Telegram. (Also deferred with driver photo.)
- "Desk-verified ✓" badge shown to riders on the driver.
- Car COLOR: new field, captured at desk; shown with model + plate. No car photo.
- Ratings: 👍/👎 after each ride, ADMIN-ONLY (never shown to either party).
- Report to admin (with a reason) — NEW, alongside the existing silent block (block stays).
- Safety button: "Share ride details" → forwardable Telegram message (driver, car model+color+plate, route, time). No GPS.

## B. Rider side
- History tab: past rides (completed + cancelled); tap → receipt (date, route, driver, fare, paid/no-show).
- Driver status pings (no GPS): "On my way" → rider notified + countdown to reach pickup; "I've arrived" boarding countdown (already built).
- Pickup: STATIC Telegram location pin for Bay Alpha + landmark text. NEED coords from
  founder (one-time). This is a static map dot, NOT live tracking.
- **Live driver-on-the-way tracker (NEW item, 2026-10-01).** Telegram live location,
  FREE (no API cost), MEDIUM effort. Driver-initiated: driver manually taps "Share
  Live Location" in the Telegram chat each trip (a Mini App button can't auto-start
  continuous background sharing). Bot receives the moving pin + relays updates to
  booked riders. Friction: driver habit + battery. Separate from the static pin above.
- Pre-book: rider sees driver photo/name/verified; phone revealed only AFTER booking.

## C. Driver side
- Edit a posted trip anytime; booked riders get notified of changes.
- Passenger card: photo + name + tower (NO rating).
- Per-trip earnings breakdown (rides + birr, from the paid taps).
- (Car/plate/seats stay desk-only — not editable by driver. By design.)

## D. Both / general
- Profile screen: view all; editable = photo (rider) + language + women-only.
- One-time terms/consent acknowledge at sign-up (rules + data use), stored.
- Driver no-show: rider taps "driver didn't show" → flags admin, counts against driver.
- In-app "Contact support" → messages admin/support account.
- First-open role-specific "how it works" (default build).
- Admin broadcast to all / drivers / riders (default build).

## E. Founder additions
- **UI/UX redesign (FOUNDATIONAL — do first).** Current UI is lifeless. Full
  visual redesign driven by the Impeccable `frontend-design` skill, anchored on
  the company brand (green/sunset palette + logo). Establish the new design
  system first, then build every A–D feature screen in the NEW look — never the
  old one. Approach: refresh the design system + redesign a couple of anchor
  screens as a proof, get founder's eyes on the vibe, then roll it across all
  screens. Founder delegates aesthetic direction ("go crazy, I trust your design
  + Impeccable").

---

## F. Robustness & live data (added 2026-09-30)
- **Fix the overbooking race.** `bookings.book()` does check-then-insert (read
  seats_left, then insert) without a transaction, so two riders tapping "Take a
  seat" for the last seat in the same instant can BOTH succeed → trip overbooks by
  one. Wrap the check + insert in an atomic transaction (conditional insert) so
  only one wins the last seat. Found during edge-case testing.
- **Full edge-case testing pass of the whole app.** We found the race above by
  poking one flow; there are likely more (other races, stale state, error paths,
  empty states, permission checks, double-taps, expiry boundaries, concurrency).
  Do a deliberate sweep, not ad-hoc.
- **Make some screens live (not static snapshots).** Right now the search-results
  list is a one-time snapshot — a rider can tap through several cars and only find
  out at "Take a seat" that a seat filled. That's work we're pushing onto the user.
  Decide which screens should refresh live (results list is the prime one; also
  driver's "My trips" passenger count, requests-near) and how (poll on focus, or
  re-fetch on a short interval / on return). Not everything needs it — pick the
  ones where stale data wastes the user's time.
- **Post-fail bounce.** When a booking fails because the seat filled, send the
  rider back to a refreshed list instead of leaving them on a dead preview.
- **One active booking per overlapping time (no double-booking a time slot).**
  A rider can't be in two cars at once, so they shouldn't be able to hold two
  bookings whose trips overlap / are near the same time. Rule: while a booking is
  active (not cancelled/completed), block booking another trip that crosses that
  time window. (Already done, narrower: a trip you've booked is hidden from search
  — 2026-10-01. This is the broader time-conflict guard.) Part of the edge-case
  sweep; founder flagged more cases like this to shake out here.

## Open micro-questions (confirm before building those bits)
- "On my way" countdown length: driver picks ~X min out, or a fixed default?
- Bay Alpha coordinates for the location pin.

## Pre-launch (ops, not features)
- Turso migration: db.py adapter, Turso only when TURSO_DATABASE_URL set (creds in .turso.env). Pre-deploy.
- Load real driver roster (with photos + car color).
- Confirm corridor stops/fares vs the real route (seed/corridor_ayat49.csv).
- Prod bot: BotFather menu button + ?start=drv / ?start=rdr links.
- Founder full walkthrough on dev bot + prod dry run before launch.

## Done session 2 (2026-10-01, committed, NOT pushed)
All buildable A–D items are now built + unit-tested:
- A: desk-verified badge · car colour · safety "share ride details" · report to
  admin · ratings (👍/👎 admin-only). (Photos deferred to cPanel.)
- B: history/receipts · boarding countdown · pre-book preview · "on my way" +
  rider countdown · hide already-booked trips from search. (Pickup pin needs
  coords; live tracker is its own backlog item.)
- C: edit a posted trip (time/seats/note) · passenger card (name+tower) ·
  per-trip earnings. (Car/plate/capacity desk-only by design.)
- D: profile screen · consent at sign-up · driver no-show (rider taps) · contact
  support · first-open walkthrough · admin broadcast.
What's LEFT (all blocked/backlog): photos (cPanel), pickup pin coords, live
driver tracker, and everything in section F (robustness sweep).

## Already done this session (committed, NOT pushed)
Language toggle · notifications · lifecycle/expiry · reminder dedupe · guards/auth ·
booking cutoff · cancelled-ride history · 4-min boarding countdown · Addis timezone fix.
