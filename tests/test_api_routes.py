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
    register(seeded, telegram_id=1001, phone="0911223344")       # driver, 4 seats
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    return seeded, TestClient(create_app(seeded, BOT_TOKEN))


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def _kaz(conn):
    return place_by_slug(conn, "kazanchis")["id"]


def _save(c, conn, **over):
    body = {"dest_place_id": _kaz(conn), "dropoff_place_ids": [], "depart_time": "07:00",
            "seats": 2, "days_mask": 0b0011111}
    body.update(over)
    return c.post("/routes", headers=_auth(1001), json=body)


def test_driver_saves_and_lists_a_route(client):
    conn, c = client
    r = _save(c, conn)
    assert r.status_code == 201 and r.json()["depart_time"] == "07:00"
    listed = c.get("/routes", headers=_auth(1001)).json()
    assert len(listed) == 1 and listed[0]["seats"] == 2


def test_route_rejects_more_seats_than_car(client):
    conn, c = client
    assert _save(c, conn, seats=9).status_code == 422


def test_riders_cannot_use_routes(client):
    _, c = client
    assert c.get("/routes", headers=_auth(2001)).status_code == 403


def test_post_route_creates_tomorrows_trip(client):
    conn, c = client
    rid = _save(c, conn).json()["id"]
    r = c.post(f"/routes/{rid}/post", headers=_auth(1001))
    assert r.status_code == 200
    body = r.json()
    assert body["already"] is False
    assert body["depart_at"].startswith(
        (datetime.now() + timedelta(days=1)).date().isoformat())
    # the trip really exists for the driver
    mine = c.get("/trips/mine", headers=_auth(1001)).json()
    assert any(t["trip_id"] == body["trip_id"] for t in mine)


def test_posting_a_route_twice_does_not_duplicate(client):
    conn, c = client
    rid = _save(c, conn).json()["id"]
    first = c.post(f"/routes/{rid}/post", headers=_auth(1001)).json()
    second = c.post(f"/routes/{rid}/post", headers=_auth(1001)).json()
    assert second["already"] is True
    assert first["trip_id"] == second["trip_id"]
    assert len(c.get("/trips/mine", headers=_auth(1001)).json()) == 1


def test_deleted_route_disappears(client):
    conn, c = client
    rid = _save(c, conn).json()["id"]
    assert c.delete(f"/routes/{rid}", headers=_auth(1001)).status_code == 204
    assert c.get("/routes", headers=_auth(1001)).json() == []
    assert c.post(f"/routes/{rid}/post", headers=_auth(1001)).status_code == 404


def test_a_driver_cannot_touch_another_drivers_route(client):
    conn, c = client
    rid = _save(c, conn).json()["id"]
    # a second driver
    import_allowlist(conn, "seed/allowlist_template.csv")
    conn.execute("INSERT OR IGNORE INTO allowlist (phone, full_name, tower, role,"
                 " car_seats, verified_at) VALUES"
                 " ('251922000000','Two','C1','driver',4,'2020-01-01')")
    conn.commit()
    register(conn, telegram_id=1002, phone="0922000000")
    assert c.delete(f"/routes/{rid}", headers=_auth(1002)).status_code == 404
    assert c.post(f"/routes/{rid}/post", headers=_auth(1002)).status_code == 404
