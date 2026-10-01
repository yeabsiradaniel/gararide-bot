"""Thumbs up/down after a completed ride — an ADMIN-ONLY trust signal.

Never shown to the rated driver, and no driver aggregate is ever shown to
riders (UX spec: ratings are ops-only, like block counts). A rider sees only
their own tap, so they know they rated. One rating per booking; re-rating
overwrites.
"""
from __future__ import annotations

import sqlite3

from . import clock


def rate(conn: sqlite3.Connection, *, booking_id: int, rater_id: int,
         ratee_id: int, value: int) -> None:
    conn.execute(
        "INSERT INTO ratings (booking_id, rater_id, ratee_id, value, created_at)"
        " VALUES (?, ?, ?, ?, ?)"
        " ON CONFLICT(booking_id) DO UPDATE SET value = excluded.value,"
        "   created_at = excluded.created_at",
        (booking_id, rater_id, ratee_id, value,
         clock.now().isoformat(timespec="seconds")),
    )
    conn.commit()


def rating_for_booking(conn: sqlite3.Connection, booking_id: int) -> int | None:
    row = conn.execute(
        "SELECT value FROM ratings WHERE booking_id = ?", (booking_id,)).fetchone()
    return row["value"] if row else None


def tally_for_driver(conn: sqlite3.Connection, driver_id: int) -> dict:
    row = conn.execute(
        "SELECT"
        "  COALESCE(SUM(CASE WHEN value = 1 THEN 1 ELSE 0 END), 0) AS up,"
        "  COALESCE(SUM(CASE WHEN value = -1 THEN 1 ELSE 0 END), 0) AS down"
        " FROM ratings WHERE ratee_id = ?", (driver_id,)).fetchone()
    return {"up": row["up"], "down": row["down"]}
