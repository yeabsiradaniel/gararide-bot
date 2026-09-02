# Gara Ride Mini App — Backend Plan (Plan 1 of 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing, tested `gararide/` domain core into a FastAPI JSON API (authenticated by Telegram Mini App `initData`), apply the four pilot-feedback fixes, and slim the bot to a launcher + notifications — so the React Mini App (Plan 2) has a working, tested backend to build against.

**Architecture:** Reuse every `gararide/` module unchanged except four small logic additions. Add a thin FastAPI layer (`gararide/api/`) that validates `initData`, resolves the caller's `telegram_id`, and calls the domain functions with `conn` as it always has. Same SQLite DB. The bot keeps only registration, a Mini-App launch button, and push notifications.

**Tech Stack:** Python 3.12+ (running on 3.14), FastAPI, uvicorn, `python-telegram-bot[job-queue]>=21,<22`, SQLite (stdlib), pytest, pytest-asyncio, FastAPI `TestClient` (httpx).

**Source specs (read first):**
- `docs/superpowers/specs/2026-09-02-gararide-miniapp-design.md` — the design. Section references (§3, §5, …) point at it.
- `gararide/` — the reused domain core. Do not change its public function signatures except where a task says so.

## Global Constraints

- **New API code lives in `gararide/api/`.** Domain logic stays in `gararide/` top-level modules; the API layer never re-implements business rules, it only calls them. (spec §2)
- **Every endpoint is authenticated by Telegram `initData`.** No endpoint trusts a `telegram_id` from the request body; identity comes only from the validated `initData`. (spec §2)
- **Pilot restrictions live only in `gararide/config.py` or seed data.** (unchanged from the original build)
- **Every trip/search/booking response embeds the fare.** Price on every view, both sides. (spec §4)
- **A user's tower is returned for drivers only.** Riders self-register without a tower; never fabricate one. (spec §3)
- **The four domain changes (§3) are the ONLY changes to business logic.** No other behavioural change to matching, fares, or bookings.
- **Amharic strings stay in `gararide/strings_am.py`.** The API returns data, not user-facing prose; any prose belongs to the frontend (Plan 2).
- **Python 3.12+**, `fastapi` and `uvicorn` pinned in `requirements.txt`.
- **Commit after every task.** Conventional commits (`feat:`, `test:`, `fix:`, `chore:`). End each commit body with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- **All timestamps are naive local time (EAT).** No timezone conversion anywhere.

---

## Task 1: Car seat capacity (domain change §3.1)

**Files:**
- Modify: `gararide/db.py` (add `car_seats` to `allowlist` and `users`)
- Modify: `gararide/users.py` (import + register copy `car_seats`)
- Modify: `seed/allowlist_template.csv`, `seed/allowlist_test.csv`
- Test: `tests/test_users.py`

**Interfaces:**
- Consumes: existing `import_allowlist`, `register`, `register_rider`.
- Produces: `users` and `allowlist` rows carry `car_seats INTEGER` (drivers: their car's passenger capacity; riders: `NULL`). Later tasks read `user["car_seats"]` to bound the seat picker.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_users.py`:

```python
def test_allowlist_and_register_carry_car_seats(conn):
    import_allowlist(conn, "seed/allowlist_template.csv")
    entry = lookup_allowlist(conn, "0911223344")
    assert entry["car_seats"] == 4
    user = register(conn, telegram_id=1001, phone="0911223344")
    assert user["car_seats"] == 4


def test_self_registered_rider_has_no_car_seats(conn):
    user = register_rider(conn, telegram_id=2001, phone="0933445566",
                          full_name="Fan")
    assert user["car_seats"] is None
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_users.py -k car_seats -v`
Expected: FAIL (`KeyError: 'car_seats'` / no such column).

- [ ] **Step 3: Add the column to the schema**

In `gararide/db.py`, in the `allowlist` table add after `is_female ...`:
```
    car_seats   INTEGER,
```
In the `users` table add after `is_female ...`:
```
    car_seats     INTEGER,
```

- [ ] **Step 4: Carry it through `users.py`**

In `import_allowlist`, add `car_seats` to the INSERT column list, values, and the `ON CONFLICT ... DO UPDATE SET`, reading `int(row["car_seats"]) if row.get("car_seats") else None`.
In `register`, add `entry["car_seats"]` to the users INSERT (new `car_seats` column).
`register_rider` inserts no `car_seats` (defaults to NULL) — no change needed beyond the column existing.

- [ ] **Step 5: Add the column to the seed CSVs**

`seed/allowlist_template.csv` header becomes:
```
phone,full_name,tower,role,car_model,plate,is_female,car_seats
0911223344,አበበ ከበደ,B4,driver,Toyota Corolla,3-AA 21457,0,4
0912334455,ሜሮን አለሙ,A2,rider,,,1,
```
`seed/allowlist_test.csv` (local, gitignored — edit if present): add `,4` to the driver row and a trailing `,car_seats` header column.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest tests/test_users.py -v`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add gararide/db.py gararide/users.py seed/ tests/test_users.py
git commit -m "feat: record car seat capacity for drivers"
```

---

## Task 2: Exclude the searcher's own trips (domain change §3.2)

**Files:**
- Modify: `gararide/matching.py` (`find_trips`, `near_misses`)
- Test: `tests/test_matching.py`

**Interfaces:**
- Consumes: existing `find_trips`, `near_misses` signatures (unchanged).
- Produces: neither function ever returns a trip whose `driver_id == rider_id`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_matching.py`:

```python
def test_a_driver_searching_never_sees_their_own_trip(corridor):
    conn, driver, rider, ids = corridor
    post_trip(conn, driver_id=driver["telegram_id"], dest_place_id=ids["kazanchis"],
              dropoff_place_ids=[ids["kazanchis"]], depart_at=_at(7), seats=3)
    # The driver themselves searches as a rider.
    assert find_trips(conn, rider_id=driver["telegram_id"],
                      dest_place_id=ids["kazanchis"],
                      window_start=_at(6, 30), window_end=_at(7, 30)) == []
    assert near_misses(conn, rider_id=driver["telegram_id"],
                       dest_place_id=ids["kazanchis"],
                       window_start=_at(6, 30), window_end=_at(7, 30)) == []
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_matching.py -k own_trip -v`
Expected: FAIL (the driver's own trip is returned).

- [ ] **Step 3: Implement the exclusion**

In `matching.py`, in the `_permitted` helper add as the first check:
```python
    if trip["driver_id"] == rider["telegram_id"]:
        return False
```
(`_permitted` already receives `rider`; `rider["telegram_id"]` is available. Both `find_trips` and `near_misses` route through `_permitted`, so one change covers both.)

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_matching.py -v`
Expected: all pass (16 tests).

- [ ] **Step 5: Commit**

```bash
git add gararide/matching.py tests/test_matching.py
git commit -m "feat: a driver never matches their own trip when riding"
```

---

## Task 3: Drop-off options exclude the destination (domain change §3.3)

**Files:**
- Modify: `gararide/trips.py` (add `intermediate_dropoffs`)
- Test: `tests/test_trips.py`

**Interfaces:**
- Consumes: existing `default_dropoffs`, `place_by_id`, `origin_place`, `all_places`.
- Produces: `intermediate_dropoffs(conn, dest_place_id) -> list[int]` — the stops strictly between origin and destination (destination excluded). The frontend renders these as the toggleable checklist; the destination is shown separately and always booked. `post_trip` is unchanged (it still auto-adds the destination).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_trips.py`:

```python
from gararide.trips import intermediate_dropoffs

def test_intermediate_dropoffs_exclude_the_destination(people):
    conn, _, _ = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    got = [conn.execute("SELECT slug FROM places WHERE id=?", (i,)).fetchone()["slug"]
           for i in intermediate_dropoffs(conn, kaz)]
    assert got == ["cmc", "megenagna", "aratkilo"]   # kazanchis excluded


def test_intermediate_dropoffs_empty_for_the_nearest_stop(people):
    conn, _, _ = people
    cmc = place_by_slug(conn, "cmc")["id"]
    assert intermediate_dropoffs(conn, cmc) == []
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_trips.py -k intermediate -v`
Expected: FAIL (`ImportError`/not defined).

- [ ] **Step 3: Implement it**

In `gararide/trips.py`:
```python
def intermediate_dropoffs(conn: sqlite3.Connection, dest_place_id: int) -> list[int]:
    """Stops strictly between origin and destination (destination excluded).

    The destination is always a drop-off, so it is not shown as a toggle in the
    checklist — the UI renders it as a fixed "-> destination" label instead.
    """
    dest = place_by_id(conn, dest_place_id)
    origin = origin_place(conn)
    lo, hi = sorted((origin["sort_order"], dest["sort_order"]))
    return [p["id"] for p in all_places(conn, CONFIG.corridor_id)
            if lo < p["sort_order"] < hi]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_trips.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add gararide/trips.py tests/test_trips.py
git commit -m "feat: intermediate drop-off list excludes the destination"
```

---

## Task 4: Saved trips and the daily confirm (domain change §3.4)

**Files:**
- Create: `gararide/saved.py`
- Test: `tests/test_saved.py`

**Interfaces:**
- Consumes: existing `saved_trips` table (from `db.py`), `CONFIG.save_prompt_threshold`, `bookings`/`trips` tables.
- Produces:
  - `should_offer_save(conn, user_id, dest_place_id, depart_time) -> bool` — True once the rider has taken this dest+time `save_prompt_threshold` times and has not already saved it.
  - `save_trip(conn, *, user_id, dest_place_id, depart_time, days_mask) -> int`
  - `saved_for(conn, user_id) -> list[sqlite3.Row]`
  - `deactivate_saved(conn, saved_id) -> None`

- [ ] **Step 1: Write the failing test**

Create `tests/test_saved.py`:

```python
from datetime import datetime, timedelta
import pytest
from gararide.bookings import book
from gararide.places import place_by_slug
from gararide.saved import (deactivate_saved, save_trip, saved_for,
                            should_offer_save)
from gararide.trips import post_trip


def _book_kaz(conn, driver_id, rider_id, kaz, days):
    depart = (datetime.now() + timedelta(days=days)).replace(
        hour=7, minute=0, second=0, microsecond=0)
    tid = post_trip(conn, driver_id=driver_id, dest_place_id=kaz,
                    dropoff_place_ids=[kaz], depart_at=depart, seats=3)
    book(conn, trip_id=tid, rider_id=rider_id, to_place_id=kaz)


def test_offer_save_after_threshold_identical_trips(people):
    conn, driver, rider = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    for d in range(1, 4):
        _book_kaz(conn, driver["telegram_id"], rider["telegram_id"], kaz, d)
    assert should_offer_save(conn, rider["telegram_id"], kaz, "07:00") is False
    _book_kaz(conn, driver["telegram_id"], rider["telegram_id"], kaz, 4)
    assert should_offer_save(conn, rider["telegram_id"], kaz, "07:00") is True


def test_save_and_list_and_deactivate(people):
    conn, _, rider = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    sid = save_trip(conn, user_id=rider["telegram_id"], dest_place_id=kaz,
                    depart_time="07:00", days_mask=0b0011111)
    rows = saved_for(conn, rider["telegram_id"])
    assert len(rows) == 1 and rows[0]["depart_time"] == "07:00"
    deactivate_saved(conn, sid)
    assert saved_for(conn, rider["telegram_id"]) == []


def test_already_saved_is_not_offered_again(people):
    conn, driver, rider = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    for d in range(1, 5):
        _book_kaz(conn, driver["telegram_id"], rider["telegram_id"], kaz, d)
    save_trip(conn, user_id=rider["telegram_id"], dest_place_id=kaz,
              depart_time="07:00", days_mask=0b0011111)
    assert should_offer_save(conn, rider["telegram_id"], kaz, "07:00") is False
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_saved.py -v`
Expected: FAIL (`ModuleNotFoundError: gararide.saved`).

- [ ] **Step 3: Create `gararide/saved.py`**

```python
"""Saved trips — the convenience layer over the same trip object (spec §3.4).

A commute is just a trip taken repeatedly. After enough identical bookings we
offer to save it; a saved trip is a one-tap repeat, never an auto-booking.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime

from .config import CONFIG


def _times_taken(conn: sqlite3.Connection, user_id: int, dest_place_id: int,
                 depart_time: str) -> int:
    return conn.execute(
        "SELECT COUNT(*) AS c FROM bookings b JOIN trips t ON t.id = b.trip_id"
        " WHERE b.rider_id = ? AND b.to_place_id = ?"
        "   AND substr(t.depart_at, 12, 5) = ?"
        "   AND b.status IN ('booked', 'completed')",
        (user_id, dest_place_id, depart_time),
    ).fetchone()["c"]


def _already_saved(conn: sqlite3.Connection, user_id: int, dest_place_id: int,
                   depart_time: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM saved_trips WHERE user_id = ? AND dest_place_id = ?"
        "   AND depart_time = ? AND active = 1",
        (user_id, dest_place_id, depart_time),
    ).fetchone() is not None


def should_offer_save(conn: sqlite3.Connection, user_id: int, dest_place_id: int,
                      depart_time: str) -> bool:
    if _already_saved(conn, user_id, dest_place_id, depart_time):
        return False
    return _times_taken(conn, user_id, dest_place_id, depart_time) >= \
        CONFIG.save_prompt_threshold


def save_trip(conn: sqlite3.Connection, *, user_id: int, dest_place_id: int,
             depart_time: str, days_mask: int) -> int:
    cur = conn.execute(
        "INSERT INTO saved_trips (user_id, dest_place_id, depart_time, days_mask,"
        " created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, dest_place_id, depart_time, days_mask,
         datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    return cur.lastrowid


def saved_for(conn: sqlite3.Connection, user_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM saved_trips WHERE user_id = ? AND active = 1"
        " ORDER BY depart_time",
        (user_id,),
    ).fetchall()


def deactivate_saved(conn: sqlite3.Connection, saved_id: int) -> None:
    conn.execute("UPDATE saved_trips SET active = 0 WHERE id = ?", (saved_id,))
    conn.commit()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_saved.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gararide/saved.py tests/test_saved.py
git commit -m "feat: saved trips and the repeat-trip threshold"
```

---

## Task 5: FastAPI skeleton, initData auth, and reference endpoints

**Files:**
- Create: `gararide/api/__init__.py`, `gararide/api/auth.py`, `gararide/api/app.py`, `gararide/api/deps.py`, `gararide/api/schemas.py`
- Modify: `requirements.txt`
- Test: `tests/test_api_auth.py`, `tests/test_api_reference.py`

**Interfaces:**
- Consumes: `db.connect`, `db.init_schema`, `places.*`, `users.get_user`.
- Produces:
  - `auth.parse_init_data(raw: str, bot_token: str) -> dict` — validates the HMAC and returns the parsed `user` dict, or raises `auth.InvalidInitData`.
  - `deps.current_user` — FastAPI dependency yielding the authenticated `users` row (or 404 if not registered) plus the request-scoped `conn`.
  - `app.create_app(conn, bot_token) -> FastAPI` — the application factory used by tests and the server.
  - Endpoints: `GET /me`, `GET /places`.

- [ ] **Step 1: Add dependencies**

`requirements.txt` gains:
```
fastapi>=0.115,<1
uvicorn[standard]>=0.30,<1
```
Install: `pip install -r requirements.txt`.

- [ ] **Step 2: Write the failing auth test**

Create `tests/test_api_auth.py`:

```python
import hashlib, hmac, json, time
from urllib.parse import urlencode
import pytest
from gararide.api.auth import InvalidInitData, parse_init_data

BOT_TOKEN = "123456:TEST"


def make_init_data(user: dict, token: str = BOT_TOKEN) -> str:
    fields = {"auth_date": str(int(time.time())),
              "user": json.dumps(user, separators=(",", ":"))}
    data_check = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def test_valid_init_data_returns_the_user():
    raw = make_init_data({"id": 1001, "first_name": "Yeab"})
    assert parse_init_data(raw, BOT_TOKEN)["id"] == 1001


def test_tampered_hash_is_rejected():
    raw = make_init_data({"id": 1001}) + "&extra=1"
    with pytest.raises(InvalidInitData):
        parse_init_data(raw, BOT_TOKEN)


def test_wrong_token_is_rejected():
    raw = make_init_data({"id": 1001}, token="other")
    with pytest.raises(InvalidInitData):
        parse_init_data(raw, BOT_TOKEN)
```

- [ ] **Step 3: Run it to verify it fails**

Run: `python -m pytest tests/test_api_auth.py -v`
Expected: FAIL (`ModuleNotFoundError: gararide.api.auth`).

- [ ] **Step 4: Implement `gararide/api/auth.py`**

```python
"""Telegram Mini App initData validation.

The Mini App sends Telegram.WebApp.initData with every request. It is a signed
query string; we recompute the HMAC with the bot token and compare. Identity is
NEVER taken from the request body — only from validated initData (spec §2).
Ref: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
from __future__ import annotations

import hashlib
import hmac
import json
from urllib.parse import parse_qsl


class InvalidInitData(Exception):
    """The initData signature did not validate against the bot token."""


def parse_init_data(raw: str, bot_token: str) -> dict:
    pairs = dict(parse_qsl(raw, keep_blank_values=True))
    received = pairs.pop("hash", None)
    if received is None:
        raise InvalidInitData("no hash")
    data_check = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise InvalidInitData("bad hash")
    user_raw = pairs.get("user")
    if not user_raw:
        raise InvalidInitData("no user")
    return json.loads(user_raw)
```

- [ ] **Step 5: Implement `gararide/api/deps.py`, `schemas.py`, `app.py`**

`gararide/api/deps.py`:
```python
"""Request-scoped dependencies: the authenticated user and the DB connection."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request

from ..users import get_user
from .auth import InvalidInitData, parse_init_data


def get_conn(request: Request):
    return request.app.state.conn


def current_user(request: Request,
                 authorization: str | None = Header(default=None),
                 conn=Depends(get_conn)):
    """Validate initData from the Authorization header ('tma <initData>')."""
    if not authorization or not authorization.startswith("tma "):
        raise HTTPException(status_code=401, detail="missing initData")
    try:
        tg = parse_init_data(authorization[4:], request.app.state.bot_token)
    except InvalidInitData:
        raise HTTPException(status_code=401, detail="invalid initData")
    user = get_user(conn, tg["id"])
    if user is None:
        raise HTTPException(status_code=404, detail="not registered")
    return user
```

`gararide/api/schemas.py`:
```python
"""Response shapes. Drivers expose tower; riders never do (spec §3)."""
from __future__ import annotations

from pydantic import BaseModel


class Me(BaseModel):
    telegram_id: int
    full_name: str
    role: str
    tower: str | None
    car_model: str | None
    plate: str | None
    car_seats: int | None
    women_only: bool
    women_present: bool


class Place(BaseModel):
    id: int
    slug: str
    name_am: str
    name_en: str
    sort_order: int
```

`gararide/api/app.py`:
```python
"""FastAPI application factory."""
from __future__ import annotations

from fastapi import Depends, FastAPI

from ..places import all_places
from ..config import CONFIG
from .deps import current_user, get_conn
from .schemas import Me, Place


def create_app(conn, bot_token: str) -> FastAPI:
    app = FastAPI(title="Gara Ride API")
    app.state.conn = conn
    app.state.bot_token = bot_token

    @app.get("/me", response_model=Me)
    def me(user=Depends(current_user)):
        return Me(
            telegram_id=user["telegram_id"], full_name=user["full_name"],
            role=user["role"], tower=user["tower"] if user["role"] == "driver" else None,
            car_model=user["car_model"], plate=user["plate"],
            car_seats=user["car_seats"], women_only=bool(user["women_only"]),
            women_present=bool(user["women_present"]))

    @app.get("/places", response_model=list[Place])
    def places(user=Depends(current_user), conn=Depends(get_conn)):
        return [Place(id=p["id"], slug=p["slug"], name_am=p["name_am"],
                      name_en=p["name_en"], sort_order=p["sort_order"])
                for p in all_places(conn, CONFIG.corridor_id)]

    return app
```

`gararide/api/__init__.py`:
```python
"""FastAPI layer over the domain core. Business rules live in gararide/, not here."""
```

- [ ] **Step 6: Write the reference-endpoint test**

Create `tests/test_api_reference.py`:

```python
import pytest
from fastapi.testclient import TestClient
from gararide.api.app import create_app
from gararide.users import import_allowlist, register, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def client(seeded):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register(seeded, telegram_id=1001, phone="0911223344")       # driver
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    return TestClient(create_app(seeded, BOT_TOKEN))


def _auth(user):
    return {"Authorization": "tma " + make_init_data(user)}


def test_me_returns_driver_with_tower(client):
    r = client.get("/me", headers=_auth({"id": 1001, "first_name": "Yeab"}))
    assert r.status_code == 200
    assert r.json()["role"] == "driver"
    assert r.json()["tower"] == "B4"
    assert r.json()["car_seats"] == 4


def test_me_hides_tower_for_riders(client):
    r = client.get("/me", headers=_auth({"id": 2001, "first_name": "Fan"}))
    assert r.json()["role"] == "rider"
    assert r.json()["tower"] is None


def test_unregistered_user_gets_404(client):
    r = client.get("/me", headers=_auth({"id": 9999, "first_name": "Nobody"}))
    assert r.status_code == 404


def test_missing_initdata_is_401(client):
    assert client.get("/me").status_code == 401


def test_places_lists_the_corridor(client):
    r = client.get("/places", headers=_auth({"id": 1001}))
    assert [p["slug"] for p in r.json()] == \
        ["ayat49", "cmc", "megenagna", "aratkilo", "kazanchis"]
```

- [ ] **Step 7: Run the API tests to verify they pass**

Run: `python -m pytest tests/test_api_auth.py tests/test_api_reference.py -v`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add gararide/api/ requirements.txt tests/test_api_auth.py tests/test_api_reference.py
git commit -m "feat: FastAPI skeleton with initData auth, /me and /places"
```

---

## Task 6: Driver endpoints

**Files:**
- Create: `gararide/api/driver.py` (an `APIRouter`)
- Modify: `gararide/api/app.py` (include the router), `gararide/api/schemas.py`
- Test: `tests/test_api_driver.py`

**Interfaces:**
- Consumes: `current_user`, `get_conn`; `trips.post_trip`, `trips.intermediate_dropoffs`, `trips.trips_by_driver`, `trips.dropoffs`, `trips.cancel_trip`, `trips.seats_left`; `bookings.bookings_for_trip`, `bookings.mark_paid`, `bookings.mark_no_show`; `requests.open_requests`; `fares.fare`; `places.origin_place`, `places.place_by_id`; `users.get_user`.
- Produces these endpoints (all require a **driver** `current_user`; a rider calling them gets 403):
  - `GET /trips/{dest_id}/dropoff-options` → `{intermediate: [Place], destination: Place}`
  - `POST /trips` body `{dest_place_id, dropoff_place_ids, depart_at (ISO), seats, note?}` → the created trip with per-stop fares. **`seats` must be `1..car_seats`** (422 otherwise).
  - `GET /trips/mine` → list of `{id, dest, depart_at, seats_total, seats_left, passengers:[{name, tower, to, fare, phone, paid}]}`
  - `POST /trips/{id}/cancel` → 204
  - `GET /requests/near` → open requests (blocked riders filtered), each `{rider_name, dest, window_start}`
  - `POST /bookings/{id}/paid`, `POST /bookings/{id}/no-show` → 204

- [ ] **Step 1: Write the failing test**

Create `tests/test_api_driver.py` covering: dropoff-options excludes the destination; posting with `seats > car_seats` is 422; posting valid returns per-stop fares; `GET /trips/mine` shows a booked passenger with fare and phone; a rider calling `POST /trips` gets 403. (Use the `client` fixture pattern and `_auth` from Task 5. Full test code:)

```python
import pytest
from fastapi.testclient import TestClient
from gararide.api.app import create_app
from gararide.places import place_by_slug
from gararide.users import import_allowlist, register, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data
from datetime import datetime, timedelta


@pytest.fixture
def client(seeded):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register(seeded, telegram_id=1001, phone="0911223344")
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    return seeded, TestClient(create_app(seeded, BOT_TOKEN))


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def _tomorrow_7():
    return (datetime.now() + timedelta(days=1)).replace(
        hour=7, minute=0, second=0, microsecond=0).isoformat(timespec="seconds")


def test_dropoff_options_exclude_destination(client):
    conn, c = client
    kaz = place_by_slug(conn, "kazanchis")["id"]
    r = c.get(f"/trips/{kaz}/dropoff-options", headers=_auth(1001))
    assert [p["slug"] for p in r.json()["intermediate"]] == ["cmc", "megenagna", "aratkilo"]
    assert r.json()["destination"]["slug"] == "kazanchis"


def test_post_trip_rejects_more_seats_than_car(client):
    conn, c = client
    kaz = place_by_slug(conn, "kazanchis")["id"]
    r = c.post("/trips", headers=_auth(1001), json={
        "dest_place_id": kaz, "dropoff_place_ids": [kaz],
        "depart_at": _tomorrow_7(), "seats": 5})   # car_seats == 4
    assert r.status_code == 422


def test_post_trip_returns_per_stop_fares(client):
    conn, c = client
    kaz = place_by_slug(conn, "kazanchis")["id"]
    meg = place_by_slug(conn, "megenagna")["id"]
    r = c.post("/trips", headers=_auth(1001), json={
        "dest_place_id": kaz, "dropoff_place_ids": [meg, kaz],
        "depart_at": _tomorrow_7(), "seats": 3})
    assert r.status_code == 201
    fares = {f["slug"]: f["fare"] for f in r.json()["fares"]}
    assert fares["megenagna"] == 55 and fares["kazanchis"] == 85


def test_a_rider_cannot_post_a_trip(client):
    conn, c = client
    kaz = place_by_slug(conn, "kazanchis")["id"]
    r = c.post("/trips", headers=_auth(2001), json={
        "dest_place_id": kaz, "dropoff_place_ids": [kaz],
        "depart_at": _tomorrow_7(), "seats": 1})
    assert r.status_code == 403
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_api_driver.py -v`
Expected: FAIL (router not present → 404s).

- [ ] **Step 3: Implement `gararide/api/driver.py`**

Create an `APIRouter`. Add a `require_driver` dependency that calls `current_user` and raises `HTTPException(403)` if `user["role"] != "driver"`. Implement each endpoint by calling the domain functions listed in Interfaces. Key rules to encode:
- `POST /trips`: validate `1 <= seats <= (user["car_seats"] or 0)`; on violation `raise HTTPException(422)`. Parse `depart_at` with `datetime.fromisoformat`. Call `post_trip(...)`. Build the `fares` list from `dropoffs(conn, trip_id)` and `fare(conn, origin_id, stop_id)`. Return status 201.
- `GET /trips/{dest_id}/dropoff-options`: `intermediate_dropoffs` + the destination `place_by_id`.
- `GET /trips/mine`: `trips_by_driver`, and per trip `bookings_for_trip` joined to `get_user` for passenger name/tower/phone.
- `POST /trips/{id}/cancel`: `cancel_trip`, return 204.
- `GET /requests/near`: `open_requests(conn, for_driver_id=user["telegram_id"])`.
- `POST /bookings/{id}/paid` and `/no-show`: `mark_paid` / `mark_no_show`, return 204.

Wire the router in `app.py` with `app.include_router(driver.router)` after building `app`, passing dependencies via `Depends`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_api_driver.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add gararide/api/ tests/test_api_driver.py
git commit -m "feat: driver API endpoints (post trip, my trips, requests, cancel, paid/no-show)"
```

---

## Task 7: Rider endpoints

**Files:**
- Create: `gararide/api/rider.py`
- Modify: `gararide/api/app.py`, `gararide/api/schemas.py`
- Test: `tests/test_api_rider.py`

**Interfaces:**
- Consumes: `matching.find_trips`, `matching.near_misses`; `bookings.book`, `bookings.cancel_booking`, `bookings.bookings_for_rider`; `requests.post_request`, `requests.demand_count`; `blocks.block`; `users.set_women_only`, `users.get_user`; `trips.get_trip`; `fares.fare`; `places.*`. The search endpoint also writes a `search_log` row (spec §5 / admin recruitment list).
- Produces (all require a `current_user`; role-agnostic — a driver may ride):
  - `GET /trips/search?dest_place_id=&when=tomorrow_morning|today|weekend` → `{matches:[{trip_id, driver_name, depart_at, seats_left, fare}], near_misses:[{trip_id, driver_name, depart_at, fare, dest, reason}], demand_count}` — **never a bare empty list; always includes near_misses + demand_count** (spec §5).
  - `POST /bookings` body `{trip_id, to_place_id}` → the trip card payload (driver name/tower/car/plate/phone, fare, both clock-source fields). Raises 409 on `TripFull`/`NotOffered`.
  - `POST /bookings/{id}/cancel` → 204
  - `GET /bookings/mine` → rider's upcoming bookings with fares
  - `POST /requests` body `{dest_place_id, window_start, window_end}` → 201
  - `POST /blocks` body `{trip_id}` → 204 (silent safety valve — never reveals to the driver)
  - `POST /me/women-only` body `{women_only, women_present}` → 204

- [ ] **Step 1: Write the failing test**

Create `tests/test_api_rider.py` covering: a search with a matching trip returns it with fare 55; a search with no exact match returns `matches: []` but non-empty `near_misses` and a `demand_count`; booking returns the driver's phone + tower; booking a declined stop is 409; `POST /blocks` returns 204 and the blocked driver then disappears from search. (Write full test code following the `client` fixture + `_auth` pattern from Task 6, seeding a driver trip via the driver API or `trips.post_trip` directly.)

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_api_rider.py -v`
Expected: FAIL (router not present).

- [ ] **Step 3: Implement `gararide/api/rider.py`**

Map `when` to a window: `tomorrow_morning` → tomorrow 06:00–09:00; `today` → now→today 23:59; `weekend` → next Sat 00:00–Sun 23:59. Call `find_trips`; write the `search_log` row (`rider_id, dest_place_id, window_start, window_end, results=len(matches), created_at`). If matches empty, also compute `near_misses` (cap 4) and `demand_count`. `POST /bookings` calls `book(...)`, catches `TripFull`/`NotOffered` → 409, and returns the trip-card payload built from `get_trip` + `get_user(driver)` + `fare`. `POST /blocks` calls `block(conn, user_id, trip["driver_id"])`. `POST /me/women-only` calls `set_women_only`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_api_rider.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add gararide/api/ tests/test_api_rider.py
git commit -m "feat: rider API endpoints (search, book, request, block, women-only)"
```

---

## Task 8: Saved-trip and admin endpoints

**Files:**
- Create: `gararide/api/saved.py`, `gararide/api/admin.py`
- Modify: `gararide/api/app.py`
- Test: `tests/test_api_saved.py`, `tests/test_api_admin.py`

**Interfaces:**
- Consumes: `saved.*`; `config.ADMIN_IDS`; the admin SQL from `handlers/admin.py` (today's ops counts, unmatched searches), `users.import_allowlist`.
- Produces:
  - `GET /me/saved` → the rider's saved trips; `POST /me/saved` `{dest_place_id, depart_time, days_mask}` → 201; `POST /me/saved/{id}/deactivate` → 204.
  - `GET /admin/ops` (admin only, else 403) → `{trips, seats, no_shows, open_requests, users}`; `GET /admin/unmatched` → list of `{dest_name, riders}`. Admin membership checked against `CONFIG`-style `ADMIN_IDS` from `config`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_api_saved.py` and `tests/test_api_admin.py`. For admin, monkeypatch/inject `ADMIN_IDS` to include `1001` (set `app.state.admin_ids`), assert a non-admin gets 403 and an admin gets the five ops counts. For saved, assert POST then GET round-trips and deactivate empties the list.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/test_api_saved.py tests/test_api_admin.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement the routers**

`saved.py`: thin wrappers over `saved.saved_for`, `saved.save_trip`, `saved.deactivate_saved`.
`admin.py`: a `require_admin` dependency checking `user["telegram_id"] in request.app.state.admin_ids`; reuse the exact ops SQL and the unmatched-searches SQL from `handlers/admin.py`. Set `app.state.admin_ids = CONFIG-derived set` in `create_app` (pass `admin_ids` as a `create_app` argument, default `frozenset()`).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_api_saved.py tests/test_api_admin.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add gararide/api/ tests/test_api_saved.py tests/test_api_admin.py
git commit -m "feat: saved-trip and admin API endpoints"
```

---

## Task 9: Slim the bot to launcher + notifications

**Files:**
- Modify: `gararide/bot.py`, `gararide/handlers/home.py`, `gararide/handlers/onboarding.py`
- Delete: `gararide/handlers/driver.py`, `gararide/handlers/rider.py`, `gararide/keyboards.py` (and their tests `tests/test_keyboards.py`)
- Create: `gararide/handlers/launch.py`
- Test: manual (bot) + `python -m pytest` stays green

**Interfaces:**
- Consumes: `WEBAPP_URL` env var (the deployed Mini App URL).
- Produces: after registration (and on `/start` for a registered user), the bot shows a single inline button that opens the Mini App via `web_app=WebAppInfo(url=WEBAPP_URL)`. The keyboard-driven flows are gone. Notifications (`notify`, `scheduler`) are unchanged.

- [ ] **Step 1: Create `gararide/handlers/launch.py`**

A `show_launch(update, context)` that replies with one `InlineKeyboardButton("Open Gara Ride 🚗", web_app=WebAppInfo(url=os.environ["WEBAPP_URL"]))` and a short Amharic line from `strings_am` (add `OPEN_APP = "..."`). `handlers()` returns any command handlers needed (e.g. `/app`).

- [ ] **Step 2: Rewire onboarding and home**

In `handlers/onboarding.py`, replace the post-registration `show_home(...)` call with `show_launch(...)`. In `handlers/home.py`, replace `show_home` internals to show the launch button (registered users) and drop the `driver_home`/`rider_home` keyboards. Remove the `CallbackQueryHandler`s for the retired flows.

- [ ] **Step 3: Remove the retired UI and update wiring**

Delete `handlers/driver.py`, `handlers/rider.py`, `keyboards.py`, `tests/test_keyboards.py`. In `bot.py`, change the registration loop to `for group in (onboarding, launch):` and drop the `driver`/`rider`/`admin`/`home` keyboard imports (keep `home.show_home`→launch if referenced). Keep `register_jobs`, the event-loop fix, and `run_polling(allowed_updates=Update.ALL_TYPES)`.

- [ ] **Step 4: Run the suite**

Run: `python -m pytest -q`
Expected: green (the deleted keyboard tests are gone; the API + domain tests pass).

- [ ] **Step 5: Manual check**

With `WEBAPP_URL` set to a placeholder https URL and a test token, run the bot, `/start`, share contact → expect the single "Open Gara Ride" button. (The button only opens a real app once Plan 2 is deployed.)

- [ ] **Step 6: Commit**

```bash
git add gararide/ tests/
git commit -m "refactor: slim the bot to a Mini App launcher plus notifications"
```

---

## Task 10: Server entrypoint and Render readiness

**Files:**
- Create: `gararide/server.py`, `Procfile`, `render.yaml`
- Modify: `gararide/api/app.py` (serve built static frontend if present; health route), `DEPLOY.md`
- Test: `tests/test_api_health.py`

**Interfaces:**
- Consumes: `create_app`, `db.connect`, `db.init_schema`, `places.seed_corridor`.
- Produces: `server.py` builds the app with a real DB + bot token from env and exposes `app` for uvicorn; `GET /healthz` → `{"status":"ok"}`; static files under `/` when a `frontend/dist` build exists (Plan 2 produces it).

- [ ] **Step 1: Write the failing health test**

`tests/test_api_health.py`: `create_app(...)` then `GET /healthz` returns 200 `{"status":"ok"}` (no auth required).

- [ ] **Step 2: Run to verify it fails**; then add an unauthenticated `@app.get("/healthz")` to `app.py`.

- [ ] **Step 3: Create `gararide/server.py`**

```python
"""ASGI entrypoint: uvicorn gararide.server:app"""
import os
from .db import connect, init_schema
from .places import seed_corridor
from .api.app import create_app

conn = connect(os.environ.get("GARARIDE_DB", "gararide.sqlite3"))
init_schema(conn)
seed_corridor(conn, os.environ.get("GARARIDE_CORRIDOR", "seed/corridor_ayat49.csv"))
admins = frozenset(int(x) for x in os.environ.get("GARARIDE_ADMINS", "").split(",") if x.strip())
app = create_app(conn, os.environ["BOT_TOKEN"], admin_ids=admins)

if os.path.isdir("frontend/dist"):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="app")
```

- [ ] **Step 4: `Procfile` + `render.yaml` + DEPLOY.md**

`Procfile`: `web: uvicorn gararide.server:app --host 0.0.0.0 --port $PORT`
`render.yaml`: a single web service running that command, env vars `BOT_TOKEN`, `GARARIDE_ADMINS`, `WEBAPP_URL`. Update `DEPLOY.md` with the Mini App setup: set the bot's Menu Button / `/setmenubutton` to `WEBAPP_URL` via BotFather, and the two deep links still work for role at registration.

- [ ] **Step 5: Run the suite and commit**

Run: `python -m pytest -q` (green).
```bash
git add gararide/ Procfile render.yaml DEPLOY.md tests/test_api_health.py
git commit -m "feat: uvicorn entrypoint, health check, and Render config"
```

---

## Notes for Plan 2 (frontend)

The Mini App consumes: `GET /me` (role → which home), `GET /places`, the driver and rider endpoints above, `GET /me/saved`, and (for admins) `/admin/*`. Auth: send `Authorization: tma <Telegram.WebApp.initData>` on every request. Price and both clocks render from the fare + `depart_at` fields every response already includes. The bot's "Open Gara Ride" button (Task 9) launches it.
