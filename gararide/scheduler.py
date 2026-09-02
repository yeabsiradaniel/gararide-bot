"""Timed messages.

20:15 the night before: the Trip Card. T-30: a reminder either side can act on.
The 4-minute dwell countdown is what stops the boarding rule from becoming an
argument between two neighbours (UX spec section 21).
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, time, timedelta

from telegram.ext import Application

from .config import CONFIG
from .notify import trip_card
from .requests import expire_stale
from .trips import get_trip

log = logging.getLogger(__name__)


def _booked_between(conn: sqlite3.Connection, start: datetime,
                    end: datetime) -> list[int]:
    rows = conn.execute(
        "SELECT b.id FROM bookings b JOIN trips t ON t.id = b.trip_id"
        " WHERE b.status = 'booked' AND t.status = 'open'"
        "   AND t.depart_at >= ? AND t.depart_at <= ?",
        (start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")),
    ).fetchall()
    return [r["id"] for r in rows]


def due_reminders(conn: sqlite3.Connection, now: datetime) -> list[int]:
    return _booked_between(
        conn, now, now + timedelta(minutes=CONFIG.reminder_minutes_before))


def due_confirmations(conn: sqlite3.Connection, now: datetime) -> list[int]:
    tomorrow = (now + timedelta(days=1)).date()
    return _booked_between(
        conn,
        datetime.combine(tomorrow, time.min),
        datetime.combine(tomorrow, time.max),
    )


async def _send(app: Application, conn: sqlite3.Connection, booking_id: int) -> None:
    booking = conn.execute("SELECT * FROM bookings WHERE id = ?",
                           (booking_id,)).fetchone()
    trip = get_trip(conn, booking["trip_id"])
    for chat_id, role in ((booking["rider_id"], "rider"),
                          (trip["driver_id"], "driver")):
        try:
            await app.bot.send_message(chat_id, trip_card(conn, booking_id, role))
        except Exception as exc:
            log.warning("scheduled message to %s failed: %s", chat_id, exc)


async def job_evening_confirm(context) -> None:
    conn = context.bot_data["conn"]
    expire_stale(conn)
    for booking_id in due_confirmations(conn, datetime.now()):
        await _send(context.application, conn, booking_id)


async def job_reminder(context) -> None:
    conn = context.bot_data["conn"]
    for booking_id in due_reminders(conn, datetime.now()):
        await _send(context.application, conn, booking_id)


def register_jobs(app: Application) -> None:
    app.job_queue.run_daily(job_evening_confirm, time(hour=20, minute=15))
    app.job_queue.run_repeating(job_reminder, interval=300, first=60)
