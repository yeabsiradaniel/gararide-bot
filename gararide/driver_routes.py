"""Driver saved routes — the commute template behind one-tap re-posting.

A driver runs the same road most mornings. Rather than rebuild the trip each day,
they save it once; posting tomorrow's ride is then a single tap. Like the rider's
saved trips, this is never automatic — the driver still confirms each day, so a
route they can't drive tomorrow simply doesn't get posted (spec §3.4 philosophy).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

from .trips import post_trip


def _dropoff_ids(route: sqlite3.Row) -> list[int]:
    return [int(x) for x in route["dropoffs"].split(",") if x]


def save_route(conn: sqlite3.Connection, *, driver_id: int, dest_place_id: int,
               dropoff_place_ids: list[int], depart_time: str, seats: int,
               days_mask: int = 0) -> int:
    dropoffs = ",".join(str(i) for i in dropoff_place_ids)
    cur = conn.execute(
        "INSERT INTO driver_routes"
        " (driver_id, dest_place_id, dropoffs, depart_time, seats, days_mask, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (driver_id, dest_place_id, dropoffs, depart_time, seats, days_mask,
         datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    return cur.lastrowid


def routes_for(conn: sqlite3.Connection, driver_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM driver_routes WHERE driver_id = ? AND active = 1"
        " ORDER BY depart_time",
        (driver_id,),
    ).fetchall()


def get_route(conn: sqlite3.Connection, route_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM driver_routes WHERE id = ?", (route_id,)).fetchone()


def deactivate_route(conn: sqlite3.Connection, route_id: int) -> None:
    conn.execute("UPDATE driver_routes SET active = 0 WHERE id = ?", (route_id,))
    conn.commit()


def tomorrow_departure(depart_time: str) -> datetime:
    hh, mm = (int(x) for x in depart_time.split(":"))
    return (datetime.now() + timedelta(days=1)).replace(
        hour=hh, minute=mm, second=0, microsecond=0)


def post_route_tomorrow(conn: sqlite3.Connection, route: sqlite3.Row) -> int:
    return post_trip(
        conn, driver_id=route["driver_id"], dest_place_id=route["dest_place_id"],
        dropoff_place_ids=_dropoff_ids(route),
        depart_at=tomorrow_departure(route["depart_time"]), seats=route["seats"])
