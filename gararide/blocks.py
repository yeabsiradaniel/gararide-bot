"""The safety valve (UX spec section 17).

One tap hides a person permanently. The blocked party is never told, never
given a reason, and never sees a change. Counts are an ops signal only.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime


def block(conn: sqlite3.Connection, blocker_id: int, blocked_id: int) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO blocks (blocker_id, blocked_id, created_at)"
        " VALUES (?, ?, ?)",
        (blocker_id, blocked_id, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()


def blocked_pairs(conn: sqlite3.Connection, user_id: int) -> set[int]:
    """Everyone this user must not be matched with, in either direction."""
    rows = conn.execute(
        "SELECT blocked_id AS other FROM blocks WHERE blocker_id = ?"
        " UNION SELECT blocker_id AS other FROM blocks WHERE blocked_id = ?",
        (user_id, user_id),
    ).fetchall()
    return {r["other"] for r in rows}


def decline_count(conn: sqlite3.Connection, user_id: int) -> int:
    """How many people have quietly declined this person. Ops only — never displayed."""
    return conn.execute(
        "SELECT COUNT(*) AS c FROM blocks WHERE blocked_id = ?", (user_id,)
    ).fetchone()["c"]
