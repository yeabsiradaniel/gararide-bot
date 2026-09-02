import pytest
from fastapi.testclient import TestClient

from gararide.api.app import create_app
from gararide.places import place_by_slug
from gararide.users import import_allowlist, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def client(seeded):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    return seeded, TestClient(create_app(seeded, BOT_TOKEN))


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def test_save_list_and_deactivate_round_trip(client):
    conn, c = client
    kaz = place_by_slug(conn, "kazanchis")["id"]
    sid = c.post("/me/saved", headers=_auth(2001), json={
        "dest_place_id": kaz, "depart_time": "07:00", "days_mask": 31}).json()["id"]
    listed = c.get("/me/saved", headers=_auth(2001)).json()
    assert len(listed) == 1 and listed[0]["depart_time"] == "07:00"
    assert c.post(f"/me/saved/{sid}/deactivate", headers=_auth(2001)).status_code == 204
    assert c.get("/me/saved", headers=_auth(2001)).json() == []
