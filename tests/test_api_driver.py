from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from gararide.api.app import create_app
from gararide.places import place_by_slug
from gararide.users import import_allowlist, register, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


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
    assert [p["slug"] for p in r.json()["intermediate"]] == \
        ["cmc", "megenagna", "aratkilo"]
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


def test_my_trips_shows_a_passenger(client):
    conn, c = client
    kaz = place_by_slug(conn, "kazanchis")["id"]
    from gararide.bookings import book
    from gararide.trips import post_trip
    from datetime import datetime as _dt
    tid = post_trip(conn, driver_id=1001, dest_place_id=kaz,
                    dropoff_place_ids=[kaz],
                    depart_at=_dt.fromisoformat(_tomorrow_7()), seats=3)
    book(conn, trip_id=tid, rider_id=2001, to_place_id=kaz)
    r = c.get("/trips/mine", headers=_auth(1001))
    trip = r.json()[0]
    assert trip["seats_left"] == 2
    assert trip["passengers"][0]["name"] == "Fan"
    assert trip["passengers"][0]["fare"] == 85


def test_a_rider_cannot_post_a_trip(client):
    conn, c = client
    kaz = place_by_slug(conn, "kazanchis")["id"]
    r = c.post("/trips", headers=_auth(2001), json={
        "dest_place_id": kaz, "dropoff_place_ids": [kaz],
        "depart_at": _tomorrow_7(), "seats": 1})
    assert r.status_code == 403
