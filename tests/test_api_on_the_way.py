from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from gararide.api.app import create_app
from gararide.places import place_by_slug
from gararide.trips import post_trip
from gararide.users import (add_to_allowlist, import_allowlist, register,
                            register_rider)
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def client(seeded):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register(seeded, telegram_id=1001, phone="0911223344")       # driver
    add_to_allowlist(seeded, phone="0911334455", full_name="D2", tower="C1",
                     role="driver", car_model="Vitz", plate="3-AA 1", car_seats=4)
    register(seeded, telegram_id=1003, phone="0911334455")       # another driver
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    return seeded, TestClient(create_app(seeded, BOT_TOKEN))


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def _booked_trip(conn, c):
    ids = {s: place_by_slug(conn, s)["id"] for s in ("megenagna", "kazanchis")}
    depart = (datetime.now() + timedelta(days=1)).replace(
        hour=7, minute=0, second=0, microsecond=0)
    tid = post_trip(conn, driver_id=1001, dest_place_id=ids["kazanchis"],
                    dropoff_place_ids=[ids["megenagna"], ids["kazanchis"]],
                    depart_at=depart, seats=3)
    c.post("/bookings", headers=_auth(2001),
           json={"trip_id": tid, "to_place_id": ids["megenagna"]})
    return tid


def test_on_my_way_sets_eta_and_shows_on_both_sides(client):
    conn, c = client
    tid = _booked_trip(conn, c)
    r = c.post(f"/trips/{tid}/on-my-way", headers=_auth(1001), json={"eta_minutes": 10})
    assert r.status_code == 200
    assert r.json()["otw_eta"] == 10

    mine = c.get("/trips/mine", headers=_auth(1001)).json()
    assert mine[0]["otw_at"] is not None and mine[0]["otw_eta"] == 10

    card = c.get("/bookings/mine", headers=_auth(2001)).json()[0]
    assert card["otw_at"] is not None and card["otw_eta"] == 10


def test_eta_out_of_range_is_rejected(client):
    conn, c = client
    tid = _booked_trip(conn, c)
    assert c.post(f"/trips/{tid}/on-my-way", headers=_auth(1001),
                  json={"eta_minutes": 0}).status_code == 422
    assert c.post(f"/trips/{tid}/on-my-way", headers=_auth(1001),
                  json={"eta_minutes": 99}).status_code == 422


def test_cannot_set_on_my_way_for_another_drivers_trip(client):
    conn, c = client
    tid = _booked_trip(conn, c)
    assert c.post(f"/trips/{tid}/on-my-way", headers=_auth(1003),
                  json={"eta_minutes": 10}).status_code == 404


def test_re_tapping_updates_the_eta(client):
    conn, c = client
    tid = _booked_trip(conn, c)
    c.post(f"/trips/{tid}/on-my-way", headers=_auth(1001), json={"eta_minutes": 15})
    c.post(f"/trips/{tid}/on-my-way", headers=_auth(1001), json={"eta_minutes": 5})
    assert c.get("/trips/mine", headers=_auth(1001)).json()[0]["otw_eta"] == 5
