"""Trips posted by drivers.

The drop-off checklist is the driver's route declaration (UX spec section 12).
The question is "where are you willing to stop?", not "which road will you
take" — a driver may pass a stop and still decline to pull over there. Only
declared drop-offs are bookable.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime

from .config import CONFIG
from .places import all_places, origin_place, place_by_id


class InvalidDropoff(Exception):
    """A drop-off that is not between the origin and the trip's destination."""


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
         seats, note, datetime.now().isoformat(timespec="seconds")),
    )
    trip_id = cur.lastrowid
    for place_id in chosen:
        conn.execute(
            "INSERT INTO trip_dropoffs (trip_id, place_id) VALUES (?, ?)",
            (trip_id, place_id))
    conn.commit()
    return trip_id


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
        params.append(datetime.now().isoformat(timespec="seconds"))
    return conn.execute(sql + " ORDER BY depart_at", params).fetchall()


def cancel_trip(conn: sqlite3.Connection, trip_id: int) -> None:
    conn.execute("UPDATE trips SET status = 'cancelled' WHERE id = ?", (trip_id,))
    conn.execute(
        "UPDATE bookings SET status = 'cancelled' WHERE trip_id = ? AND status = 'booked'",
        (trip_id,))
    conn.commit()
