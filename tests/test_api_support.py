import pytest
from fastapi.testclient import TestClient

from gararide.api.app import create_app
from gararide.users import import_allowlist, register, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def client(seeded):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register(seeded, telegram_id=1001, phone="0911223344")
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    return seeded, TestClient(create_app(seeded, BOT_TOKEN, admin_ids=frozenset({1001})))


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def test_me_includes_phone(client):
    _, c = client
    me = c.get("/me", headers=_auth(2001)).json()
    assert me["phone"].endswith("999999999")


def test_support_accepts_a_message(client):
    _, c = client
    # no bot attached in tests, so the push is a no-op; endpoint still returns 204
    r = c.post("/support", headers=_auth(2001), json={"message": "my seat vanished"})
    assert r.status_code == 204


def test_support_ignores_blank(client):
    _, c = client
    assert c.post("/support", headers=_auth(2001), json={"message": "   "}).status_code == 204


def test_support_is_rate_limited(client):
    _, c = client
    for _ in range(3):
        assert c.post("/support", headers=_auth(2001),
                      json={"message": "help"}).status_code == 204
    # 4th within the window is blocked
    assert c.post("/support", headers=_auth(2001),
                  json={"message": "help"}).status_code == 429
