"""ASGI entrypoint — one process serves the Mini App API + static frontend and
runs the Telegram bot (registration + notifications) on the same event loop.

    uvicorn gararide.server:app

The bot only starts when BOT_TOKEN is set, so the app still boots (and /healthz
answers) without one. Reuses a single SQLite connection across both.
"""
from __future__ import annotations

import contextlib
import logging
import os

from telegram import Update

from .api.app import create_app
from .bot import build_app
from .db import connect, init_schema
from .places import seed_corridor

log = logging.getLogger("gararide.server")

conn = connect(os.environ.get("GARARIDE_DB", "gararide.sqlite3"))
init_schema(conn)
seed_corridor(conn, os.environ.get("GARARIDE_CORRIDOR", "seed/corridor_ayat49.csv"))

_admins = frozenset(int(x) for x in os.environ.get("GARARIDE_ADMINS", "").split(",")
                    if x.strip())
_bot_token = os.environ.get("BOT_TOKEN", "")
# The API always needs BOT_TOKEN to validate initData. Running the bot poller in
# this process is opt-in (RUN_BOT=1) — for local testing you can run the bot
# standalone (`python -m gararide.bot`) instead.
_run_bot = os.environ.get("RUN_BOT", "").strip().lower() not in ("", "0", "false", "no")


@contextlib.asynccontextmanager
async def _lifespan(app):
    bot = None
    if _bot_token and _run_bot:
        try:
            bot = build_app(_bot_token, conn=conn)
            await bot.initialize()
            await bot.start()
            await bot.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            log.info("bot polling started")
        except Exception as exc:  # a bot hiccup must not take down the Mini App
            log.warning("bot failed to start, serving API only: %s", exc)
            bot = None
    yield
    if bot is not None:
        try:
            await bot.updater.stop()
            await bot.stop()
            await bot.shutdown()
        except Exception:  # noqa
            pass


app = create_app(conn, _bot_token, admin_ids=_admins, lifespan=_lifespan)

# Serve the built Mini App (Plan 2 produces frontend/dist). Mounted last so the
# API routes above take precedence.
if os.path.isdir("frontend/dist"):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="app")
