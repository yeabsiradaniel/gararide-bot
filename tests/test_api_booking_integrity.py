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
    register(seeded, telegram_id=1001, phone="0911223344")       # driver
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="A")
    register_rider(seeded, telegram_id=2002, phone="0999999998", full_name="B")
    return seeded, TestClient(create_app(seeded, BOT_TOKEN))


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def _trip(conn, hour, minute=0, seats=3):
    ids = {s: place_by_slug(conn, s)["id"] for s in ("megenagna", "kazanchis")}
    depart = (datetime.now() + timedelta(days=1)).replace(
        hour=hour, minute=minute, second=0, microsecond=0)
    tid = post_trip(conn, driver_id=1001, dest_place_id=ids["kazanchis"],
                    dropoff_place_ids=[ids["megenagna"], ids["kazanchis"]],
                    depart_at=depart, seats=seats)
    return tid, ids["megenagna"]


def test_last_seat_cannot_be_double_booked(client):
    conn, c = client
    tid, meg = _trip(conn, 7, seats=1)
    assert c.post("/bookings", headers=_auth(2001),
                  json={"trip_id": tid, "to_place_id": meg}).status_code == 201
    r = c.post("/bookings", headers=_auth(2002), json={"trip_id": tid, "to_place_id": meg})
    assert r.status_code == 409   # seat already claimed — atomic insert blocks it


def test_rider_cannot_book_overlapping_times(client):
    conn, c = client
    a, meg = _trip(conn, 7, 0)
    b, _ = _trip(conn, 7, 30)     # 30 min later — overlaps
    assert c.post("/bookings", headers=_auth(2001),
                  json={"trip_id": a, "to_place_id": meg}).status_code == 201
    r = c.post("/bookings", headers=_auth(2001), json={"trip_id": b, "to_place_id": meg})
    assert r.status_code == 409 and r.json()["detail"] == "time_conflict"


def test_driver_cannot_book_own_trip(client):
    conn, c = client
    a, meg = _trip(conn, 7, 0)   # driver 1001's trip
    r = c.post("/bookings", headers=_auth(1001), json={"trip_id": a, "to_place_id": meg})
    assert r.status_code == 409 and r.json()["detail"] == "own_trip"


def test_rider_can_book_well_separated_times(client):
    conn, c = client
    a, meg = _trip(conn, 7, 0)
    far, _ = _trip(conn, 11, 0)   # 4h later — no overlap
    assert c.post("/bookings", headers=_auth(2001),
                  json={"trip_id": a, "to_place_id": meg}).status_code == 201
    assert c.post("/bookings", headers=_auth(2001),
                  json={"trip_id": far, "to_place_id": meg}).status_code == 201
