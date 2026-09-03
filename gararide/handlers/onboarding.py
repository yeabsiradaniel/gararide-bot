"""Three-tap registration: /start, share contact, done (UX spec section 10)."""
from __future__ import annotations

import logging

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CommandHandler, ContextTypes, MessageHandler, filters)

from .. import strings_am as S
from ..users import (NotAllowlisted, get_user, lookup_allowlist, reconcile_role,
                     register, register_rider)
from .launch import show_launch

log = logging.getLogger(__name__)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = context.bot_data["conn"]
    user = get_user(conn, update.effective_user.id)
    if user is not None:
        # A rider who has since been desk-verified as a driver gets promoted here.
        reconcile_role(conn, update.effective_user.id)
        await show_launch(update, context)
        return

    arg = (context.args or ["rdr"])[0]
    context.user_data["signup_role"] = "driver" if arg.startswith("drv") else "rider"
    text = S.WELCOME_DRIVER if arg.startswith("drv") else S.WELCOME_RIDER
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton(S.SHARE_CONTACT, request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(text, reply_markup=keyboard)


async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = context.bot_data["conn"]
    contact = update.message.contact
    if contact.user_id != update.effective_user.id:
        await update.message.reply_text(S.NOT_ALLOWLISTED,
                                        reply_markup=ReplyKeyboardRemove())
        return
    # The allowlist is authoritative for drivers: a desk-verified number becomes
    # a driver regardless of which link or command was used. Everyone else
    # self-registers as a rider (no desk check, no tower).
    if lookup_allowlist(conn, contact.phone_number) is not None:
        try:
            register(conn, telegram_id=update.effective_user.id,
                     phone=contact.phone_number)
        except NotAllowlisted:  # the driver slot is already claimed by another account
            await update.message.reply_text(S.NOT_ALLOWLISTED,
                                            reply_markup=ReplyKeyboardRemove())
            return
    else:
        register_rider(conn, telegram_id=update.effective_user.id,
                       phone=contact.phone_number,
                       full_name=update.effective_user.full_name)
    await update.message.reply_text(S.REGISTERED, reply_markup=ReplyKeyboardRemove())
    await show_launch(update, context)


def handlers() -> list:
    return [
        CommandHandler("start", cmd_start),
        MessageHandler(filters.CONTACT, on_contact),
    ]
