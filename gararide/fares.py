"""Fare lookup.

Fares are seeded, not computed. They are deliberately set below the driver's
trip cost — see execution plan section 1. Never derive a fare from distance
or time at runtime.
"""
from __future__ import annotations

import sqlite3


def fare(conn: sqlite3.Connection, from_place_id: int, to_place_id: int) -> int:
    row = conn.execute(
        "SELECT birr FROM fares WHERE from_place_id = ? AND to_place_id = ?",
        (from_place_id, to_place_id),
    ).fetchone()
    if row is None:
        raise KeyError(f"no fare for {from_place_id} -> {to_place_id}")
    return row["birr"]
