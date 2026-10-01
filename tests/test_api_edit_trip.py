from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from gararide.api.app import create_app
from gararide.places import place_by_slug
from gararide.trips import mark_arrived, post_trip
from gararide.users import import_allowlist, register, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def client(seeded):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register(seeded, telegram_id=1001, phone="0911223344")       # driver (car_seats 4)
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    return seeded, TestClient(create_app(seeded, BOT_TOKEN))


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def _at(hour):
    return (datetime.now() + timedelta(days=1)).replace(
        hour=hour, minute=0, second=0, microsecond=0)


def _trip(conn, seats=3):
    ids = {s: place_by_slug(conn, s)["id"] for s in ("megenagna", "kazanchis")}
    tid = post_trip(conn, driver_id=1001, dest_place_id=ids["kazanchis"],
                    dropoff_place_ids=[ids["megenagna"], ids["kazanchis"]],
                    depart_at=_at(7), seats=seats)
    return tid, ids


def test_edit_changes_time_and_seats(client):
    conn, c = client
    tid, _ = _trip(conn)
    r = c.patch(f"/trips/{tid}", headers=_auth(1001),
                json={"depart_at": _at(8).isoformat(timespec="seconds"),
                      "seats": 2, "note": "running a bit later"})
    assert r.status_code == 200
    mine = c.get("/trips/mine", headers=_auth(1001)).json()[0]
    assert mine["depart_at"].endswith("08:00:00")
    assert mine["seats_total"] == 2
    assert mine["note"] == "running a bit later"


def test_cannot_drop_seats_below_booked(client):
    conn, c = client
    tid, ids = _trip(conn, seats=3)
    c.post("/bookings", headers=_auth(2001),
           json={"trip_id": tid, "to_place_id": ids["megenagna"]})  # 1 booked
    r = c.patch(f"/trips/{tid}", headers=_auth(1001),
                json={"depart_at": _at(7).isoformat(timespec="seconds"), "seats": 0})
    assert r.status_code == 422


def test_cannot_set_time_in_the_past(client):
    conn, c = client
    tid, _ = _trip(conn)
    past = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
    r = c.patch(f"/trips/{tid}", headers=_auth(1001),
                json={"depart_at": past, "seats": 2})
    assert r.status_code == 422


def test_cannot_edit_after_arrived(client):
    conn, c = client
    tid, _ = _trip(conn)
    mark_arrived(conn, tid)
    r = c.patch(f"/trips/{tid}", headers=_auth(1001),
                json={"depart_at": _at(8).isoformat(timespec="seconds"), "seats": 2})
    assert r.status_code == 409


def test_cannot_edit_another_drivers_trip(client):
    conn, c = client
    tid, _ = _trip(conn)
    r = c.patch(f"/trips/{tid}", headers=_auth(2001),  # the rider
                json={"depart_at": _at(8).isoformat(timespec="seconds"), "seats": 2})
    assert r.status_code in (403, 404)
