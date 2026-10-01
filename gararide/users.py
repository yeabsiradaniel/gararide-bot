"""Registration against the desk-verified allowlist.

Sign-up is three taps because verification already happened in person
(UX spec section 11). The app never asks for a document, and a phone number
that was not verified at the desk cannot register at all.
"""
from __future__ import annotations

import csv
import re
import sqlite3
from datetime import datetime
from . import clock


class NotAllowlisted(Exception):
    """This phone was not verified at the onboarding desk, or is already claimed."""


class NotOnRoster(Exception):
    """No allowlist row for this phone — nothing to remove."""


def normalise_phone(raw: str) -> str:
    """Reduce any Ethiopian format to 251XXXXXXXXX."""
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("251"):
        return digits
    if digits.startswith("0"):
        return "251" + digits[1:]
    return "251" + digits


def import_allowlist(conn: sqlite3.Connection, csv_path: str) -> int:
    with open(csv_path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    now = clock.now().isoformat(timespec="seconds")
    for row in rows:
        conn.execute(
            "INSERT INTO allowlist"
            " (phone, full_name, tower, role, car_model, car_color, plate, is_female,"
            "  car_seats, verified_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(phone) DO UPDATE SET"
            "   full_name=excluded.full_name, tower=excluded.tower,"
            "   role=excluded.role, car_model=excluded.car_model,"
            "   car_color=excluded.car_color, plate=excluded.plate,"
            "   is_female=excluded.is_female, car_seats=excluded.car_seats",
            (normalise_phone(row["phone"]), row["full_name"], row["tower"],
             row["role"], row.get("car_model") or None, row.get("car_color") or None,
             row.get("plate") or None, int(row.get("is_female") or 0),
             int(row["car_seats"]) if row.get("car_seats") else None, now),
        )
    conn.commit()
    return len(rows)


def add_to_allowlist(conn: sqlite3.Connection, *, phone: str, full_name: str,
                     tower: str, role: str = "driver", car_model: str | None = None,
                     car_color: str | None = None, plate: str | None = None,
                     is_female: bool = False,
                     car_seats: int | None = None) -> sqlite3.Row:
    """Desk-verify one person into the allowlist (the in-app equivalent of a CSV
    import row). Upserts on phone so re-adding corrects a typo instead of failing.
    The person still self-onboards through the bot afterwards."""
    now = clock.now().isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO allowlist"
        " (phone, full_name, tower, role, car_model, car_color, plate, is_female,"
        "  car_seats, verified_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(phone) DO UPDATE SET"
        "   full_name=excluded.full_name, tower=excluded.tower,"
        "   role=excluded.role, car_model=excluded.car_model,"
        "   car_color=excluded.car_color, plate=excluded.plate,"
        "   is_female=excluded.is_female, car_seats=excluded.car_seats",
        (normalise_phone(phone), full_name, tower, role, car_model or None,
         car_color or None, plate or None, int(is_female), car_seats, now),
    )
    conn.commit()
    return lookup_allowlist(conn, phone)


def remove_driver(conn: sqlite3.Connection, phone: str) -> dict:
    """Remove a driver as an admin. Off the roster for good; if they had already
    onboarded, their open trips (and the bookings on them) are cancelled and their
    account is deactivated so they can no longer operate. History rows stay intact
    for the record — foreign keys forbid a hard delete anyway."""
    p = normalise_phone(phone)
    row = conn.execute(
        "SELECT claimed_by FROM allowlist WHERE phone = ?", (p,)).fetchone()
    if row is None:
        raise NotOnRoster(phone)
    claimed_by = row["claimed_by"]
    trips_cancelled = 0
    if claimed_by is not None:
        for t in conn.execute(
                "SELECT id FROM trips WHERE driver_id = ? AND status = 'open'",
                (claimed_by,)).fetchall():
            conn.execute("UPDATE trips SET status = 'cancelled' WHERE id = ?", (t["id"],))
            conn.execute(
                "UPDATE bookings SET status = 'cancelled'"
                " WHERE trip_id = ? AND status = 'booked'", (t["id"],))
            trips_cancelled += 1
        conn.execute("UPDATE users SET active = 0 WHERE telegram_id = ?", (claimed_by,))
    conn.execute("DELETE FROM allowlist WHERE phone = ?", (p,))
    conn.commit()
    return {"was_onboarded": claimed_by is not None, "trips_cancelled": trips_cancelled}


def update_driver(conn: sqlite3.Connection, phone: str, *, full_name: str, tower: str,
                  car_model: str | None, car_color: str | None, plate: str | None,
                  car_seats: int | None, is_female: bool) -> sqlite3.Row:
    """Admin edit of a desk-verified driver. Updates the allowlist row and, if the
    driver has already onboarded, their live user record too so the change shows
    for riders immediately. Phone (the identity) is not editable here."""
    p = normalise_phone(phone)
    row = lookup_allowlist(conn, p)
    if row is None:
        raise NotOnRoster(phone)
    fields = (full_name, tower, car_model or None, car_color or None, plate or None,
              int(is_female), car_seats)
    conn.execute(
        "UPDATE allowlist SET full_name=?, tower=?, car_model=?, car_color=?,"
        "  plate=?, is_female=?, car_seats=? WHERE phone=?", (*fields, p))
    if row["claimed_by"] is not None:
        conn.execute(
            "UPDATE users SET full_name=?, tower=?, car_model=?, car_color=?,"
            "  plate=?, is_female=?, car_seats=? WHERE telegram_id=?",
            (*fields, row["claimed_by"]))
    conn.commit()
    return lookup_allowlist(conn, p)


def roster(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Everyone desk-verified, newest first, with whether they've onboarded yet."""
    return conn.execute(
        "SELECT phone, full_name, tower, role, car_model, car_color, plate, is_female,"
        "       car_seats, verified_at, claimed_by,"
        "       claimed_by IS NOT NULL AS onboarded"
        " FROM allowlist ORDER BY verified_at DESC"
    ).fetchall()


def lookup_allowlist(conn: sqlite3.Connection, phone: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM allowlist WHERE phone = ?", (normalise_phone(phone),)
    ).fetchone()


def get_user(conn: sqlite3.Connection, telegram_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    ).fetchone()


def register(conn: sqlite3.Connection, telegram_id: int, phone: str,
             lang: str = "am") -> sqlite3.Row:
    existing = get_user(conn, telegram_id)
    if existing is not None:
        return existing

    entry = lookup_allowlist(conn, phone)
    if entry is None:
        raise NotAllowlisted(phone)
    if entry["claimed_by"] is not None and entry["claimed_by"] != telegram_id:
        raise NotAllowlisted(phone)

    is_female = entry["is_female"]

    conn.execute(
        "INSERT INTO users"
        " (telegram_id, phone, full_name, tower, role, car_model, car_color, plate,"
        "  is_female, car_seats, created_at, lang)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (telegram_id, normalise_phone(phone), entry["full_name"], entry["tower"],
         entry["role"], entry["car_model"], entry["car_color"], entry["plate"],
         is_female, entry["car_seats"], clock.now().isoformat(timespec="seconds"), lang),
    )
    conn.execute("UPDATE allowlist SET claimed_by = ? WHERE phone = ?",
                 (telegram_id, normalise_phone(phone)))
    conn.commit()
    return get_user(conn, telegram_id)


def register_rider(conn: sqlite3.Connection, telegram_id: int, phone: str,
                   full_name: str, lang: str = "am") -> sqlite3.Row:
    """Self-registration for riders.

    Riders are NOT desk-verified — they arrive via the Telegram link (QR
    standees / HOA broadcast), so there is no allowlist check. Telegram supplies
    the name and phone; riders carry no tower (the tower trust signal is
    driver-side only). Drivers still go through register() against the allowlist.
    """
    existing = get_user(conn, telegram_id)
    if existing is not None:
        return existing
    conn.execute(
        "INSERT INTO users"
        " (telegram_id, phone, full_name, tower, role, created_at, lang)"
        " VALUES (?, ?, ?, '', 'rider', ?, ?)",
        (telegram_id, normalise_phone(phone), full_name,
         clock.now().isoformat(timespec="seconds"), lang),
    )
    conn.commit()
    return get_user(conn, telegram_id)


def set_consent(conn: sqlite3.Connection, telegram_id: int) -> None:
    """Record a one-time acknowledgement of the rules + data use."""
    conn.execute("UPDATE users SET consented_at = ? WHERE telegram_id = ?",
                 (clock.now().isoformat(timespec="seconds"), telegram_id))
    conn.commit()


def set_lang(conn: sqlite3.Connection, telegram_id: int, lang: str) -> None:
    """Persist the user's language ('am' or 'en'); drives both the bot and app."""
    conn.execute("UPDATE users SET lang = ? WHERE telegram_id = ?",
                 (lang if lang in ("am", "en") else "am", telegram_id))
    conn.commit()


def reconcile_role(conn: sqlite3.Connection, telegram_id: int) -> sqlite3.Row | None:
    """Promote a registered rider to driver if their phone is now on the driver
    allowlist. Registration happens once, but a rider can be desk-verified later
    (e.g. an admin adds them from Ops) — this catches up their role the next time
    they open the bot or the app. The allowlist is authoritative for drivers."""
    user = get_user(conn, telegram_id)
    if user is None or user["role"] == "driver":
        return user
    entry = lookup_allowlist(conn, user["phone"])
    if entry is None or entry["role"] != "driver":
        return user
    if entry["claimed_by"] not in (None, telegram_id):
        return user  # this driver slot belongs to another account
    conn.execute(
        "UPDATE users SET role='driver', tower=?, car_model=?, car_color=?, plate=?,"
        "  is_female=?, car_seats=? WHERE telegram_id=?",
        (entry["tower"], entry["car_model"], entry["car_color"], entry["plate"],
         entry["is_female"], entry["car_seats"], telegram_id),
    )
    conn.execute("UPDATE allowlist SET claimed_by=? WHERE phone=?",
                 (telegram_id, user["phone"]))
    conn.commit()
    return get_user(conn, telegram_id)


def set_women_only(conn: sqlite3.Connection, telegram_id: int,
                   women_only: bool, women_present: bool) -> None:
    conn.execute(
        "UPDATE users SET women_only = ?, women_present = ? WHERE telegram_id = ?",
        (int(women_only), int(women_present), telegram_id),
    )
    conn.commit()
