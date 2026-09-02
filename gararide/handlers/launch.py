"""The Mini App launcher — the bot's only interactive job after registration.

Everything the user does happens in the Mini App (opened by this button).
The bot otherwise just sends push notifications (trip cards, reminders).
"""
from __future__ import annotations

import os

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update,
                      WebAppInfo)
from telegram.ext import CommandHandler, ContextTypes

from .. import strings_am as S


def _webapp_url() -> str:
    # Telegram requires an https URL for a WebApp button; a placeholder keeps the
    # bot runnable before the Mini App is deployed (Plan 2).
    return os.environ.get("WEBAPP_URL", "https://example.com/app")


async def show_launch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton(S.OPEN_APP, web_app=WebAppInfo(url=_webapp_url()))]])
    message = update.message or (
        update.callback_query.message if update.callback_query else None)
    if message is not None:
        await message.reply_text(S.OPEN_APP_PROMPT, reply_markup=markup)


async def cmd_app(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_launch(update, context)


def handlers() -> list:
    return [CommandHandler("app", cmd_app)]
