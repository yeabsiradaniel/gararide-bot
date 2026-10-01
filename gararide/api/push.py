"""Fire-and-forget Telegram pushes from the (sync) API endpoints.

The bot runs on the ASGI event loop; API handlers run in a threadpool. We hand
the coroutine to the loop and don't wait — a push must never slow down or fail a
request. When the bot isn't attached (tests, API-only mode) this is a no-op.
"""
from __future__ import annotations

import asyncio
import logging

log = logging.getLogger(__name__)


async def _send(tg, chat_id: int, text: str) -> None:
    try:
        await tg.send_message(chat_id, text)
    except Exception as exc:  # blocked the bot, deactivated, etc. — never fatal
        log.warning("push to %s failed: %s", chat_id, exc)


def notify(app, chat_id: int | None, text: str | None) -> None:
    tg = getattr(app.state, "tg", None)
    loop = getattr(app.state, "loop", None)
    if tg is None or loop is None or not chat_id or not text:
        return
    try:
        asyncio.run_coroutine_threadsafe(_send(tg, chat_id, text), loop)
    except Exception as exc:  # noqa
        log.warning("could not schedule push: %s", exc)
