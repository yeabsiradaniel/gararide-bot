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
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    return seeded, TestClient(create_app(seeded, BOT_TOKEN))


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def _at7():
    return (datetime.now() + timedelta(days=1)).replace(
        hour=7, minute=0, second=0, microsecond=0)


def _post_kaz_via_meg(conn):
    ids = {s: place_by_slug(conn, s)["id"] for s in ("megenagna", "kazanchis")}
    return post_trip(conn, driver_id=1001, dest_place_id=ids["kazanchis"],
                     dropoff_place_ids=[ids["megenagna"], ids["kazanchis"]],
                     depart_at=_at7(), seats=3), ids


def test_search_returns_a_matching_trip_with_fare(client):
    conn, c = client
    _, ids = _post_kaz_via_meg(conn)
    r = c.get("/trips/search", params={"dest_place_id": ids["megenagna"]},
              headers=_auth(2001))
    body = r.json()
    assert len(body["matches"]) == 1
    assert body["matches"][0]["fare"] == 55


def test_search_with_no_exact_match_is_never_empty(client):
    conn, c = client
    _post_kaz_via_meg(conn)  # offers megenagna + kazanchis, not aratkilo
    arat = place_by_slug(conn, "aratkilo")["id"]
    r = c.get("/trips/search", params={"dest_place_id": arat}, headers=_auth(2001))
    body = r.json()
    assert body["matches"] == []
    assert len(body["near_misses"]) >= 1
    assert body["near_misses"][0]["reason"] == "partway"
    assert "demand_count" in body


def test_a_trip_you_already_booked_is_not_offered_again(client):
    conn, c = client
    tid, ids = _post_kaz_via_meg(conn)
    before = c.get("/trips/search", params={"dest_place_id": ids["megenagna"]},
                   headers=_auth(2001)).json()
    assert len(before["matches"]) == 1
    c.post("/bookings", headers=_auth(2001),
           json={"trip_id": tid, "to_place_id": ids["megenagna"]})
    after = c.get("/trips/search", params={"dest_place_id": ids["megenagna"]},
                  headers=_auth(2001)).json()
    assert after["matches"] == []


def test_booking_returns_driver_contact_and_price(client):
    conn, c = client
    _, ids = _post_kaz_via_meg(conn)
    tid = _post_kaz_via_meg(conn)[0]  # a fresh trip to book
    r = c.post("/bookings", headers=_auth(2001),
               json={"trip_id": tid, "to_place_id": ids["megenagna"]})
    assert r.status_code == 201
    card = r.json()
    assert card["fare"] == 55
    assert card["plate"] == "3-AA 21457"
    assert card["phone"].endswith("911223344")
    assert card["bay"] == "Bay Alpha"


def test_booking_a_declined_stop_is_409(client):
    conn, c = client
    tid, _ = _post_kaz_via_meg(conn)
    cmc = place_by_slug(conn, "cmc")["id"]     # not offered
    r = c.post("/bookings", headers=_auth(2001),
               json={"trip_id": tid, "to_place_id": cmc})
    assert r.status_code == 409


def test_blocking_a_driver_removes_them_from_search(client):
    conn, c = client
    tid, ids = _post_kaz_via_meg(conn)
    assert len(c.get("/trips/search", params={"dest_place_id": ids["kazanchis"]},
                     headers=_auth(2001)).json()["matches"]) == 1
    assert c.post("/blocks", headers=_auth(2001), json={"trip_id": tid}).status_code == 204
    assert c.get("/trips/search", params={"dest_place_id": ids["kazanchis"]},
                 headers=_auth(2001)).json()["matches"] == []
