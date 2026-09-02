# Gara Ride Mini App — Frontend Plan (Plan 2 of 2)

> **For agentic workers:** the backend (Plan 1) is complete and tested. This plan builds the React Mini App that consumes it. UI is design-heavy and built with the Impeccable `frontend-design` skill + the brand tokens (`docs/brand.md`); screens are specified by responsibility, data, and interactions rather than pre-written JSX.

**Goal:** A polished Telegram Mini App (split driver/rider, Amharic-first) that lets verified neighbours find a seat or trust the person in it, talking to the Plan 1 API.

**Architecture:** Vite + React + TypeScript under `frontend/`. `@telegram-apps/sdk-react` for WebApp integration (theme, viewport, back button, main button). A typed API client sending `Authorization: tma <initData>`. Role from `GET /me` picks the home. Built to `frontend/dist`, served by `gararide/server.py`.

**Tech Stack:** Vite, React 18, TypeScript, `@telegram-apps/sdk-react`, a tiny fetch wrapper (no heavy state lib), CSS with custom properties from the brand.

## Global Constraints
- **Amharic-first copy** in one `strings.ts` (mirrors `gararide/strings_am.py`).
- **Price + both clocks on every trip view**; **tower shown for drivers only**.
- **Never an empty search result** — render near-misses + demand + post-request.
- **Brand:** primary `#0DA200`, secondary `#53C830`, accent `#9AEF61`, sunset `#FF7A45`, ink `#0B2E08`, surface `#EEFDE3`, gradient `#0DA200→#53C830→#9AEF61`. Light theme. Noto Sans Ethiopic + a warm grotesque. Impeccable anti-slop rules apply.
- **Every screen must help find a seat or trust the person in it** — else cut.
- Commit after each task.

## File structure
```
frontend/
  index.html, vite.config.ts, tsconfig.json, package.json
  src/
    main.tsx, App.tsx
    telegram.ts        WebApp init, initData, theme, back/main button helpers
    api.ts             typed client (auth header, all endpoints)
    strings.ts         Amharic copy
    fmt.ts             fmt_time (both clocks), fmt_money, fmt_person
    theme.css          brand tokens + base type/reset
    components/        Button, Card, TripLine, Field, Sheet, Spinner, EmptyState
    screens/
      Boot.tsx         GET /me -> route to home or register bounce
      DriverHome.tsx, PostTrip.tsx, MyTrips.tsx, RequestsNear.tsx
      RiderHome.tsx, FindRide.tsx, Results.tsx, TripCard.tsx, PostRequest.tsx
      MyBookings.tsx, WomenOnly.tsx, Saved.tsx
      Admin.tsx
```

## Tasks (build order)
1. **Scaffold + design system.** Vite React TS project; `theme.css` with brand tokens, type scale, base components (Button, Card, Field). Deliverable: `npm run build` produces `frontend/dist`; a styled "Boot" screen renders.
2. **Telegram + API plumbing.** `telegram.ts` (init WebApp, expand, theme, initData), `api.ts` (typed calls with `tma` auth), `fmt.ts`, `strings.ts`. `Boot` calls `GET /me` and routes by role (or shows the register bounce).
3. **Driver home + Post a trip.** Home tiles; the post flow: destination → intermediate drop-offs (destination shown fixed) → slot/time → free seats `1..car_seats` → note → confirm (per-stop fares, both clocks). Uses `/trips/{dest}/dropoff-options`, `POST /trips`.
4. **My trips + Requests near me.** `/trips/mine` (passenger list, Paid/No-show), `/requests/near`.
5. **Rider home + Find a ride + Results.** Home; search → results; the never-empty screen (near-misses, demand line, Post request, Notify me). `/trips/search`.
6. **Booking + Trip card + safety valve.** `POST /bookings` → trip card (driver name/tower/car/plate/phone, price, both clocks, Bay Alpha, Call via `openTelegramLink`/`tel:`), Cancel, "Not this driver" → `POST /blocks`.
7. **Requests, My bookings, Women-only, Saved/repeat + daily confirm.** `POST /requests`, `/bookings/mine`, `POST /me/women-only`, `/me/saved`. The daily-confirm entry (deferred from Plan 1) lands here as a simple "Riding tomorrow?" prompt on saved trips.
8. **Admin.** `/admin/ops`, `/admin/unmatched` for admin ids.
9. **Wire into server + build.** Confirm `gararide/server.py` serves `frontend/dist`; document the `npm run build` step in DEPLOY.md; manual test in Telegram against the test bot.

## Testing
Manual testing inside Telegram (via https tunnel) against the running backend, plus light component tests only where they earn their place. The backend's 111 tests already cover the logic.
