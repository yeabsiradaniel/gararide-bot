import pytest
from fastapi.testclient import TestClient

from gararide.api.app import create_app
from gararide.users import import_allowlist, register, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def client(seeded):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register(seeded, telegram_id=1001, phone="0911223344")       # driver
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    return TestClient(create_app(seeded, BOT_TOKEN))


def _auth(user):
    return {"Authorization": "tma " + make_init_data(user)}


def test_me_returns_driver_with_tower(client):
    r = client.get("/me", headers=_auth({"id": 1001, "first_name": "Yeab"}))
    assert r.status_code == 200
    assert r.json()["role"] == "driver"
    assert r.json()["tower"] == "B4"
    assert r.json()["car_seats"] == 4


def test_me_hides_tower_for_riders(client):
    r = client.get("/me", headers=_auth({"id": 2001, "first_name": "Fan"}))
    assert r.json()["role"] == "rider"
    assert r.json()["tower"] is None


def test_unregistered_user_gets_404(client):
    r = client.get("/me", headers=_auth({"id": 9999, "first_name": "Nobody"}))
    assert r.status_code == 404


def test_missing_initdata_is_401(client):
    assert client.get("/me").status_code == 401


def test_places_lists_the_corridor(client):
    r = client.get("/places", headers=_auth({"id": 1001}))
    assert [p["slug"] for p in r.json()] == \
        ["ayat49", "cmc", "megenagna", "aratkilo", "kazanchis"]
