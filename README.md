# ጋራ ራይድ — GaraRIde Demo Bot

Demo Telegram bot + mini app for the GaraRIde pitch: **drivers post their commute
with free seats, riders pick a ride and split the fare.** Amharic-first UI,
seeded with fake drivers on the Megenagna → Bole corridor.

> Demo only — no real payments, no real drivers, data resets on restart.

## What's inside

| File | What it does |
|------|--------------|
| `bot.py` | The bot (driver/rider flows) + serves the mini app and its JSON API |
| `data.py` | Corridor stops, segment pricing, persistent store (JSON file), seed drivers |
| `strings.py` | All Amharic bot text in one place |
| `webapp/` | The Telegram mini app (HTML/CSS/JS, no build step) |
| `gararide_data.json` | Created at runtime — rides/bookings survive restarts. Delete to reset the demo. |

## Features

- **Segment matching** — a rider going Hayahulet → Bole Medhanialem matches any driver passing through those stops, and pays only for their segment.
- **Driver flow** — post route, departure (incl. tomorrow morning), seats, car/plate; fare auto-computed.
- **Notifications** — drivers get a message when someone books or cancels; riders get notified if a driver cancels a ride.
- **My bookings / My rides** — riders can cancel a booking, drivers can cancel a ride (from the bot home or the mini app).
- **Mini app** — stop-to-stop filter, live seat counts, booking codes, refresh, offline fallback demo data.
- **`/stats`** — rides posted, bookings, seats filled, total rider savings (your pitch numbers).

## 1. Install

```bash
pip install -r requirements.txt
```

## 2. Preview the mini app right now (no bot needed)

```bash
python bot.py
```

Then open **http://localhost:8080** in your browser. Without a bot token it
only runs the web server, which is handy for UI work.

## 3. Create the bot (when ready)

1. In Telegram, talk to **@BotFather** → `/newbot` → follow the steps → copy the token.
2. Set the token and run:

```bash
# Windows cmd
set BOT_TOKEN=123456:ABC-your-token && python bot.py

# PowerShell
$env:BOT_TOKEN="123456:ABC-your-token"; python bot.py
```

3. Open your bot in Telegram and press **/start**.

## 4. Make the mini app button work (HTTPS)

Telegram only opens mini apps from HTTPS URLs. For the pitch, run the bot on
your laptop and expose it with a tunnel:

```bash
ngrok http 8080
```

Copy the `https://....ngrok.io` URL, then restart the bot with:

```bash
# Windows cmd
set BOT_TOKEN=... && set WEBAPP_URL=https://your-subdomain.ngrok.io && python bot.py
```

The "📱 ሚኒ አፑን ክፈት" button in `/start` now opens the live mini app.
(Tip: ngrok's free static domain keeps the URL stable between restarts.)

**Backup option:** put the `webapp/` folder on GitHub Pages and use that URL.
The mini app detects the API is missing and runs on baked-in demo data — it
can never fail on stage, it just won't share live state with the bot.

## Demo script (for the pitch)

1. `/start` → "🚙 መንገድ ልለጥፍ" — post a ride as a driver (route, time, seats; fare is auto-computed).
2. "🙋 መንገድ ልፈልግ" — as a rider, browse seeded drivers, open one, see the savings vs. going solo.
3. "✅ ቦታ ልያዝ" — booking code + Telebirr payment instruction (clearly marked as demo).
4. "📱 ሚኒ አፑን ክፈት" — same flow in the polished mini app; the ride posted in step 1 shows up live.

## Known demo shortcuts (fine for a pitch, not for production)

- `initData` from the mini app is not verified — anyone could call the API.
- In-memory storage: restart = fresh seed data.
- Payments are just instructions; nothing checks Telebirr.
