# Deploying GaraRIde for free — NO credit card required

Two verified options (checked: neither asks for a payment method on the free tier),
plus a zero-signup fallback.

---

## Option A — Hugging Face Spaces (recommended)

Free, always-on, HTTPS URL included, secrets UI, no card. Sign up with email or GitHub.

1. **Create an account:** https://huggingface.co/join
2. **Create a Space:** https://huggingface.co/new-space
   - Name: `gararide` (anything)
   - SDK: **Gradio** (free — Docker shows a paywall on some accounts, Gradio doesn't)
   - Hardware: **CPU basic (free)**
3. **Upload the code** (Space page → "Files" → "Add file" → upload, no git needed):
   - `app.py` (the entry point), `bot.py`, `data.py`, `strings.py`, `requirements.txt`
   - the whole `webapp/` folder
   - (`Dockerfile` is NOT needed for this path)
4. **Add secrets** (Space page → "Settings" → "Variables and secrets"):
   - `BOT_TOKEN` = your @BotFather token
   - `WEBAPP_URL` = `https://<your-username>-gararide.hf.space`
5. The Space builds and starts. Your mini app lives at the `hf.space` URL —
   open it to confirm, then check the bot with `/start` in Telegram.
6. **Keep it awake:** free Spaces sleep after ~48h without HTTP traffic.
   Create a free monitor at https://uptimerobot.com/ (no card) →
   "HTTP(s) monitor" → your Space URL, every 5 minutes. Done — it never sleeps.
7. **Point Telegram's menu button at the new URL** (one-time):
   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setChatMenuButton" \
     -H "Content-Type: application/json" \
     -d '{"menu_button":{"type":"web_app","text":"መንገዶች 🚗","web_app":{"url":"https://<your-username>-gararide.hf.space"}}}'
   ```

Notes:
- Make the Space **public** (default) or the mini app can't be reached.
- Data (`gararide_data.json`) resets if the Space restarts — fine for a demo.

---

## Option B — Render + UptimeRobot

No card on the free tier; 750 instance-hours/month = one service 24/7.
Caveat: sleeps after 15 min without traffic, so UptimeRobot is mandatory here.

1. **Sign up:** https://dashboard.render.com/register (GitHub login works)
2. Push the project to GitHub: https://github.com/new
3. Render dashboard → "New" → "Web Service" → connect the repo
   - Root directory: `gararide-bot`
   - Build command: `pip install -r requirements.txt`
   - Start command: `python bot.py`
   - Instance type: **Free**
4. Environment variables: `BOT_TOKEN`, and after first deploy
   `WEBAPP_URL` = your `https://<name>.onrender.com` URL (then redeploy).
5. **Keep awake:** https://uptimerobot.com/ → monitor your `.onrender.com` URL
   every 5 minutes.
6. Update the Telegram menu button as in Option A step 7.

Docs: https://render.com/docs/free

---

## Option C — Zero accounts: old Android phone + Termux

No card, no signup, no PC. Install Termux from F-Droid
(NOT the outdated Play Store build): https://f-droid.org/en/packages/com.termux/

```bash
pkg install python git
git clone <your-repo> && cd GaraRIde/gararide-bot
pip install -r requirements.txt
BOT_TOKEN="..." WEBAPP_URL="..." python bot.py
```

Keep it plugged in and tap "Acquire wakelock" in the Termux notification.
For a stable public mini-app URL, pair it with a free Cloudflare Tunnel:
https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/
