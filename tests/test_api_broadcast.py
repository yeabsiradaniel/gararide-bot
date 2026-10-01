import pytest
from fastapi.testclient import TestClient

from gararide.api.app import create_app
from gararide.users import import_allowlist, register, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def client(seeded):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register(seeded, telegram_id=1001, phone="0911223344")                     # driver
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="A")  # rider
    register_rider(seeded, telegram_id=2002, phone="0999999998", full_name="B")  # rider
    app = create_app(seeded, BOT_TOKEN, admin_ids=frozenset({1001}))
    return seeded, TestClient(app)


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def test_broadcast_to_riders_counts_only_riders(client):
    _, c = client
    r = c.post("/admin/broadcast", headers=_auth(1001),
               json={"audience": "riders", "message": "no service tomorrow"})
    assert r.status_code == 200 and r.json()["sent"] == 2


def test_broadcast_to_everyone(client):
    _, c = client
    r = c.post("/admin/broadcast", headers=_auth(1001),
               json={"audience": "all", "message": "hi all"})
    assert r.json()["sent"] == 3


def test_blank_broadcast_sends_to_nobody(client):
    _, c = client
    assert c.post("/admin/broadcast", headers=_auth(1001),
                  json={"audience": "all", "message": "  "}).json()["sent"] == 0


def test_non_admin_cannot_broadcast(client):
    _, c = client
    assert c.post("/admin/broadcast", headers=_auth(2001),
                  json={"audience": "all", "message": "x"}).status_code == 403
