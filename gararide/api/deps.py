"""Request-scoped dependencies: the authenticated user and the DB connection."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request

from ..users import get_user
from .auth import InvalidInitData, parse_init_data


def get_conn(request: Request):
    return request.app.state.conn


def current_user(request: Request,
                 authorization: str | None = Header(default=None),
                 conn=Depends(get_conn)):
    """Validate initData from the Authorization header ('tma <initData>')."""
    if not authorization or not authorization.startswith("tma "):
        raise HTTPException(status_code=401, detail="missing initData")
    try:
        tg = parse_init_data(authorization[4:], request.app.state.bot_token)
    except InvalidInitData:
        raise HTTPException(status_code=401, detail="invalid initData")
    user = get_user(conn, tg["id"])
    # A removed (deactivated) user is treated as unregistered — the app bounces
    # them to the register screen instead of letting them keep operating.
    if user is None or not user["active"]:
        raise HTTPException(status_code=404, detail="not registered")
    return user


def require_driver(user=Depends(current_user)):
    if user["role"] != "driver":
        raise HTTPException(status_code=403, detail="drivers only")
    return user
