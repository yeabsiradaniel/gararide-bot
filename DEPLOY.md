# Deploying the Gara Ride Mini App

One Render **web service** runs everything: the FastAPI Mini App API, the static
frontend (once Plan 2 is built into `frontend/dist`), and the Telegram bot
(registration + notifications) on the same process. HTTPS is required by Telegram
for Mini Apps — Render provides it.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `BOT_TOKEN` | yes | From @BotFather. Also validates Mini App `initData`. |
| `WEBAPP_URL` | yes | The public https URL of this service (e.g. `https://gararide.onrender.com`). The bot's "Open Gara Ride" button and BotFather menu button point here. |
| `GARARIDE_ADMINS` | yes | Comma-separated Telegram user ids allowed to call `/admin/*`. |
| `GARARIDE_DB` | no | SQLite path. On Render use the mounted disk, e.g. `/var/data/gararide.sqlite3`. |
| `GARARIDE_CORRIDOR` | no | Stop-list CSV. Default `seed/corridor_ayat49.csv`. |

## Render setup (Docker)

The service builds from the repo's `Dockerfile` (a multi-stage build: Node
compiles the Mini App, then a Python image serves the API + static frontend and
runs the bot in one process). No dashboard build/start command is needed — the
container defines them. Health check: `/healthz`.

Reuse the existing instance:
1. Runtime must be **Docker** (Settings → the service reads `./Dockerfile`).
2. Set the env vars in the table above. `BOT_TOKEN` and `WEBAPP_URL` from the old
   demo carry over unchanged (same names). Add `GARARIDE_ADMINS` (your Telegram
   id) and keep `GARARIDE_DB` on the disk.
3. Attach a **1 GB persistent disk at `/var/data`** so the SQLite DB survives
   redeploys — without it every deploy wipes all users, trips and bookings.
4. Deploy. Each push to the connected branch rebuilds automatically.

`render.yaml` describes this exact service if you ever recreate it as a Blueprint.

## BotFather / Telegram setup

1. **Menu button → Mini App:** BotFather → `/setmenubutton` → choose the bot →
   set the URL to `WEBAPP_URL`. Now the chat's menu button opens the app.
2. **Registration deep links still work** and set the role greeting:
   - Driver desk standee: `https://t.me/<botname>?start=drv`
   - Rider lift-lobby standee: `https://t.me/<botname>?start=rdr`
   The number decides the actual role (allowlisted → driver; else self-register rider).

## Before launch

1. **Load the desk-verified driver roster.** Put the real drivers (with
   `car_seats`) in `seed/allowlist.csv`, then import it into the live DB — the bot
   no longer has an `/import` command, so run it once against the deployed DB:
   ```bash
   GARARIDE_DB=/var/data/gararide.sqlite3 python -c "from gararide.db import connect,init_schema; from gararide.users import import_allowlist; c=connect('/var/data/gararide.sqlite3'); init_schema(c); print('imported', import_allowlist(c,'seed/allowlist.csv'))"
   ```
   Riders self-register from the link — they are not in the roster.
2. Confirm the stop order and fares in `seed/corridor_ayat49.csv` against the real
   route (execution plan §9). Editing this CSV is the only change needed — no code
   touches fares.
3. **Back up the SQLite DB daily.** It holds every verified user, trip and booking.

## Local run

```powershell
pip install -r requirements.txt
$env:BOT_TOKEN="..."; $env:WEBAPP_URL="https://<your-ngrok-or-render>.app"; $env:GARARIDE_ADMINS="123456789"
uvicorn gararide.server:app --host 0.0.0.0 --port 8000
```
For local Mini App testing you need an https tunnel (e.g. ngrok) pointing at
port 8000, and set `WEBAPP_URL` to that tunnel URL.
