"""Bookings join a rider to a trip for one segment.

Money never passes through the platform (UX spec section 24). `paid` is a
one-tap driver confirmation that gives us settlement data for the KPIs
without processing a birr.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime

from .fares import fare
from .places import origin_place
from .trips import get_trip, seats_left


class TripFull(Exception):
    """No seats left."""


class NotOffered(Exception):
    """The driver did not declare this stop as a drop-off."""


def book(conn: sqlite3.Connection, *, trip_id: int, rider_id: int,
         to_place_id: int) -> sqlite3.Row:
    trip = get_trip(conn, trip_id)
    if trip is None or trip["status"] != "open":
        raise TripFull(trip_id)
    offered = conn.execute(
        "SELECT 1 FROM trip_dropoffs WHERE trip_id = ? AND place_id = ?",
        (trip_id, to_place_id),
    ).fetchone()
    if offered is None:
        raise NotOffered(to_place_id)
    if seats_left(conn, trip_id) <= 0:
        raise TripFull(trip_id)

    origin = origin_place(conn)
    cur = conn.execute(
        "INSERT INTO bookings"
        " (trip_id, rider_id, from_place_id, to_place_id, fare, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (trip_id, rider_id, origin["id"], to_place_id,
         fare(conn, origin["id"], to_place_id),
         datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    return conn.execute("SELECT * FROM bookings WHERE id = ?",
                        (cur.lastrowid,)).fetchone()


def cancel_booking(conn: sqlite3.Connection, booking_id: int) -> sqlite3.Row | None:
    row = conn.execute("SELECT * FROM bookings WHERE id = ?",
                       (booking_id,)).fetchone()
    if row is None:
        return None
    conn.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?",
                 (booking_id,))
    conn.commit()
    return row


def mark_no_show(conn: sqlite3.Connection, booking_id: int) -> None:
    conn.execute("UPDATE bookings SET status = 'no_show' WHERE id = ?", (booking_id,))
    conn.commit()


def mark_paid(conn: sqlite3.Connection, booking_id: int) -> None:
    conn.execute("UPDATE bookings SET paid = 1 WHERE id = ?", (booking_id,))
    conn.commit()


def bookings_for_trip(conn: sqlite3.Connection, trip_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM bookings WHERE trip_id = ? AND status = 'booked'"
        " ORDER BY created_at",
        (trip_id,),
    ).fetchall()


def bookings_for_rider(conn: sqlite3.Connection, rider_id: int,
                       upcoming_only: bool = True) -> list[sqlite3.Row]:
    sql = ("SELECT b.* FROM bookings b JOIN trips t ON t.id = b.trip_id"
           " WHERE b.rider_id = ? AND b.status = 'booked'")
    params: list = [rider_id]
    if upcoming_only:
        sql += " AND t.depart_at > ?"
        params.append(datetime.now().isoformat(timespec="seconds"))
    return conn.execute(sql + " ORDER BY t.depart_at", params).fetchall()
