"""Rider-posted requests.

Most marketplaces let supply post and demand search. In a thin market that
wastes half the signal (UX spec section 6). A request is a standing offer any
driver can fill, and the count of open requests is what turns an empty search
result into "3 neighbours also want this".
"""
from __future__ import annotations

import sqlite3
from datetime import datetime

from .blocks import blocked_pairs
from .places import origin_place


def post_request(conn: sqlite3.Connection, *, rider_id: int, dest_place_id: int,
                 window_start: datetime, window_end: datetime) -> int:
    origin = origin_place(conn)
    cur = conn.execute(
        "INSERT INTO requests"
        " (rider_id, origin_place_id, dest_place_id, window_start, window_end,"
        "  created_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (rider_id, origin["id"], dest_place_id,
         window_start.isoformat(timespec="seconds"),
         window_end.isoformat(timespec="seconds"),
         datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    return cur.lastrowid


def open_requests(conn: sqlite3.Connection, *, for_driver_id: int | None = None,
                  dest_place_id: int | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM requests WHERE status = 'open'"
    params: list = []
    if dest_place_id is not None:
        sql += " AND dest_place_id = ?"
        params.append(dest_place_id)
    rows = conn.execute(sql + " ORDER BY window_start", params).fetchall()
    if for_driver_id is not None:
        blocked = blocked_pairs(conn, for_driver_id)
        rows = [r for r in rows if r["rider_id"] not in blocked]
    return rows


def requests_matching_trip(conn: sqlite3.Connection, trip_id: int) -> list[sqlite3.Row]:
    """Open requests this trip could carry: a declared drop-off, inside the window."""
    trip = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if trip is None or trip["status"] != "open":
        return []
    return conn.execute(
        "SELECT r.* FROM requests r"
        " WHERE r.status = 'open'"
        "   AND r.dest_place_id IN"
        "       (SELECT place_id FROM trip_dropoffs WHERE trip_id = ?)"
        "   AND ? BETWEEN r.window_start AND r.window_end"
        " ORDER BY r.window_start",
        (trip_id, trip["depart_at"]),
    ).fetchall()


def fill_request(conn: sqlite3.Connection, request_id: int) -> None:
    conn.execute("UPDATE requests SET status = 'filled' WHERE id = ?", (request_id,))
    conn.commit()


def cancel_request(conn: sqlite3.Connection, request_id: int) -> None:
    conn.execute("UPDATE requests SET status = 'cancelled' WHERE id = ?",
                 (request_id,))
    conn.commit()


def expire_stale(conn: sqlite3.Connection, now: datetime | None = None) -> int:
    cutoff = (now or datetime.now()).isoformat(timespec="seconds")
    cur = conn.execute(
        "UPDATE requests SET status = 'expired'"
        " WHERE status = 'open' AND window_end < ?", (cutoff,))
    conn.commit()
    return cur.rowcount


def demand_count(conn: sqlite3.Connection, dest_place_id: int,
                 window_start: datetime, window_end: datetime) -> int:
    return conn.execute(
        "SELECT COUNT(*) AS c FROM requests"
        " WHERE status = 'open' AND dest_place_id = ?"
        "   AND window_start <= ? AND window_end >= ?",
        (dest_place_id, window_end.isoformat(timespec="seconds"),
         window_start.isoformat(timespec="seconds")),
    ).fetchone()["c"]
