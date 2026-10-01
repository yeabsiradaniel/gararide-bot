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
    card = c.post("/bookings", headers=_auth(2001),
                  json={"trip_id": tid, "to_place_id": ids["megenagna"]}).json()
    return card["booking_id"]


def _complete(conn, bid):
    # Mirror expire_trips: the trip has departed and the booking is completed.
    past = (datetime.now() - timedelta(days=1)).isoformat(timespec="seconds")
    conn.execute(
        "UPDATE trips SET depart_at=?, status='done'"
        " WHERE id=(SELECT trip_id FROM bookings WHERE id=?)", (past, bid))
    conn.execute("UPDATE bookings SET status='completed' WHERE id=?", (bid,))
    conn.commit()


def test_cannot_rate_until_completed(client):
    conn, c = client
    bid = _booked(conn, c)
    assert c.post(f"/bookings/{bid}/rate", headers=_auth(2001),
                  json={"value": 1}).status_code == 400


def test_rating_shows_in_history_and_admin_tally_and_overwrites(client):
    conn, c = client
    bid = _booked(conn, c)
    _complete(conn, bid)
    assert c.post(f"/bookings/{bid}/rate", headers=_auth(2001),
                  json={"value": 1}).status_code == 204

    hist = c.get("/bookings/history", headers=_auth(2001)).json()
    assert hist[0]["rating"] == 1

    d = next(x for x in c.get("/admin/drivers", headers=_auth(1001)).json()
             if x["onboarded"])
    assert d["ratings"] == {"up": 1, "down": 0}

    # re-rating the same booking overwrites, never stacks
    c.post(f"/bookings/{bid}/rate", headers=_auth(2001), json={"value": -1})
    d = next(x for x in c.get("/admin/drivers", headers=_auth(1001)).json()
             if x["onboarded"])
    assert d["ratings"] == {"up": 0, "down": 1}


def test_bad_value_rejected(client):
    conn, c = client
    bid = _booked(conn, c)
    _complete(conn, bid)
    assert c.post(f"/bookings/{bid}/rate", headers=_auth(2001),
                  json={"value": 5}).status_code == 422


def test_cannot_rate_a_booking_that_isnt_yours(client):
    conn, c = client
    bid = _booked(conn, c)
    _complete(conn, bid)
    assert c.post(f"/bookings/{bid}/rate", headers=_auth(1001),  # the driver
                  json={"value": 1}).status_code == 404
