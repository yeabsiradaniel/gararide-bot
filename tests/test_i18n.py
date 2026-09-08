import pytest
from fastapi.testclient import TestClient

from gararide.api.app import create_app
from gararide.copy import strings
from gararide.users import get_user, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def client(seeded):
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    return seeded, TestClient(create_app(seeded, BOT_TOKEN))


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def test_new_user_defaults_to_amharic(client):
    _, c = client
    assert c.get("/me", headers=_auth(2001)).json()["lang"] == "am"


def test_setting_language_persists_for_bot_and_app(client):
    conn, c = client
    assert c.post("/me/lang", headers=_auth(2001), json={"lang": "en"}).status_code == 204
    # the Mini App sees it
    assert c.get("/me", headers=_auth(2001)).json()["lang"] == "en"
    # and the bot reads the same stored value
    assert get_user(conn, 2001)["lang"] == "en"


def test_bad_language_falls_back_to_amharic(client):
    conn, c = client
    c.post("/me/lang", headers=_auth(2001), json={"lang": "fr"})
    assert get_user(conn, 2001)["lang"] == "am"


def test_copy_selector_picks_the_right_module():
    assert strings("en").REGISTERED == "You're registered 🎉"
    assert strings("am").REGISTERED == "ተመዝግበዋል 🎉"
    assert strings(None).REGISTERED == strings("am").REGISTERED  # default Amharic
