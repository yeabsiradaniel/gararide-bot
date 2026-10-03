"""Inline-button callbacks — let riders and drivers act from the chat without
opening the Mini App. Every callback verifies the acting user owns the thing.

callback_data shape: "<action>:<arg>[:<arg>]". Keep each under 64 bytes.
"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from ..api.push import kb
from ..bookings import (BookingClosed, NotOffered, TripFull, book,
                        bookings_for_trip, cancel_booking, mark_no_show, mark_paid)
from ..copy import strings as copy
from ..driver_routes import get_route, post_route_tomorrow, tomorrow_departure
from ..fmt import fmt_when
from ..places import place_by_id
from ..ratings import rate
from ..trips import (cancel_trip, dwell_expired, get_trip, mark_arrived,
                     mark_on_way, post_block_reason)
from ..users import get_user
from .. import waitlist
from datetime import datetime

log = logging.getLogger(__name__)


def _pname(conn, pid: int, lang: str | None) -> str:
    p = place_by_id(conn, pid)
    return p["name_en"] if lang == "en" else p["name_am"]


def _owns_trip(trip, uid: int) -> bool:
    return trip is not None and trip["driver_id"] == uid


def _booking(conn, bid: int):
    b = conn.execute("SELECT * FROM bookings WHERE id = ?", (bid,)).fetchone()
    return b, (get_trip(conn, b["trip_id"]) if b else None)


async def _send(bot, chat_id: int, text: str, markup=None) -> None:
    try:
        await bot.send_message(chat_id, text, reply_markup=markup)
    except Exception as exc:  # noqa
        log.warning("actions: send to %s failed: %s", chat_id, exc)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if q is None:
        return
    conn = context.bot_data["conn"]
    uid = q.from_user.id
    user = get_user(conn, uid)
    if user is None:
        await q.answer()
        return
    S = copy(user["lang"])
    bot = context.application.bot
    try:
        await _dispatch(q, bot, conn, uid, user, S)
    except Exception as exc:  # a bad tap must never crash the bot
        log.warning("callback %r failed: %s", q.data, exc)
        try:
            await q.answer()
        except Exception:  # noqa
            pass


async def _dispatch(q, bot, conn, uid, user, S) -> None:
    parts = (q.data or "").split(":")
    action = parts[0]

    # ---- driver: on my way ------------------------------------------------
    if action == "otw":
        tid = int(parts[1])
        if not _owns_trip(get_trip(conn, tid), uid):
            return await q.answer(S.CB_NOT_YOURS, show_alert=True)
        await q.edit_message_reply_markup(reply_markup=kb([[
            (S.ETA_5, f"otwset:{tid}:5"), (S.ETA_10, f"otwset:{tid}:10"),
            (S.ETA_15, f"otwset:{tid}:15")]]))
        return await q.answer(S.CB_PICK_ETA)

    if action == "otwset":
        tid, mins = int(parts[1]), int(parts[2])
        if not _owns_trip(get_trip(conn, tid), uid):
            return await q.answer(S.CB_NOT_YOURS, show_alert=True)
        mark_on_way(conn, tid, mins)
        for b in bookings_for_trip(conn, tid):
            r = get_user(conn, b["rider_id"])
            if r:
                await _send(bot, r["telegram_id"], copy(r["lang"]).ON_THE_WAY.format(mins=mins),
                            kb([[(copy(r["lang"]).BTN_IM_COMING, f"imcoming:{tid}")]]))
        await q.edit_message_reply_markup(reply_markup=kb([[(S.BTN_ARRIVED, f"arrived:{tid}")]]))
        return await q.answer(S.CB_ON_WAY)

    # ---- driver: arrived -> boarding + per-passenger controls -------------
    if action == "arrived":
        tid = int(parts[1])
        trip = get_trip(conn, tid)
        if not _owns_trip(trip, uid):
            return await q.answer(S.CB_NOT_YOURS, show_alert=True)
        mark_arrived(conn, tid)
        from ..config import CONFIG
        for b in bookings_for_trip(conn, tid):
            r = get_user(conn, b["rider_id"])
            if r:
                await _send(bot, r["telegram_id"],
                            copy(r["lang"]).BOARDING_OPEN.format(mins=CONFIG.dwell_minutes))
            await _send(bot, uid, S.DRIVER_PAX.format(
                name=(r["full_name"] if r else "?"),
                dest=_pname(conn, b["to_place_id"], user["lang"])),
                kb([[(S.BTN_PAID.format(name=(r["full_name"] if r else "?")), f"paid:{b['id']}"),
                     (S.BTN_NOSHOW.format(name=(r["full_name"] if r else "?")), f"noshow:{b['id']}")]]))
        await q.edit_message_reply_markup(reply_markup=None)
        return await q.answer(S.CB_ARRIVED)

    if action == "paid":
        b, trip = _booking(conn, int(parts[1]))
        if trip is None or trip["driver_id"] != uid:
            return await q.answer(S.CB_NOT_YOURS, show_alert=True)
        mark_paid(conn, b["id"])
        await q.edit_message_reply_markup(reply_markup=None)
        return await q.answer(S.CB_PAID)

    if action == "noshow":
        b, trip = _booking(conn, int(parts[1]))
        if trip is None or trip["driver_id"] != uid:
            return await q.answer(S.CB_NOT_YOURS, show_alert=True)
        if not dwell_expired(trip):
            return await q.answer(S.CB_NOSHOW_EARLY, show_alert=True)
        mark_no_show(conn, b["id"])
        await q.edit_message_reply_markup(reply_markup=None)
        return await q.answer(S.CB_NOSHOW)

    # ---- rider: cancel seat ----------------------------------------------
    if action == "cancelbk":
        b, trip = _booking(conn, int(parts[1]))
        if b is None or b["rider_id"] != uid:
            return await q.answer(S.CB_NOT_YOURS, show_alert=True)
        if b["status"] == "booked":
            cancel_booking(conn, b["id"])
            await _after_cancel(bot, conn, b, trip)
        await q.edit_message_reply_markup(reply_markup=None)
        return await q.answer(S.CB_CANCELLED)

    # ---- rider: rate ------------------------------------------------------
    if action == "rate":
        b, trip = _booking(conn, int(parts[2]))
        if b is None or b["rider_id"] != uid or b["status"] != "completed":
            return await q.answer(S.CB_NOT_YOURS, show_alert=True)
        rate(conn, booking_id=b["id"], rater_id=uid, ratee_id=trip["driver_id"],
             value=1 if parts[1] == "up" else -1)
        await q.edit_message_reply_markup(reply_markup=None)
        return await q.answer(S.CB_RATED)

    # ---- driver: post today's usual run ----------------------------------
    if action == "postroute":
        r = get_route(conn, int(parts[1]))
        if r is None or r["driver_id"] != uid:
            return await q.answer(S.CB_NOT_YOURS, show_alert=True)
        depart = tomorrow_departure(r["depart_time"])
        if post_block_reason(depart):
            return await q.answer(S.CB_LOCKED, show_alert=True)
        dupe = conn.execute(
            "SELECT 1 FROM trips WHERE driver_id=? AND dest_place_id=? AND depart_at=?"
            "   AND status='open'",
            (uid, r["dest_place_id"], depart.isoformat(timespec="seconds"))).fetchone()
        if dupe:
            return await q.answer(S.CB_POSTED_ALREADY, show_alert=True)
        post_route_tomorrow(conn, r)
        await q.edit_message_reply_markup(reply_markup=None)
        return await q.answer(S.CB_POSTED)

    # ---- rider: waitlist join / grab a freed seat ------------------------
    if action == "waitlist":
        tid, pid = int(parts[1]), int(parts[2])
        waitlist.join(conn, tid, uid, pid)
        await q.edit_message_reply_markup(reply_markup=None)
        return await q.answer(S.CB_WAITLISTED)

    if action == "wlbook":
        tid, pid = int(parts[1]), int(parts[2])
        try:
            book(conn, trip_id=tid, rider_id=uid, to_place_id=pid)
        except (BookingClosed, TripFull, NotOffered):
            return await q.answer(S.CB_SEAT_GONE, show_alert=True)
        waitlist.remove(conn, tid, uid)
        trip = get_trip(conn, tid)
        driver = get_user(conn, trip["driver_id"]) if trip else None
        if driver:
            await _send(bot, driver["telegram_id"], copy(driver["lang"]).SEAT_BOOKED.format(
                name=user["full_name"], dest=_pname(conn, pid, driver["lang"])))
        await q.edit_message_reply_markup(reply_markup=None)
        return await q.answer(S.CB_DONE)

    # ---- driver: evening confirm -----------------------------------------
    if action == "evening":
        tid = int(parts[2])
        trip = get_trip(conn, tid)
        if not _owns_trip(trip, uid):
            return await q.answer(S.CB_NOT_YOURS, show_alert=True)
        if parts[1] == "cancel":
            await _notify_trip_cancelled(bot, conn, tid)
            cancel_trip(conn, tid)
            await q.edit_message_reply_markup(reply_markup=None)
            return await q.answer(S.CB_TRIP_CANCELLED)
        await q.edit_message_reply_markup(reply_markup=None)
        return await q.answer(S.CB_DONE)

    # ---- rider: I'm on my way to pickup ----------------------------------
    if action == "imcoming":
        tid = int(parts[1])
        trip = get_trip(conn, tid)
        mine = conn.execute(
            "SELECT 1 FROM bookings WHERE trip_id=? AND rider_id=? AND status='booked'",
            (tid, uid)).fetchone()
        if trip is None or mine is None:
            return await q.answer(S.CB_NOT_YOURS, show_alert=True)
        driver = get_user(conn, trip["driver_id"])
        if driver:
            await _send(bot, driver["telegram_id"],
                        copy(driver["lang"]).RIDER_COMING.format(name=user["full_name"]))
        return await q.answer(S.CB_RIDER_COMING)

    await q.answer()


async def _after_cancel(bot, conn, booking, trip) -> None:
    """Tell the driver a seat went, and ping anyone waiting that it's free."""
    if trip is None:
        return
    driver = get_user(conn, trip["driver_id"])
    if driver:
        await _send(bot, driver["telegram_id"], copy(driver["lang"]).BOOKING_CANCELLED.format(
            name="", dest=_pname(conn, booking["to_place_id"], driver["lang"])))
    when = fmt_when(datetime.fromisoformat(trip["depart_at"]))
    for w in waitlist.for_trip(conn, trip["id"]):
        r = get_user(conn, w["rider_id"])
        if r:
            await _send(bot, r["telegram_id"], copy(r["lang"]).SEAT_FREED.format(
                dest=_pname(conn, w["to_place_id"], r["lang"]), when=when),
                kb([[(copy(r["lang"]).BTN_BOOK_NOW, f"wlbook:{trip['id']}:{w['to_place_id']}")]]))


async def _notify_trip_cancelled(bot, conn, tid: int) -> None:
    trip = get_trip(conn, tid)
    when = fmt_when(datetime.fromisoformat(trip["depart_at"])) if trip else ""
    for b in bookings_for_trip(conn, tid):
        r = get_user(conn, b["rider_id"])
        if r:
            await _send(bot, r["telegram_id"], copy(r["lang"]).TRIP_CANCELLED.format(
                dest=_pname(conn, b["to_place_id"], r["lang"]), when=when))


def handlers() -> list:
    return [CallbackQueryHandler(on_callback)]
