import pytest
from fastapi.testclient import TestClient

from gararide.api import driver as driver_mod
from gararide.api import rider as rider_mod
from gararide.api.app import create_app
from gararide.places import place_by_slug
from gararide.users import import_allowlist, register, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def client(seeded, monkeypatch):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register(seeded, telegram_id=1001, phone="0911223344")       # driver, 4 seats
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    sent: list[tuple[int, str]] = []
    rec = lambda app, chat_id, text: sent.append((chat_id, text))  # noqa: E731
    monkeypatch.setattr(rider_mod, "notify", rec)
    monkeypatch.setattr(driver_mod, "notify", rec)
    return seeded, TestClient(create_app(seeded, BOT_TOKEN)), sent


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def _post_trip(conn, c):
    kaz = place_by_slug(conn, "kazanchis")["id"]
    r = c.post("/trips", headers=_auth(1001), json={
        "dest_place_id": kaz, "dropoff_place_ids": [], "seats": 2,
        "depart_at": "2999-01-01T07:00:00"})
    return r.json()["trip_id"], kaz


def test_booking_notifies_the_driver(client):
    conn, c, sent = client
    trip_id, kaz = _post_trip(conn, c)
    c.post("/bookings", headers=_auth(2001), json={"trip_id": trip_id, "to_place_id": kaz})
    assert any(chat == 1001 and "Fan" in text for chat, text in sent)


def test_cancelling_a_booking_notifies_the_driver(client):
    conn, c, sent = client
    trip_id, kaz = _post_trip(conn, c)
    bid = c.post("/bookings", headers=_auth(2001),
                 json={"trip_id": trip_id, "to_place_id": kaz}).json()["booking_id"]
    sent.clear()
    c.post(f"/bookings/{bid}/cancel", headers=_auth(2001))
    assert any(chat == 1001 for chat, _ in sent)


def test_driver_cancelling_a_trip_notifies_the_rider(client):
    conn, c, sent = client
    trip_id, kaz = _post_trip(conn, c)
    c.post("/bookings", headers=_auth(2001), json={"trip_id": trip_id, "to_place_id": kaz})
    sent.clear()
    c.post(f"/trips/{trip_id}/cancel", headers=_auth(1001))
    assert any(chat == 2001 for chat, _ in sent)
