"""Timed messages.

Reminders and confirmations now carry inline buttons so either side can act from
the chat: riders cancel a seat or say they're coming; drivers start the trip,
arrive, or confirm the evening before. Completed rides prompt a 👍/👎 rating.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, time, timedelta
from . import clock

from telegram.ext import Application

from .api.push import kb
from .config import CONFIG
from .copy import strings as copy
from .driver_routes import tomorrow_departure
from .fmt import fmt_when
from .notify import trip_card
from .places import place_by_id
from .requests import expire_stale
from .trips import expire_trips, get_trip
from .users import get_user

log = logging.getLogger(__name__)


def _pname(conn, pid, lang):
    p = place_by_id(conn, pid)
    return p["name_en"] if lang == "en" else p["name_am"]


def due_reminders(conn: sqlite3.Connection, now: datetime) -> list[int]:
    rows = conn.execute(
        "SELECT b.id FROM bookings b JOIN trips t ON t.id = b.trip_id"
        " WHERE b.status = 'booked' AND t.status = 'open' AND b.reminded = 0"
        "   AND t.depart_at >= ? AND t.depart_at <= ?",
        (now.isoformat(timespec="seconds"),
         (now + timedelta(minutes=CONFIG.reminder_minutes_before)).isoformat(timespec="seconds")),
    ).fetchall()
    return [r["id"] for r in rows]


def due_confirmations(conn: sqlite3.Connection, now: datetime) -> list[int]:
    tomorrow = (now + timedelta(days=1)).date()
    rows = conn.execute(
        "SELECT b.id FROM bookings b JOIN trips t ON t.id = b.trip_id"
        " WHERE b.status = 'booked' AND t.status = 'open'"
        "   AND t.depart_at >= ? AND t.depart_at <= ?",
        (datetime.combine(tomorrow, time.min).isoformat(timespec="seconds"),
         datetime.combine(tomorrow, time.max).isoformat(timespec="seconds")),
    ).fetchall()
    return [r["id"] for r in rows]


async def _send(app, chat_id, text, markup=None) -> None:
    try:
        await app.bot.send_message(chat_id, text, reply_markup=markup)
    except Exception as exc:
        log.warning("scheduled message to %s failed: %s", chat_id, exc)


async def _remind_rider(app, conn, booking) -> None:
    rider = get_user(conn, booking["rider_id"])
    if not rider:
        return
    S = copy(rider["lang"])
    await _send(app, rider["telegram_id"], trip_card(conn, booking["id"], "rider"),
                kb([[(S.BTN_IM_COMING, f"imcoming:{booking['trip_id']}")],
                    [(S.BTN_CANCEL_SEAT, f"cancelbk:{booking['id']}")],
                    [(S.BTN_OPEN, "web:#seats")]]))


async def _remind_driver(app, conn, trip) -> None:
    driver = get_user(conn, trip["driver_id"])
    if not driver:
        return
    S = copy(driver["lang"])
    when = fmt_when(datetime.fromisoformat(trip["depart_at"]))
    dest = _pname(conn, trip["dest_place_id"], driver["lang"])
    await _send(app, driver["telegram_id"], S.DRIVER_REMINDER.format(dest=dest, when=when),
                kb([[(S.BTN_ON_WAY, f"otw:{trip['id']}"), (S.BTN_ARRIVED, f"arrived:{trip['id']}")],
                    [(S.BTN_OPEN, "web:#trips")]]))


async def _prompt_rating(app, conn, row) -> None:
    rider = get_user(conn, row["rider_id"])
    driver = get_user(conn, row["driver_id"])
    if not rider:
        return
    S = copy(rider["lang"])
    await _send(app, rider["telegram_id"], S.RATE_PROMPT.format(
        dest=_pname(conn, row["to_place_id"], rider["lang"]),
        name=driver["full_name"] if driver else "—"),
        kb([[(S.BTN_RATE_UP, f"rate:up:{row['id']}"), (S.BTN_RATE_DOWN, f"rate:down:{row['id']}")]]))


async def job_reminder(context) -> None:
    conn = context.bot_data["conn"]
    app = context.application
    now = clock.now()
    expire_trips(conn)

    # Rider reminders (once each).
    for bid in due_reminders(conn, now):
        b = conn.execute("SELECT * FROM bookings WHERE id = ?", (bid,)).fetchone()
        await _remind_rider(app, conn, b)
        conn.execute("UPDATE bookings SET reminded = 1 WHERE id = ?", (bid,))
    conn.commit()

    # Driver reminders (once each, only if they haven't already set off).
    drows = conn.execute(
        "SELECT * FROM trips WHERE status = 'open' AND driver_reminded = 0"
        "   AND arrived_at IS NULL AND otw_at IS NULL"
        "   AND depart_at >= ? AND depart_at <= ?",
        (now.isoformat(timespec="seconds"),
         (now + timedelta(minutes=CONFIG.reminder_minutes_before)).isoformat(timespec="seconds")),
    ).fetchall()
    for t in drows:
        if bookings := conn.execute(
                "SELECT 1 FROM bookings WHERE trip_id=? AND status='booked'", (t["id"],)).fetchone():
            await _remind_driver(app, conn, t)
        conn.execute("UPDATE trips SET driver_reminded = 1 WHERE id = ?", (t["id"],))
    conn.commit()

    # Rating prompts for freshly-completed rides (once each).
    rrows = conn.execute(
        "SELECT b.id, b.rider_id, b.to_place_id, t.driver_id FROM bookings b"
        " JOIN trips t ON t.id = b.trip_id"
        " WHERE b.status = 'completed' AND b.rate_prompted = 0 AND t.depart_at >= ?",
        ((now - timedelta(hours=6)).isoformat(timespec="seconds"),),
    ).fetchall()
    for r in rrows:
        await _prompt_rating(app, conn, r)
        conn.execute("UPDATE bookings SET rate_prompted = 1 WHERE id = ?", (r["id"],))
    conn.commit()

    # Driver earnings summary once a trip is done.
    for t in conn.execute(
            "SELECT * FROM trips WHERE status = 'done' AND summary_sent = 0"
            "   AND depart_at >= ?",
            ((now - timedelta(hours=6)).isoformat(timespec="seconds"),)).fetchall():
        agg = conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(CASE WHEN paid=1 THEN fare ELSE 0 END),0) AS birr"
            " FROM bookings WHERE trip_id=? AND status='completed'", (t["id"],)).fetchone()
        driver = get_user(conn, t["driver_id"])
        if driver and agg["n"]:
            S = copy(driver["lang"])
            await _send(app, driver["telegram_id"], S.EARNINGS_SUMMARY.format(
                dest=_pname(conn, t["dest_place_id"], driver["lang"]),
                n=agg["n"], birr=agg["birr"]))
        conn.execute("UPDATE trips SET summary_sent = 1 WHERE id = ?", (t["id"],))
    conn.commit()


async def job_evening_confirm(context) -> None:
    conn = context.bot_data["conn"]
    app = context.application
    expire_stale(conn)
    expire_trips(conn)
    # Riders: the trip card for tomorrow, with a cancel option.
    seen_trips = set()
    for bid in due_confirmations(conn, clock.now()):
        b = conn.execute("SELECT * FROM bookings WHERE id = ?", (bid,)).fetchone()
        rider = get_user(conn, b["rider_id"])
        if rider:
            S = copy(rider["lang"])
            await _send(app, rider["telegram_id"], trip_card(conn, bid, "rider"),
                        kb([[(S.BTN_CANCEL_SEAT, f"cancelbk:{bid}")]]))
        seen_trips.add(b["trip_id"])
    # Drivers: one interactive confirm per trip that has riders.
    for tid in seen_trips:
        trip = get_trip(conn, tid)
        driver = get_user(conn, trip["driver_id"]) if trip else None
        if driver:
            S = copy(driver["lang"])
            await _send(app, driver["telegram_id"], S.EVENING_CONFIRM_Q.format(
                dest=_pname(conn, trip["dest_place_id"], driver["lang"]),
                when=fmt_when(datetime.fromisoformat(trip["depart_at"]))),
                kb([[(S.BTN_YES_DRIVING, f"evening:yes:{tid}"),
                     (S.BTN_CANCEL_TRIP, f"evening:cancel:{tid}")]]))


async def job_route_nudge(context) -> None:
    """Evening nudge: drivers with a saved route that isn't posted for tomorrow
    get a one-tap [Post] (never auto-posts — the driver still confirms)."""
    conn = context.bot_data["conn"]
    app = context.application
    rows = conn.execute(
        "SELECT dr.id, dr.driver_id, dr.dest_place_id, dr.depart_time, u.lang"
        " FROM driver_routes dr JOIN users u ON u.telegram_id = dr.driver_id"
        " WHERE dr.active = 1").fetchall()
    for r in rows:
        depart = tomorrow_departure(r["depart_time"])
        if conn.execute(
                "SELECT 1 FROM trips WHERE driver_id=? AND dest_place_id=? AND depart_at=?"
                "   AND status='open'",
                (r["driver_id"], r["dest_place_id"],
                 depart.isoformat(timespec="seconds"))).fetchone():
            continue  # already posted
        S = copy(r["lang"])
        await _send(app, r["driver_id"], S.MORNING_NUDGE.format(
            dest=_pname(conn, r["dest_place_id"], r["lang"]), time=r["depart_time"]),
            kb([[(S.BTN_POST_TODAY, f"postroute:{r['id']}")]]))


def register_jobs(app: Application) -> None:
    app.job_queue.run_daily(
        job_evening_confirm, time(hour=20, minute=15, tzinfo=clock.ADDIS))
    app.job_queue.run_daily(
        job_route_nudge, time(hour=19, minute=0, tzinfo=clock.ADDIS))
    app.job_queue.run_repeating(job_reminder, interval=300, first=60)
