"""Fire-and-forget Telegram pushes from the (sync) API endpoints.

The bot runs on the ASGI event loop; API handlers run in a threadpool. We hand
the coroutine to the loop and don't wait — a push must never slow down or fail a
request. When the bot isn't attached (tests, API-only mode) this is a no-op.

A push may carry inline buttons: rows of (label, data). `data` beginning with
"web:" opens the Mini App (web_app button) at WEBAPP_URL + the rest; anything
else is callback_data handled by gararide.handlers.actions.
"""
from __future__ import annotations

import asyncio
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

log = logging.getLogger(__name__)

Rows = list  # list[list[tuple[str, str]]]


def _webapp_url() -> str:
    return os.environ.get("WEBAPP_URL", "https://example.com/app")


def kb(buttons: Rows | None) -> InlineKeyboardMarkup | None:
    if not buttons:
        return None
    rows = []
    for row in buttons:
        cells = []
        for label, data in row:
            if data.startswith("web:"):
                cells.append(InlineKeyboardButton(
                    label, web_app=WebAppInfo(url=_webapp_url() + data[4:])))
            else:
                cells.append(InlineKeyboardButton(label, callback_data=data))
        rows.append(cells)
    return InlineKeyboardMarkup(rows)


async def _send(tg, chat_id: int, text: str, markup) -> None:
    try:
        await tg.send_message(chat_id, text, reply_markup=markup)
    except Exception as exc:  # blocked the bot, deactivated, etc. — never fatal
        log.warning("push to %s failed: %s", chat_id, exc)


def notify(app, chat_id: int | None, text: str | None, buttons: Rows | None = None) -> None:
    tg = getattr(app.state, "tg", None)
    loop = getattr(app.state, "loop", None)
    if tg is None or loop is None or not chat_id or not text:
        return
    markup = kb(buttons)
    try:
        asyncio.run_coroutine_threadsafe(_send(tg, chat_id, text, markup), loop)
    except Exception as exc:  # noqa
        log.warning("could not schedule push: %s", exc)
