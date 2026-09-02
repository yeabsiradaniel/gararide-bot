import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from gararide.api.auth import InvalidInitData, parse_init_data

BOT_TOKEN = "123456:TEST"


def make_init_data(user: dict, token: str = BOT_TOKEN) -> str:
    fields = {"auth_date": str(int(time.time())),
              "user": json.dumps(user, separators=(",", ":"))}
    data_check = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, data_check.encode(),
                              hashlib.sha256).hexdigest()
    return urlencode(fields)


def test_valid_init_data_returns_the_user():
    raw = make_init_data({"id": 1001, "first_name": "Yeab"})
    assert parse_init_data(raw, BOT_TOKEN)["id"] == 1001


def test_tampered_hash_is_rejected():
    raw = make_init_data({"id": 1001}) + "&extra=1"
    with pytest.raises(InvalidInitData):
        parse_init_data(raw, BOT_TOKEN)


def test_wrong_token_is_rejected():
    raw = make_init_data({"id": 1001}, token="other")
    with pytest.raises(InvalidInitData):
        parse_init_data(raw, BOT_TOKEN)
