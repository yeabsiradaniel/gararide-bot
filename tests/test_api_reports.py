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


def _trip(conn):
    ids = {s: place_by_slug(conn, s)["id"] for s in ("megenagna", "kazanchis")}
    depart = (datetime.now() + timedelta(days=1)).replace(
        hour=7, minute=0, second=0, microsecond=0)
    tid = post_trip(conn, driver_id=1001, dest_place_id=ids["kazanchis"],
                    dropoff_place_ids=[ids["megenagna"], ids["kazanchis"]],
                    depart_at=depart, seats=3)
    return tid


def test_rider_reports_and_admin_sees_it(client):
    conn, c = client
    tid = _trip(conn)
    r = c.post("/reports", headers=_auth(2001),
               json={"trip_id": tid, "reason": "unsafe_driving", "note": "sped a lot"})
    assert r.status_code == 201
    assert "report_id" in r.json()

    rows = c.get("/admin/reports", headers=_auth(1001)).json()
    assert len(rows) == 1
    assert rows[0]["reason"] == "unsafe_driving"
    assert rows[0]["note"] == "sped a lot"
    assert rows[0]["reporter_name"] == "Fan"
    # the reported party's phone is for the admin only
    assert rows[0]["reported_phone"].endswith("911223344")


def test_unknown_reason_is_rejected(client):
    conn, c = client
    tid = _trip(conn)
    r = c.post("/reports", headers=_auth(2001),
               json={"trip_id": tid, "reason": "aliens"})
    assert r.status_code == 422


def test_cannot_report_yourself(client):
    conn, c = client
    tid = _trip(conn)
    r = c.post("/reports", headers=_auth(1001),  # the driver of this trip
               json={"trip_id": tid, "reason": "other"})
    assert r.status_code == 400


def test_non_admin_cannot_list_reports(client):
    conn, c = client
    assert c.get("/admin/reports", headers=_auth(2001)).status_code == 403


def test_resolve_clears_the_report(client):
    conn, c = client
    tid = _trip(conn)
    rid = c.post("/reports", headers=_auth(2001),
                 json={"trip_id": tid, "reason": "rude"}).json()["report_id"]
    assert c.post(f"/admin/reports/{rid}/resolve", headers=_auth(1001)).status_code == 204
    assert c.get("/admin/reports", headers=_auth(1001)).json() == []
    # resolving again is a 404 (already resolved)
    assert c.post(f"/admin/reports/{rid}/resolve", headers=_auth(1001)).status_code == 404
