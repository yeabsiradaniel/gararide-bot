"""Wiring and entry point.

Run:  BOT_TOKEN=... python -m gararide.bot
"""
from __future__ import annotations

import asyncio
import logging
import os

from telegram import Update
from telegram.ext import Application

from .db import connect, init_schema
from .handlers import launch, onboarding
from .places import seed_corridor
from .scheduler import register_jobs

logging.basicConfig(level=logging.INFO,
                    format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("gararide")

DB_PATH = os.environ.get("GARARIDE_DB", "gararide.sqlite3")
CORRIDOR_CSV = os.environ.get("GARARIDE_CORRIDOR", "seed/corridor_ayat49.csv")


def build_app(token: str, conn=None) -> Application:
    if conn is None:
        conn = connect(DB_PATH)
        init_schema(conn)
        seed_corridor(conn, CORRIDOR_CSV)

    app = (Application.builder().token(token)
           .connect_timeout(30.0).read_timeout(30.0)
           .get_updates_read_timeout(50.0).build())
    app.bot_data["conn"] = conn
    for group in (onboarding, launch):
        for handler in group.handlers():
            app.add_handler(handler)
    register_jobs(app)
    return app


def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise SystemExit("BOT_TOKEN is not set")
    log.info("starting, db=%s", DB_PATH)
    # Python 3.14 no longer auto-creates an event loop in the main thread, but
    # python-telegram-bot's run_polling() calls asyncio.get_event_loop(). Give it
    # one explicitly so polling can start.
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    # Explicitly request every update type. Telegram remembers the last
    # allowed_updates set on this token, and a shared bot may have restricted it
    # to exclude callback_query (button presses) — this overrides that.
    build_app(token).run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
