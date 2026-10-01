"""Bookings join a rider to a trip for one segment.

Money never passes through the platform (UX spec section 24). `paid` is a
one-tap driver confirmation that gives us settlement data for the KPIs
without processing a birr.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from . import clock

from .fares import fare
from .places import origin_place
from .trips import booking_open, get_trip, seats_left


class TripFull(Exception):
    """No seats left."""


class NotOffered(Exception):
    """The driver did not declare this stop as a drop-off."""


class BookingClosed(Exception):
    """Past the booking cutoff (roster locked the night before)."""


def book(conn: sqlite3.Connection, *, trip_id: int, rider_id: int,
         to_place_id: int) -> sqlite3.Row:
    trip = get_trip(conn, trip_id)
    if trip is None or trip["status"] != "open":
        raise TripFull(trip_id)
    if not booking_open(datetime.fromisoformat(trip["depart_at"])):
        raise BookingClosed(trip_id)  # departed, or past the night-before cutoff
    # Idempotent: a rider can't hold two seats on the same trip (double-tap safe).
    existing = conn.execute(
        "SELECT * FROM bookings WHERE trip_id = ? AND rider_id = ? AND status = 'booked'",
        (trip_id, rider_id),
    ).fetchone()
    if existing is not None:
        return existing
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
         clock.now().isoformat(timespec="seconds")),
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


def cancelled_upcoming_for_rider(conn: sqlite3.Connection,
                                 rider_id: int) -> list[sqlite3.Row]:
    """Bookings a driver/admin cancelled on trips that would still be upcoming, so
    the rider sees why a ride vanished — not just the push notification."""
    return conn.execute(
        "SELECT b.* FROM bookings b JOIN trips t ON t.id = b.trip_id"
        " WHERE b.rider_id = ? AND b.status = 'cancelled' AND t.status = 'cancelled'"
        "   AND t.depart_at > ? ORDER BY t.depart_at",
        (rider_id, clock.now().isoformat(timespec="seconds")),
    ).fetchall()


def history_for_rider(conn: sqlite3.Connection, rider_id: int,
                      limit: int = 60) -> list[sqlite3.Row]:
    """Past rides for the receipts view: any booking whose trip has departed,
    newest first — completed, no-show or cancelled."""
    return conn.execute(
        "SELECT b.* FROM bookings b JOIN trips t ON t.id = b.trip_id"
        " WHERE b.rider_id = ? AND t.depart_at < ?"
        " ORDER BY t.depart_at DESC LIMIT ?",
        (rider_id, clock.now().isoformat(timespec="seconds"), limit),
    ).fetchall()


def bookings_for_rider(conn: sqlite3.Connection, rider_id: int,
                       upcoming_only: bool = True) -> list[sqlite3.Row]:
    sql = ("SELECT b.* FROM bookings b JOIN trips t ON t.id = b.trip_id"
           " WHERE b.rider_id = ? AND b.status = 'booked'")
    params: list = [rider_id]
    if upcoming_only:
        sql += " AND t.depart_at > ?"
        params.append(clock.now().isoformat(timespec="seconds"))
    return conn.execute(sql + " ORDER BY t.depart_at", params).fetchall()
