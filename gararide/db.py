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
    car_color   TEXT,
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
    car_color     TEXT,
    plate         TEXT,
    photo_file_id TEXT,
    is_female     INTEGER NOT NULL DEFAULT 0,
    car_seats     INTEGER,
    women_only    INTEGER NOT NULL DEFAULT 0,
    women_present INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL,
    active        INTEGER NOT NULL DEFAULT 1,
    lang          TEXT NOT NULL DEFAULT 'am',
    consented_at  TEXT
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
    arrived_at     TEXT,
    otw_at         TEXT,
    otw_eta        INTEGER,
    driver_reminded INTEGER NOT NULL DEFAULT 0,
    summary_sent   INTEGER NOT NULL DEFAULT 0,
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
    reminded      INTEGER NOT NULL DEFAULT 0,
    rate_prompted INTEGER NOT NULL DEFAULT 0,
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

-- A reasoned report that reaches an admin (unlike the silent block above).
-- The reported party is never told. Admins triage and resolve.
CREATE TABLE IF NOT EXISTS reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    reporter_id INTEGER NOT NULL REFERENCES users(telegram_id),
    reported_id INTEGER NOT NULL REFERENCES users(telegram_id),
    trip_id     INTEGER REFERENCES trips(id),
    reason      TEXT NOT NULL,
    note        TEXT,
    status      TEXT NOT NULL DEFAULT 'open'
                CHECK (status IN ('open', 'resolved')),
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status, created_at);

-- A thumbs up/down left by a rider after a completed ride. ADMIN-ONLY signal:
-- never shown to the rated driver, and no driver aggregate is shown to riders.
-- One rating per booking; re-rating overwrites.
CREATE TABLE IF NOT EXISTS ratings (
    booking_id INTEGER PRIMARY KEY REFERENCES bookings(id),
    rater_id   INTEGER NOT NULL REFERENCES users(telegram_id),
    ratee_id   INTEGER NOT NULL REFERENCES users(telegram_id),
    value      INTEGER NOT NULL CHECK (value IN (-1, 1)),
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ratings_ratee ON ratings(ratee_id);

-- Riders waiting for a seat on a full trip. When a seat frees they're pinged.
CREATE TABLE IF NOT EXISTS waitlist (
    trip_id     INTEGER NOT NULL REFERENCES trips(id),
    rider_id    INTEGER NOT NULL REFERENCES users(telegram_id),
    to_place_id INTEGER NOT NULL REFERENCES places(id),
    created_at  TEXT NOT NULL,
    PRIMARY KEY (trip_id, rider_id)
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
    # WAL lets readers and a writer coexist; busy_timeout makes a writer wait for
    # a lock instead of erroring. Each request gets its own connection (deps.py),
    # so connections are never used from two threads at once.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.commit()


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns to tables that predate them (CREATE TABLE IF NOT EXISTS never
    alters an existing table)."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
    if "lang" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN lang TEXT NOT NULL DEFAULT 'am'")
    bcols = {r[1] for r in conn.execute("PRAGMA table_info(bookings)")}
    if "reminded" not in bcols:
        conn.execute("ALTER TABLE bookings ADD COLUMN reminded INTEGER NOT NULL DEFAULT 0")
    tcols = {r[1] for r in conn.execute("PRAGMA table_info(trips)")}
    if "arrived_at" not in tcols:
        conn.execute("ALTER TABLE trips ADD COLUMN arrived_at TEXT")
    if "otw_at" not in tcols:
        conn.execute("ALTER TABLE trips ADD COLUMN otw_at TEXT")       # 'on my way' stamp
    if "otw_eta" not in tcols:
        conn.execute("ALTER TABLE trips ADD COLUMN otw_eta INTEGER")   # minutes to pickup
    if "driver_reminded" not in tcols:
        conn.execute("ALTER TABLE trips ADD COLUMN driver_reminded INTEGER NOT NULL DEFAULT 0")
    if "summary_sent" not in tcols:
        conn.execute("ALTER TABLE trips ADD COLUMN summary_sent INTEGER NOT NULL DEFAULT 0")
    if "rate_prompted" not in bcols:
        conn.execute("ALTER TABLE bookings ADD COLUMN rate_prompted INTEGER NOT NULL DEFAULT 0")
    if "car_color" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN car_color TEXT")
    if "consented_at" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN consented_at TEXT")
    acols = {r[1] for r in conn.execute("PRAGMA table_info(allowlist)")}
    if "car_color" not in acols:
        conn.execute("ALTER TABLE allowlist ADD COLUMN car_color TEXT")
