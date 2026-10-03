from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from gararide import waitlist
from gararide.api.app import create_app
from gararide.places import place_by_slug
from gararide.trips import post_trip
from gararide.users import import_allowlist, register, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def client(seeded):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register(seeded, telegram_id=1001, phone="0911223344")
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="A")
    register_rider(seeded, telegram_id=2002, phone="0999999998", full_name="B")
    return seeded, TestClient(create_app(seeded, BOT_TOKEN))


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def _trip(conn, seats=1):
    ids = {s: place_by_slug(conn, s)["id"] for s in ("megenagna", "kazanchis")}
    depart = (datetime.now() + timedelta(days=1)).replace(
        hour=7, minute=0, second=0, microsecond=0)
    tid = post_trip(conn, driver_id=1001, dest_place_id=ids["kazanchis"],
                    dropoff_place_ids=[ids["megenagna"], ids["kazanchis"]],
                    depart_at=depart, seats=seats)
    return tid, ids["megenagna"]


def test_join_waitlist(client):
    conn, c = client
    tid, meg = _trip(conn)
    assert c.post("/waitlist", headers=_auth(2001),
                  json={"trip_id": tid, "to_place_id": meg}).status_code == 204
    assert waitlist.is_waiting(conn, tid, 2001)


def test_cancel_releases_without_error(client):
    conn, c = client
    tid, meg = _trip(conn, seats=1)
    # 2002 takes the only seat; 2001 waits
    bid = c.post("/bookings", headers=_auth(2002),
                 json={"trip_id": tid, "to_place_id": meg}).json()["booking_id"]
    c.post("/waitlist", headers=_auth(2001), json={"trip_id": tid, "to_place_id": meg})
    # 2002 cancels -> seat frees, waitlist pinged (no bot in tests; must not error)
    assert c.post(f"/bookings/{bid}/cancel", headers=_auth(2002)).status_code == 204
