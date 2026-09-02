"""Outbound messages. The Trip Card is the whole product (UX spec section 20)."""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime

from . import strings_am as S
from .fmt import fmt_money, fmt_person, fmt_when
from .places import place_by_id
from .trips import get_trip
from .users import get_user

log = logging.getLogger(__name__)


def trip_card(conn: sqlite3.Connection, booking_id: int, for_role: str) -> str:
    booking = conn.execute("SELECT * FROM bookings WHERE id = ?",
                           (booking_id,)).fetchone()
    trip = get_trip(conn, booking["trip_id"])
    driver = get_user(conn, trip["driver_id"])
    rider = get_user(conn, booking["rider_id"])
    depart = datetime.fromisoformat(trip["depart_at"])
    dest = place_by_id(conn, booking["to_place_id"])["name_am"]

    if for_role == "rider":
        return "\n".join([
            fmt_when(depart),
            S.BAY_ALPHA,
            "",
            f"👤 {fmt_person(driver)}",
            f"🚗 {driver['car_model'] or '—'} · {driver['plate'] or '—'}",
            f"📍 → {dest}",
            f"💵 {S.PAY_IN_CAR.format(amount=fmt_money(booking['fare']))}",
            f"📞 {driver['phone']}",
        ])
    return "\n".join([
        fmt_when(depart),
        S.BAY_ALPHA,
        "",
        f"👤 {fmt_person(rider)} → {dest}",
        f"💵 {fmt_money(booking['fare'])}",
        f"📞 {rider['phone']}",
    ])


async def send_trip_card(bot, conn: sqlite3.Connection, booking_id: int) -> None:
    booking = conn.execute("SELECT * FROM bookings WHERE id = ?",
                           (booking_id,)).fetchone()
    trip = get_trip(conn, booking["trip_id"])
    for chat_id, role in ((booking["rider_id"], "rider"),
                          (trip["driver_id"], "driver")):
        try:
            await bot.send_message(chat_id, trip_card(conn, booking_id, role))
        except Exception as exc:  # blocked the bot, deactivated, etc.
            log.warning("trip card to %s failed: %s", chat_id, exc)
