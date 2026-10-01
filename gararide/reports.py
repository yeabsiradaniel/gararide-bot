"""Reasoned reports that reach an admin.

Unlike a block (silent, no reason, invisible to the other party — see blocks.py),
a report carries a reason and lands in the admin's queue. The reported party is
still never notified; admins triage and resolve. Both can coexist: a rider can
block *and* report the same person.
"""
from __future__ import annotations

import sqlite3

from . import clock

# The reasons the app offers. Free-form notes ride alongside in the `note` column.
# 'driver_no_show' is filed by the rider-taps "driver didn't show" flow.
REASONS = ("unsafe_driving", "no_show", "rude", "wrong_car", "driver_no_show", "other")


def file_report(conn: sqlite3.Connection, *, reporter_id: int, reported_id: int,
                reason: str, trip_id: int | None = None,
                note: str | None = None) -> int:
    cur = conn.execute(
        "INSERT INTO reports (reporter_id, reported_id, trip_id, reason, note,"
        " created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (reporter_id, reported_id, trip_id, reason, (note or None),
         clock.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    return cur.lastrowid


def open_reports(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Unresolved reports, newest first, with both parties' names for the admin."""
    return conn.execute(
        "SELECT r.id, r.reason, r.note, r.trip_id, r.created_at,"
        "       rp.full_name AS reporter_name,"
        "       rd.full_name AS reported_name, rd.phone AS reported_phone,"
        "       rd.tower AS reported_tower"
        " FROM reports r"
        " JOIN users rp ON rp.telegram_id = r.reporter_id"
        " JOIN users rd ON rd.telegram_id = r.reported_id"
        " WHERE r.status = 'open'"
        " ORDER BY r.created_at DESC",
    ).fetchall()


def resolve_report(conn: sqlite3.Connection, report_id: int) -> bool:
    cur = conn.execute(
        "UPDATE reports SET status = 'resolved' WHERE id = ? AND status = 'open'",
        (report_id,))
    conn.commit()
    return cur.rowcount > 0


def open_report_count(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "SELECT COUNT(*) AS c FROM reports WHERE status = 'open'").fetchone()["c"]
