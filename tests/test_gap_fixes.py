from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from gararide.api import admin as admin_mod
from gararide.api import driver as driver_mod
from gararide.api import rider as rider_mod
from gararide.api.app import create_app
from gararide.bookings import book
from gararide.matching import near_misses
from gararide.places import place_by_slug
from gararide.requests import post_request
from gararide.scheduler import due_reminders
from gararide.trips import (booking_open, expire_trips, get_trip, post_block_reason,
                            post_trip)
from gararide.users import add_to_allowlist, import_allowlist, register, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def env(seeded, monkeypatch):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register(seeded, telegram_id=1001, phone="0911223344")     # driver + admin
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    register_rider(seeded, telegram_id=2002, phone="0900000002", full_name="Two")
    sent: list[tuple[int, str]] = []
    rec = lambda app, cid, txt: sent.append((cid, txt))  # noqa: E731
    for m in (admin_mod, driver_mod, rider_mod):
        monkeypatch.setattr(m, "notify", rec)
    app = create_app(seeded, BOT_TOKEN, admin_ids=frozenset({1001}))
    return seeded, TestClient(app), sent


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def _kaz(conn):
    return place_by_slug(conn, "kazanchis")["id"]


def _dt(mins):
    return (datetime.now() + timedelta(minutes=mins)).replace(microsecond=0)


def _trip(conn, depart, driver=1001, dest=None):
    dest = dest or _kaz(conn)
    return post_trip(conn, driver_id=driver, dest_place_id=dest,
                     dropoff_place_ids=[dest], depart_at=depart, seats=2)


# ---- guards ---------------------------------------------------------------

def test_posting_a_past_trip_is_rejected(env):
    conn, c, _ = env
    r = c.post("/trips", headers=_auth(1001), json={
        "dest_place_id": _kaz(conn), "dropoff_place_ids": [], "seats": 2,
        "depart_at": _dt(-60).isoformat(timespec="seconds")})
    assert r.status_code == 422


def test_booking_a_departed_trip_is_rejected(env):
    conn, c, _ = env
    tid = _trip(conn, _dt(-5))
    r = c.post("/bookings", headers=_auth(2001),
               json={"trip_id": tid, "to_place_id": _kaz(conn)})
    assert r.status_code == 409


def test_double_booking_is_idempotent(env):
    conn, c, _ = env
    tid = _trip(conn, _dt(120))
    k = _kaz(conn)
    b1 = c.post("/bookings", headers=_auth(2001), json={"trip_id": tid, "to_place_id": k}).json()
    b2 = c.post("/bookings", headers=_auth(2001), json={"trip_id": tid, "to_place_id": k}).json()
    assert b1["booking_id"] == b2["booking_id"]
    booked = conn.execute("SELECT COUNT(*) FROM bookings WHERE trip_id=? AND status='booked'",
                          (tid,)).fetchone()[0]
    assert booked == 1


def test_cannot_cancel_another_riders_booking(env):
    conn, c, _ = env
    tid = _trip(conn, _dt(120))
    bid = c.post("/bookings", headers=_auth(2001),
                 json={"trip_id": tid, "to_place_id": _kaz(conn)}).json()["booking_id"]
    assert c.post(f"/bookings/{bid}/cancel", headers=_auth(2002)).status_code == 404
    # still booked
    assert conn.execute("SELECT status FROM bookings WHERE id=?", (bid,)).fetchone()[0] == "booked"


# ---- request loop ---------------------------------------------------------

def test_booking_fills_the_riders_own_request(env):
    conn, c, _ = env
    k = _kaz(conn)
    post_request(conn, rider_id=2001, dest_place_id=k,
                 window_start=datetime.now(), window_end=_dt(180))
    tid = _trip(conn, _dt(90))
    c.post("/bookings", headers=_auth(2001), json={"trip_id": tid, "to_place_id": k})
    assert conn.execute("SELECT status FROM requests WHERE rider_id=2001").fetchone()[0] == "filled"


def test_posting_a_matching_trip_notifies_waiting_rider(env):
    conn, c, sent = env
    k = _kaz(conn)
    post_request(conn, rider_id=2001, dest_place_id=k,
                 window_start=datetime.now(), window_end=_dt(180))
    c.post("/trips", headers=_auth(1001), json={
        "dest_place_id": k, "dropoff_place_ids": [], "seats": 2,
        "depart_at": _dt(150).isoformat(timespec="seconds")})  # >2h: passes the post gate
    assert any(cid == 2001 for cid, _ in sent)
    assert conn.execute("SELECT status FROM requests WHERE rider_id=2001").fetchone()[0] == "filled"


def test_admin_removing_a_driver_notifies_booked_riders(env):
    conn, c, sent = env
    add_to_allowlist(conn, phone="0900000003", full_name="D2", tower="C1", car_seats=4)
    register(conn, telegram_id=3003, phone="0900000003")
    tid = _trip(conn, _dt(120), driver=3003)
    c.post("/bookings", headers=_auth(2001), json={"trip_id": tid, "to_place_id": _kaz(conn)})
    sent.clear()
    assert c.delete("/admin/drivers/0900000003", headers=_auth(1001)).status_code == 200
    assert any(cid == 2001 for cid, _ in sent)


# ---- lifecycle ------------------------------------------------------------

def test_expire_trips_closes_departed_open_trips(env):
    conn, _, _ = env
    past = _trip(conn, _dt(-10))
    fut = _trip(conn, _dt(120))
    expire_trips(conn)
    assert get_trip(conn, past)["status"] == "done"
    assert get_trip(conn, fut)["status"] == "open"


def test_past_ride_moves_to_history(env):
    conn, c, _ = env
    k = _kaz(conn)
    tid = _trip(conn, _dt(120))  # book with a valid (>1h) lead
    c.post("/bookings", headers=_auth(2001), json={"trip_id": tid, "to_place_id": k})
    # push the trip into the past, then expire it
    conn.execute("UPDATE trips SET depart_at=? WHERE id=?",
                 (_dt(-60).isoformat(timespec="seconds"), tid))
    conn.commit()
    expire_trips(conn)
    hist = c.get("/bookings/history", headers=_auth(2001)).json()
    assert any(h["booking_id"] and h["status"] == "completed" for h in hist)
    # and it's gone from upcoming
    assert not c.get("/bookings/mine", headers=_auth(2001)).json()


def test_near_misses_do_not_show_departed_trips(env):
    conn, _, _ = env
    past = _trip(conn, _dt(-10))
    start = datetime.now()
    end = start.replace(hour=23, minute=59, second=59)
    nms = near_misses(conn, rider_id=2001, dest_place_id=_kaz(conn),
                      window_start=start, window_end=end)
    assert all(m.trip_id != past for m in nms)


def test_reminder_is_sent_once(env):
    conn, _, _ = env
    tid = _trip(conn, _dt(120))  # book with a valid (>1h) lead
    bid = book(conn, trip_id=tid, rider_id=2001, to_place_id=_kaz(conn))["id"]
    # then the departure draws near, so the reminder comes due
    conn.execute("UPDATE trips SET depart_at=? WHERE id=?",
                 (_dt(25).isoformat(timespec="seconds"), tid))
    conn.commit()
    now = datetime.now()
    assert bid in due_reminders(conn, now)
    conn.execute("UPDATE bookings SET reminded=1 WHERE id=?", (bid,))
    conn.commit()
    assert bid not in due_reminders(conn, now)


# ---- booking cutoff (#1) --------------------------------------------------

def test_booking_open_locks_the_night_before():
    depart = datetime(2026, 1, 2, 7, 0)                 # a 07:00 trip
    assert booking_open(depart, datetime(2026, 1, 1, 20, 30)) is True   # before 21:00 eve
    assert booking_open(depart, datetime(2026, 1, 1, 21, 30)) is False  # after 21:00 cutoff
    # same-day ad-hoc trip stays open until it leaves
    assert booking_open(datetime(2026, 1, 1, 18, 0), datetime(2026, 1, 1, 9, 0)) is True
    # already departed
    assert booking_open(datetime(2026, 1, 1, 8, 0), datetime(2026, 1, 1, 9, 0)) is False


def test_booking_closes_one_hour_before_departure():
    depart = datetime(2026, 1, 1, 8, 0)
    assert booking_open(depart, datetime(2026, 1, 1, 6, 0)) is True    # 2h before: open
    assert booking_open(depart, datetime(2026, 1, 1, 7, 0)) is False   # 1h before: closed
    assert booking_open(depart, datetime(2026, 1, 1, 7, 30)) is False  # within 1h: closed


def test_post_block_reason_lead_and_lock():
    now = datetime(2026, 1, 1, 8, 0)
    assert post_block_reason(datetime(2026, 1, 1, 9, 0), now) == "too_soon"     # same-day <2h
    assert post_block_reason(datetime(2026, 1, 1, 10, 0), now) is None          # same-day >=2h
    assert post_block_reason(datetime(2026, 1, 2, 7, 0), now) is None           # next-day, pre-lock
    assert post_block_reason(datetime(2026, 1, 2, 7, 0),
                             datetime(2026, 1, 1, 21, 30)) == "roster_locked"   # next-day, post-21:00


# ---- cancelled-booking history (#2) ---------------------------------------

def test_cancelled_ride_shows_in_my_bookings(env):
    conn, c, _ = env
    tid = _trip(conn, _dt(120))
    c.post("/bookings", headers=_auth(2001), json={"trip_id": tid, "to_place_id": _kaz(conn)})
    c.post(f"/trips/{tid}/cancel", headers=_auth(1001))
    mine = c.get("/bookings/mine", headers=_auth(2001)).json()
    assert any(b["cancelled"] for b in mine)


# ---- dwell / boarding (#3) ------------------------------------------------

def test_arrival_notifies_riders_and_returns_dwell(env):
    conn, c, sent = env
    tid = _trip(conn, _dt(120))  # book with a valid (>1h) lead
    c.post("/bookings", headers=_auth(2001), json={"trip_id": tid, "to_place_id": _kaz(conn)})
    sent.clear()
    r = c.post(f"/trips/{tid}/arrived", headers=_auth(1001))
    assert r.status_code == 200 and r.json()["dwell_minutes"] == 4
    assert any(cid == 2001 for cid, _ in sent)


def test_no_show_blocked_until_dwell_passes(env):
    conn, c, _ = env
    tid = _trip(conn, _dt(120))
    bid = c.post("/bookings", headers=_auth(2001),
                 json={"trip_id": tid, "to_place_id": _kaz(conn)}).json()["booking_id"]
    # driver arrives now -> can't no-show during the 4-minute grace
    c.post(f"/trips/{tid}/arrived", headers=_auth(1001))
    assert c.post(f"/bookings/{bid}/no-show", headers=_auth(1001)).status_code == 409
    # once the dwell has elapsed (simulate an earlier arrival) it's allowed
    conn.execute("UPDATE trips SET arrived_at=? WHERE id=?",
                 ((datetime.now() - timedelta(minutes=10)).isoformat(timespec="seconds"), tid))
    conn.commit()
    assert c.post(f"/bookings/{bid}/no-show", headers=_auth(1001)).status_code == 204
