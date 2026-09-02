"""Segment matching and near-miss search.

A trip is bookable for a rider going to D when the driver declared D as a
drop-off, the trip has a free seat, it leaves inside the rider's window, and
neither party has declined the other.

There is no "no results" screen (UX spec section 8), so every search that
returns nothing must be able to offer near-misses instead.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta

from .blocks import blocked_pairs
from .config import CONFIG
from .fares import fare
from .places import origin_place, place_by_id
from .users import get_user


@dataclass(frozen=True)
class Match:
    trip_id: int
    driver_id: int
    depart_at: datetime
    seats_left: int
    fare: int
    dest_place_id: int


@dataclass(frozen=True)
class NearMiss:
    trip_id: int
    driver_id: int
    depart_at: datetime
    fare: int
    dest_place_id: int
    reason: str  # "earlier" | "later" | "partway"


def _candidate_rows(conn: sqlite3.Connection, start: datetime,
                    end: datetime) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT t.*,"
        "  (t.seats_total - (SELECT COUNT(*) FROM bookings b"
        "    WHERE b.trip_id = t.id AND b.status = 'booked')) AS seats_left"
        " FROM trips t"
        " WHERE t.status = 'open' AND t.depart_at >= ? AND t.depart_at <= ?"
        " ORDER BY t.depart_at",
        (start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds")),
    ).fetchall()


def _permitted(conn: sqlite3.Connection, rider, trip: sqlite3.Row,
               blocked: set[int]) -> bool:
    if trip["driver_id"] == rider["telegram_id"]:
        return False  # you can't ride in your own car
    if trip["driver_id"] in blocked:
        return False
    if trip["seats_left"] <= 0:
        return False
    if rider["women_only"]:
        driver = get_user(conn, trip["driver_id"])
        if driver is None or not driver["is_female"]:
            return False
    if rider["women_present"]:
        others = conn.execute(
            "SELECT u.is_female FROM bookings b JOIN users u"
            "  ON u.telegram_id = b.rider_id"
            " WHERE b.trip_id = ? AND b.status = 'booked'",
            (trip["id"],),
        ).fetchall()
        driver = get_user(conn, trip["driver_id"])
        female_present = (driver is not None and driver["is_female"]) or any(
            o["is_female"] for o in others)
        if not female_present:
            return False
    return True


def _offers(conn: sqlite3.Connection, trip_id: int, place_id: int) -> bool:
    return conn.execute(
        "SELECT 1 FROM trip_dropoffs WHERE trip_id = ? AND place_id = ?",
        (trip_id, place_id),
    ).fetchone() is not None


def find_trips(conn: sqlite3.Connection, *, rider_id: int, dest_place_id: int,
               window_start: datetime, window_end: datetime) -> list[Match]:
    rider = get_user(conn, rider_id)
    if rider is None:
        return []
    blocked = blocked_pairs(conn, rider_id)
    origin = origin_place(conn)

    out: list[Match] = []
    for trip in _candidate_rows(conn, window_start, window_end):
        if not _permitted(conn, rider, trip, blocked):
            continue
        if not _offers(conn, trip["id"], dest_place_id):
            continue
        out.append(Match(
            trip_id=trip["id"],
            driver_id=trip["driver_id"],
            depart_at=datetime.fromisoformat(trip["depart_at"]),
            seats_left=trip["seats_left"],
            fare=fare(conn, origin["id"], dest_place_id),
            dest_place_id=dest_place_id,
        ))
    return out


def near_misses(conn: sqlite3.Connection, *, rider_id: int, dest_place_id: int,
                window_start: datetime, window_end: datetime) -> list[NearMiss]:
    """Trips worth showing when nothing matched exactly.

    Two kinds: the right destination at a nearby time, and a trip inside the
    window that gets the rider part of the way along the corridor.
    """
    rider = get_user(conn, rider_id)
    if rider is None:
        return []
    blocked = blocked_pairs(conn, rider_id)
    origin = origin_place(conn)
    dest = place_by_id(conn, dest_place_id)
    pad = timedelta(minutes=CONFIG.near_miss_window_minutes)

    exact_ids = {m.trip_id for m in find_trips(
        conn, rider_id=rider_id, dest_place_id=dest_place_id,
        window_start=window_start, window_end=window_end)}

    out: list[NearMiss] = []
    for trip in _candidate_rows(conn, window_start - pad, window_end + pad):
        if trip["id"] in exact_ids or not _permitted(conn, rider, trip, blocked):
            continue
        depart = datetime.fromisoformat(trip["depart_at"])

        if _offers(conn, trip["id"], dest_place_id):
            reason = "earlier" if depart < window_start else "later"
            out.append(NearMiss(
                trip_id=trip["id"], driver_id=trip["driver_id"],
                depart_at=depart, fare=fare(conn, origin["id"], dest_place_id),
                dest_place_id=dest_place_id, reason=reason))
            continue

        if window_start <= depart <= window_end:
            partway = conn.execute(
                "SELECT p.* FROM trip_dropoffs d JOIN places p ON p.id = d.place_id"
                " WHERE d.trip_id = ? AND p.sort_order < ?"
                " ORDER BY p.sort_order DESC LIMIT 1",
                (trip["id"], dest["sort_order"]),
            ).fetchone()
            if partway is not None:
                out.append(NearMiss(
                    trip_id=trip["id"], driver_id=trip["driver_id"],
                    depart_at=depart,
                    fare=fare(conn, origin["id"], partway["id"]),
                    dest_place_id=partway["id"], reason="partway"))
    return out
