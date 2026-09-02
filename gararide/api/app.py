"""FastAPI application factory."""
from __future__ import annotations

from fastapi import Depends, FastAPI, Request

from ..config import CONFIG
from ..places import all_places
from . import admin, driver, rider, routes, saved
from .deps import current_user, get_conn
from .schemas import Me, Place


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
    def me(request: Request, user=Depends(current_user)):
        return Me(
            telegram_id=user["telegram_id"], full_name=user["full_name"],
            role=user["role"],
            tower=user["tower"] if user["role"] == "driver" else None,
            car_model=user["car_model"], plate=user["plate"],
            car_seats=user["car_seats"], women_only=bool(user["women_only"]),
            women_present=bool(user["women_present"]),
            is_admin=user["telegram_id"] in request.app.state.admin_ids)

    @app.get("/places", response_model=list[Place])
    def places(user=Depends(current_user), conn=Depends(get_conn)):
        return [Place(id=p["id"], slug=p["slug"], name_am=p["name_am"],
                      name_en=p["name_en"], sort_order=p["sort_order"])
                for p in all_places(conn, CONFIG.corridor_id)]

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app
