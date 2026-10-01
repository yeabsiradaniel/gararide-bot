from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from gararide.api.app import create_app
from gararide.places import place_by_slug
from gararide.trips import post_trip
from gararide.users import import_allowlist, register, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def client(seeded):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register(seeded, telegram_id=1001, phone="0911223344")       # driver + admin
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    app = create_app(seeded, BOT_TOKEN, admin_ids=frozenset({1001}))
    return seeded, TestClient(app)


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def _booked(conn, c):
    ids = {s: place_by_slug(conn, s)["id"] for s in ("megenagna", "kazanchis")}
    depart = (datetime.now() + timedelta(days=1)).replace(
        hour=7, minute=0, second=0, microsecond=0)
    tid = post_trip(conn, driver_id=1001, dest_place_id=ids["kazanchis"],
                    dropoff_place_ids=[ids["megenagna"], ids["kazanchis"]],
                    depart_at=depart, seats=3)
    bid = c.post("/bookings", headers=_auth(2001),
                 json={"trip_id": tid, "to_place_id": ids["megenagna"]}).json()["booking_id"]
    return tid, bid


def _depart_now_passed(conn, tid):
    past = (datetime.now() - timedelta(minutes=5)).isoformat(timespec="seconds")
    conn.execute("UPDATE trips SET depart_at=? WHERE id=?", (past, tid))
    conn.commit()


def test_rider_flags_driver_no_show_reaches_admin(client):
    conn, c = client
    tid, bid = _booked(conn, c)
    _depart_now_passed(conn, tid)
    assert c.post(f"/bookings/{bid}/driver-no-show", headers=_auth(2001)).status_code == 204
    rows = c.get("/admin/reports", headers=_auth(1001)).json()
    assert len(rows) == 1 and rows[0]["reason"] == "driver_no_show"


def test_cannot_flag_before_departure(client):
    conn, c = client
    _, bid = _booked(conn, c)   # still in the future
    assert c.post(f"/bookings/{bid}/driver-no-show", headers=_auth(2001)).status_code == 400


def test_cannot_flag_someone_elses_booking(client):
    conn, c = client
    tid, bid = _booked(conn, c)
    _depart_now_passed(conn, tid)
    assert c.post(f"/bookings/{bid}/driver-no-show", headers=_auth(1001)).status_code == 404
