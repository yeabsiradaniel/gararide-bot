"""Corridor stops. The stop list is seed data, never code (UX spec section 4)."""
from __future__ import annotations

import csv
import sqlite3

from .config import CONFIG


def seed_corridor(conn: sqlite3.Connection, csv_path: str) -> None:
    """Load stops and derive the full fare matrix from fare_from_origin."""
    with open(csv_path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    for row in rows:
        conn.execute(
            "INSERT INTO places (slug, name_am, name_en, corridor_id, sort_order)"
            " VALUES (?, ?, ?, ?, ?)"
            " ON CONFLICT(slug) DO UPDATE SET"
            "   name_am=excluded.name_am, name_en=excluded.name_en,"
            "   sort_order=excluded.sort_order",
            (row["slug"], row["name_am"], row["name_en"],
             CONFIG.corridor_id, int(row["sort_order"])),
        )

    ids = {r["slug"]: r["id"] for r in all_places(conn, CONFIG.corridor_id)}
    origin_fare = {r["slug"]: int(r["fare_from_origin"]) for r in rows}

    # A segment fare is the difference between the two stops' origin fares.
    # Symmetric, so the evening return leg costs the same as the morning.
    for a_slug, a_fare in origin_fare.items():
        for b_slug, b_fare in origin_fare.items():
            conn.execute(
                "INSERT INTO fares (from_place_id, to_place_id, birr)"
                " VALUES (?, ?, ?)"
                " ON CONFLICT(from_place_id, to_place_id) DO UPDATE SET"
                "   birr=excluded.birr",
                (ids[a_slug], ids[b_slug], abs(a_fare - b_fare)),
            )
    conn.commit()


def all_places(conn: sqlite3.Connection, corridor_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM places WHERE corridor_id = ? ORDER BY sort_order",
        (corridor_id,),
    ).fetchall()


def place_by_slug(conn: sqlite3.Connection, slug: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM places WHERE slug = ?", (slug,)).fetchone()


def place_by_id(conn: sqlite3.Connection, place_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM places WHERE id = ?", (place_id,)).fetchone()
    if row is None:
        raise KeyError(f"no place with id {place_id}")
    return row


def origin_place(conn: sqlite3.Connection) -> sqlite3.Row:
    """The Phase 1 locked origin. Phase 2 removes the caller, not this function."""
    row = place_by_slug(conn, CONFIG.origin_slug)
    if row is None:
        raise KeyError(f"origin {CONFIG.origin_slug!r} not seeded")
    return row


def destinations(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Every stop a rider or driver may choose as a destination."""
    return [p for p in all_places(conn, CONFIG.corridor_id)
            if p["slug"] != CONFIG.origin_slug]
