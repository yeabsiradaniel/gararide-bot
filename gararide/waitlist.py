"""Seat waitlist for full trips. When a rider cancels, those waiting are pinged."""
from __future__ import annotations

import sqlite3

from . import clock


def join(conn: sqlite3.Connection, trip_id: int, rider_id: int, to_place_id: int) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO waitlist (trip_id, rider_id, to_place_id, created_at)"
        " VALUES (?, ?, ?, ?)",
        (trip_id, rider_id, to_place_id, clock.now().isoformat(timespec="seconds")))
    conn.commit()


def remove(conn: sqlite3.Connection, trip_id: int, rider_id: int) -> None:
    conn.execute("DELETE FROM waitlist WHERE trip_id = ? AND rider_id = ?",
                 (trip_id, rider_id))
    conn.commit()


def for_trip(conn: sqlite3.Connection, trip_id: int) -> list[sqlite3.Row]:
    """Everyone waiting on this trip, oldest first."""
    return conn.execute(
        "SELECT * FROM waitlist WHERE trip_id = ? ORDER BY created_at", (trip_id,)
    ).fetchall()


def is_waiting(conn: sqlite3.Connection, trip_id: int, rider_id: int) -> bool:
    return conn.execute(
        "SELECT 1 FROM waitlist WHERE trip_id = ? AND rider_id = ?",
        (trip_id, rider_id)).fetchone() is not None
