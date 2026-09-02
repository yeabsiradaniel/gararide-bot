from fastapi.testclient import TestClient

from gararide.api.app import create_app
from tests.test_api_auth import BOT_TOKEN


def test_healthz_is_open(seeded):
    c = TestClient(create_app(seeded, BOT_TOKEN))
    r = c.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
