"""Saved trips — the convenience layer over the same trip object (spec §3.4).

A commute is just a trip taken repeatedly. After enough identical bookings we
offer to save it; a saved trip is a one-tap repeat, never an auto-booking.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from . import clock

from .config import CONFIG


def _times_taken(conn: sqlite3.Connection, user_id: int, dest_place_id: int,
                 depart_time: str) -> int:
    return conn.execute(
        "SELECT COUNT(*) AS c FROM bookings b JOIN trips t ON t.id = b.trip_id"
        " WHERE b.rider_id = ? AND b.to_place_id = ?"
        "   AND substr(t.depart_at, 12, 5) = ?"
        "   AND b.status IN ('booked', 'completed')",
        (user_id, dest_place_id, depart_time),
    ).fetchone()["c"]


def _already_saved(conn: sqlite3.Connection, user_id: int, dest_place_id: int,
                   depart_time: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM saved_trips WHERE user_id = ? AND dest_place_id = ?"
        "   AND depart_time = ? AND active = 1",
        (user_id, dest_place_id, depart_time),
    ).fetchone() is not None


def should_offer_save(conn: sqlite3.Connection, user_id: int, dest_place_id: int,
                      depart_time: str) -> bool:
    if _already_saved(conn, user_id, dest_place_id, depart_time):
        return False
    return _times_taken(conn, user_id, dest_place_id, depart_time) >= \
        CONFIG.save_prompt_threshold


def save_trip(conn: sqlite3.Connection, *, user_id: int, dest_place_id: int,
              depart_time: str, days_mask: int) -> int:
    cur = conn.execute(
        "INSERT INTO saved_trips (user_id, dest_place_id, depart_time, days_mask,"
        " created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, dest_place_id, depart_time, days_mask,
         clock.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    return cur.lastrowid


def saved_for(conn: sqlite3.Connection, user_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM saved_trips WHERE user_id = ? AND active = 1"
        " ORDER BY depart_time",
        (user_id,),
    ).fetchall()


def deactivate_saved(conn: sqlite3.Connection, saved_id: int) -> None:
    conn.execute("UPDATE saved_trips SET active = 0 WHERE id = ?", (saved_id,))
    conn.commit()
