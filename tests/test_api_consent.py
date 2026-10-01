import pytest
from fastapi.testclient import TestClient

from gararide.api.app import create_app
from gararide.users import import_allowlist, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def client(seeded):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    return seeded, TestClient(create_app(seeded, BOT_TOKEN))


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def test_consent_starts_false_then_sticks(client):
    _, c = client
    assert c.get("/me", headers=_auth(2001)).json()["consented"] is False
    assert c.post("/me/consent", headers=_auth(2001)).status_code == 204
    assert c.get("/me", headers=_auth(2001)).json()["consented"] is True
