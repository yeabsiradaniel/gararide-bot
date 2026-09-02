"""SQLite schema and connection handling."""
from __future__ import annotations

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS places (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT NOT NULL UNIQUE,
    name_am     TEXT NOT NULL,
    name_en     TEXT NOT NULL,
    corridor_id INTEGER NOT NULL,
    sort_order  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fares (
    from_place_id INTEGER NOT NULL REFERENCES places(id),
    to_place_id   INTEGER NOT NULL REFERENCES places(id),
    birr          INTEGER NOT NULL,
    PRIMARY KEY (from_place_id, to_place_id)
);

-- Populated from the onboarding desk. Registration is impossible without a row here.
CREATE TABLE IF NOT EXISTS allowlist (
    phone       TEXT PRIMARY KEY,
    full_name   TEXT NOT NULL,
    tower       TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('driver', 'rider')),
    car_model   TEXT,
    plate       TEXT,
    is_female   INTEGER NOT NULL DEFAULT 0,
    car_seats   INTEGER,
    verified_at TEXT NOT NULL,
    claimed_by  INTEGER
);

CREATE TABLE IF NOT EXISTS users (
    telegram_id   INTEGER PRIMARY KEY,
    phone         TEXT NOT NULL UNIQUE,
    full_name     TEXT NOT NULL,
    tower         TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('driver', 'rider')),
    car_model     TEXT,
    plate         TEXT,
    photo_file_id TEXT,
    is_female     INTEGER NOT NULL DEFAULT 0,
    car_seats     INTEGER,
    women_only    INTEGER NOT NULL DEFAULT 0,
    women_present INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL,
    active        INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS trips (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id      INTEGER NOT NULL REFERENCES users(telegram_id),
    origin_place_id INTEGER NOT NULL REFERENCES places(id),
    dest_place_id  INTEGER NOT NULL REFERENCES places(id),
    depart_at      TEXT NOT NULL,
    seats_total    INTEGER NOT NULL,
    note           TEXT,
    status         TEXT NOT NULL DEFAULT 'open'
                   CHECK (status IN ('open', 'cancelled', 'done')),
    created_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_trips_depart ON trips(depart_at, status);

-- The driver's declared drop-offs. This IS the route (UX spec section 12).
CREATE TABLE IF NOT EXISTS trip_dropoffs (
    trip_id  INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    place_id INTEGER NOT NULL REFERENCES places(id),
    PRIMARY KEY (trip_id, place_id)
);

CREATE TABLE IF NOT EXISTS bookings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id       INTEGER NOT NULL REFERENCES trips(id),
    rider_id      INTEGER NOT NULL REFERENCES users(telegram_id),
    from_place_id INTEGER NOT NULL REFERENCES places(id),
    to_place_id   INTEGER NOT NULL REFERENCES places(id),
    fare          INTEGER NOT NULL,
    status        TEXT NOT NULL DEFAULT 'booked'
                  CHECK (status IN ('booked', 'cancelled', 'no_show', 'completed')),
    paid          INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_bookings_trip ON bookings(trip_id, status);

CREATE TABLE IF NOT EXISTS requests (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    rider_id      INTEGER NOT NULL REFERENCES users(telegram_id),
    origin_place_id INTEGER NOT NULL REFERENCES places(id),
    dest_place_id INTEGER NOT NULL REFERENCES places(id),
    window_start  TEXT NOT NULL,
    window_end    TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'open'
                  CHECK (status IN ('open', 'filled', 'expired', 'cancelled')),
    created_at    TEXT NOT NULL
);

-- The safety valve. Never shown to the blocked party (UX spec section 17).
CREATE TABLE IF NOT EXISTS blocks (
    blocker_id INTEGER NOT NULL REFERENCES users(telegram_id),
    blocked_id INTEGER NOT NULL REFERENCES users(telegram_id),
    created_at TEXT NOT NULL,
    PRIMARY KEY (blocker_id, blocked_id)
);

CREATE TABLE IF NOT EXISTS saved_trips (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(telegram_id),
    dest_place_id INTEGER NOT NULL REFERENCES places(id),
    depart_time   TEXT NOT NULL,
    days_mask     INTEGER NOT NULL,
    active        INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL
);

-- A driver's usual commute, saved for one-tap re-posting (never auto-posts).
CREATE TABLE IF NOT EXISTS driver_routes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id     INTEGER NOT NULL REFERENCES users(telegram_id),
    dest_place_id INTEGER NOT NULL REFERENCES places(id),
    dropoffs      TEXT NOT NULL DEFAULT '',   -- comma-separated place ids
    depart_time   TEXT NOT NULL,              -- 'HH:MM' local
    seats         INTEGER NOT NULL,
    days_mask     INTEGER NOT NULL DEFAULT 0, -- bit i set = weekday i (Mon=0)
    active        INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL
);

-- Every unmatched search is a driver-recruitment target (UX spec section 8).
CREATE TABLE IF NOT EXISTS search_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    rider_id      INTEGER NOT NULL,
    dest_place_id INTEGER NOT NULL REFERENCES places(id),
    window_start  TEXT NOT NULL,
    window_end    TEXT NOT NULL,
    results       INTEGER NOT NULL,
    created_at    TEXT NOT NULL
);
"""


def connect(path: str) -> sqlite3.Connection:
    # check_same_thread=False: the FastAPI layer serves requests from a thread
    # pool, so the shared connection is touched from worker threads. SQLite's
    # default serialized mode keeps that safe at the pilot's low volume.
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
