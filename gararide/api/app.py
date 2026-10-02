"""FastAPI application factory."""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request

from pydantic import BaseModel

from ..config import CONFIG
from ..copy import strings as copy_
from ..places import all_places
from ..users import get_user as get_user_, reconcile_role, set_consent, set_lang
from . import admin, driver, rider, routes, saved
from .deps import current_user, get_conn
from .schemas import Me, Place


class LangIn(BaseModel):
    lang: str


class SupportIn(BaseModel):
    message: str


def create_app(conn, bot_token: str, admin_ids=frozenset(), lifespan=None) -> FastAPI:
    app = FastAPI(title="Gara Ride API", lifespan=lifespan)
    app.state.conn = conn
    app.state.bot_token = bot_token
    app.state.admin_ids = admin_ids
    app.include_router(driver.router)
    app.include_router(rider.router)
    app.include_router(routes.router)
    app.include_router(saved.router)
    app.include_router(admin.router)

    @app.get("/me", response_model=Me)
    def me(request: Request, user=Depends(current_user), conn=Depends(get_conn)):
        # Catch up a rider who was desk-verified as a driver after registering.
        user = reconcile_role(conn, user["telegram_id"]) or user
        return Me(
            telegram_id=user["telegram_id"], full_name=user["full_name"],
            phone=user["phone"], role=user["role"],
            tower=user["tower"] if user["role"] == "driver" else None,
            car_model=user["car_model"], plate=user["plate"],
            car_seats=user["car_seats"], women_only=bool(user["women_only"]),
            women_present=bool(user["women_present"]),
            is_admin=user["telegram_id"] in request.app.state.admin_ids,
            lang=user["lang"], consented=user["consented_at"] is not None)

    @app.post("/me/consent", status_code=204)
    def me_consent(user=Depends(current_user), conn=Depends(get_conn)):
        set_consent(conn, user["telegram_id"])

    @app.post("/me/lang", status_code=204)
    def me_lang(body: LangIn, user=Depends(current_user), conn=Depends(get_conn)):
        # Drives both the bot's messages and the Mini App's copy.
        set_lang(conn, user["telegram_id"], body.lang)

    @app.post("/support", status_code=204)
    def support(body: SupportIn, request: Request, user=Depends(current_user),
                conn=Depends(get_conn)):
        from .push import notify
        from ..ratelimit import allow
        text = (body.message or "").strip()[:800]
        if not text:
            return
        if not allow(f"support:{user['telegram_id']}", 3, 300):
            raise HTTPException(status_code=429, detail="rate_limited")
        for admin_id in request.app.state.admin_ids:
            adm = get_user_(conn, admin_id)
            lang = adm["lang"] if adm else "am"
            notify(request.app, admin_id, copy_(lang).SUPPORT_MSG.format(
                name=user["full_name"], phone=user["phone"], msg=text))

    @app.get("/places", response_model=list[Place])
    def places(user=Depends(current_user), conn=Depends(get_conn)):
        return [Place(id=p["id"], slug=p["slug"], name_am=p["name_am"],
                      name_en=p["name_en"], sort_order=p["sort_order"])
                for p in all_places(conn, CONFIG.corridor_id)]

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app
