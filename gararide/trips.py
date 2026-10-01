"""Trips posted by drivers.

The drop-off checklist is the driver's route declaration (UX spec section 12).
The question is "where are you willing to stop?", not "which road will you
take" — a driver may pass a stop and still decline to pull over there. Only
declared drop-offs are bookable.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, time, timedelta
from . import clock

from .config import CONFIG
from .places import all_places, origin_place, place_by_id


class InvalidDropoff(Exception):
    """A drop-off that is not between the origin and the trip's destination."""


def booking_open(depart: datetime, now: datetime | None = None) -> bool:
    """Whether a trip still accepts bookings. The roster locks at the cutoff hour
    (20:00) the night before departure, matching the evening confirmation. A trip
    departing the same day it was posted stays open until it leaves (ad-hoc)."""
    now = now or clock.now()
    if depart <= now:
        return False
    if depart.date() <= now.date():
        return True
    lock = datetime.combine(depart.date() - timedelta(days=1),
                            time(hour=CONFIG.booking_cutoff_hour))
    return now < lock


def default_dropoffs(conn: sqlite3.Connection, dest_place_id: int) -> list[int]:
    """Every stop between the origin and the destination, inclusive.

    Pre-ticked in the UI so accepting the common case is one tap.
    """
    dest = place_by_id(conn, dest_place_id)
    origin = origin_place(conn)
    lo, hi = sorted((origin["sort_order"], dest["sort_order"]))
    return [p["id"] for p in all_places(conn, CONFIG.corridor_id)
            if lo < p["sort_order"] <= hi]


def intermediate_dropoffs(conn: sqlite3.Connection, dest_place_id: int) -> list[int]:
    """Stops strictly between origin and destination (destination excluded).

    The destination is always a drop-off, so the UI does not show it as a toggle
    in the checklist — it renders it as a fixed "-> destination" label instead.
    """
    dest = place_by_id(conn, dest_place_id)
    origin = origin_place(conn)
    lo, hi = sorted((origin["sort_order"], dest["sort_order"]))
    return [p["id"] for p in all_places(conn, CONFIG.corridor_id)
            if lo < p["sort_order"] < hi]


def post_trip(conn: sqlite3.Connection, *, driver_id: int, dest_place_id: int,
              dropoff_place_ids: list[int], depart_at: datetime,
              seats: int, note: str | None = None) -> int:
    origin = origin_place(conn)
    allowed = set(default_dropoffs(conn, dest_place_id))
    chosen = set(dropoff_place_ids) | {dest_place_id}
    if not chosen <= allowed:
        raise InvalidDropoff(sorted(chosen - allowed))

    cur = conn.execute(
        "INSERT INTO trips"
        " (driver_id, origin_place_id, dest_place_id, depart_at, seats_total,"
        "  note, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (driver_id, origin["id"], dest_place_id, depart_at.isoformat(timespec="seconds"),
         seats, note, clock.now().isoformat(timespec="seconds")),
    )
    trip_id = cur.lastrowid
    for place_id in chosen:
        conn.execute(
            "INSERT INTO trip_dropoffs (trip_id, place_id) VALUES (?, ?)",
            (trip_id, place_id))
    conn.commit()
    return trip_id


def update_trip(conn: sqlite3.Connection, trip_id: int, *, depart_at: datetime,
                seats: int, note: str | None) -> None:
    """Driver edits a posted trip (time / seats / note). Validation lives in the
    endpoint; this just writes. Destination and route are not editable here."""
    conn.execute(
        "UPDATE trips SET depart_at = ?, seats_total = ?, note = ? WHERE id = ?",
        (depart_at.isoformat(timespec="seconds"), seats, note, trip_id))
    conn.commit()


def get_trip(conn: sqlite3.Connection, trip_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()


def dropoffs(conn: sqlite3.Connection, trip_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT p.* FROM trip_dropoffs d JOIN places p ON p.id = d.place_id"
        " WHERE d.trip_id = ? ORDER BY p.sort_order",
        (trip_id,),
    ).fetchall()


def seats_left(conn: sqlite3.Connection, trip_id: int) -> int:
    trip = get_trip(conn, trip_id)
    taken = conn.execute(
        "SELECT COUNT(*) AS c FROM bookings WHERE trip_id = ? AND status = 'booked'",
        (trip_id,),
    ).fetchone()["c"]
    return trip["seats_total"] - taken


def trips_by_driver(conn: sqlite3.Connection, driver_id: int,
                    upcoming_only: bool = True) -> list[sqlite3.Row]:
    sql = "SELECT * FROM trips WHERE driver_id = ? AND status = 'open'"
    params: list = [driver_id]
    if upcoming_only:
        sql += " AND depart_at > ?"
        params.append(clock.now().isoformat(timespec="seconds"))
    return conn.execute(sql + " ORDER BY depart_at", params).fetchall()


def cancel_trip(conn: sqlite3.Connection, trip_id: int) -> None:
    conn.execute("UPDATE trips SET status = 'cancelled' WHERE id = ?", (trip_id,))
    conn.execute(
        "UPDATE bookings SET status = 'cancelled' WHERE trip_id = ? AND status = 'booked'",
        (trip_id,))
    conn.commit()


def mark_arrived(conn: sqlite3.Connection, trip_id: int) -> str:
    """Driver is at the pickup — stamp the arrival that starts the boarding clock.
    Idempotent: a second tap keeps the original time so the countdown is stable."""
    trip = get_trip(conn, trip_id)
    if trip and trip["arrived_at"]:
        return trip["arrived_at"]
    now = clock.now().isoformat(timespec="seconds")
    conn.execute("UPDATE trips SET arrived_at = ? WHERE id = ?", (now, trip_id))
    conn.commit()
    return now


def mark_on_way(conn: sqlite3.Connection, trip_id: int, eta_minutes: int) -> str:
    """Driver has set off for pickup. Re-tapping updates the ETA (running late),
    restarting the rider's countdown from now."""
    now = clock.now().isoformat(timespec="seconds")
    conn.execute("UPDATE trips SET otw_at = ?, otw_eta = ? WHERE id = ?",
                 (now, eta_minutes, trip_id))
    conn.commit()
    return now


def dwell_expired(trip: sqlite3.Row, now: datetime | None = None) -> bool:
    """True once the driver has waited the full dwell after arriving (so a no-show
    can be marked). If they never tapped 'arrived', fall back to depart time."""
    now = now or clock.now()
    base = trip["arrived_at"] or trip["depart_at"]
    return now >= datetime.fromisoformat(base) + timedelta(minutes=CONFIG.dwell_minutes)


def expire_trips(conn: sqlite3.Connection, now: datetime | None = None) -> int:
    """Close out trips whose departure has passed so they stop lingering as 'open'
    (and can never surface in search or near-misses). Their bookings complete."""
    cutoff = (now or clock.now()).isoformat(timespec="seconds")
    conn.execute(
        "UPDATE bookings SET status = 'completed'"
        " WHERE status = 'booked' AND trip_id IN"
        "   (SELECT id FROM trips WHERE status = 'open' AND depart_at < ?)",
        (cutoff,))
    cur = conn.execute(
        "UPDATE trips SET status = 'done' WHERE status = 'open' AND depart_at < ?",
        (cutoff,))
    conn.commit()
    return cur.rowcount
