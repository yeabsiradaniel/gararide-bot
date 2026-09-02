"""Telegram Mini App initData validation.

The Mini App sends Telegram.WebApp.initData with every request. It is a signed
query string; we recompute the HMAC with the bot token and compare. Identity is
NEVER taken from the request body — only from validated initData (spec §2).
Ref: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
from __future__ import annotations

import hashlib
import hmac
import json
from urllib.parse import parse_qsl


class InvalidInitData(Exception):
    """The initData signature did not validate against the bot token."""


def parse_init_data(raw: str, bot_token: str) -> dict:
    pairs = dict(parse_qsl(raw, keep_blank_values=True))
    received = pairs.pop("hash", None)
    if received is None:
        raise InvalidInitData("no hash")
    data_check = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise InvalidInitData("bad hash")
    user_raw = pairs.get("user")
    if not user_raw:
        raise InvalidInitData("no user")
    return json.loads(user_raw)
