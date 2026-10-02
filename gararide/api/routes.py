"""Driver saved-route endpoints. Each requires a driver (403 for riders)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..driver_routes import (deactivate_route, get_route, post_route_tomorrow,
                             routes_for, save_route, tomorrow_departure)
from ..fares import fare
from ..places import origin_place, place_by_id
from ..trips import post_block_reason
from ..trips import dropoffs as trip_dropoffs
from .deps import get_conn, require_driver

router = APIRouter()


class SaveRoute(BaseModel):
    dest_place_id: int
    dropoff_place_ids: list[int]
    depart_time: str  # 'HH:MM' local
    seats: int
    days_mask: int = 0


def _out(conn, r) -> dict:
    return {"id": r["id"], "dest_place_id": r["dest_place_id"],
            "dest_name_am": place_by_id(conn, r["dest_place_id"])["name_am"],
            "depart_time": r["depart_time"], "seats": r["seats"],
            "days_mask": r["days_mask"]}


@router.get("/routes")
def list_routes(user=Depends(require_driver), conn=Depends(get_conn)):
    return [_out(conn, r) for r in routes_for(conn, user["telegram_id"])]


@router.post("/routes", status_code=201)
def create_route(body: SaveRoute, user=Depends(require_driver), conn=Depends(get_conn)):
    cap = user["car_seats"] or 0
    if not 1 <= body.seats <= cap:
        raise HTTPException(status_code=422, detail=f"seats must be 1..{cap}")
    rid = save_route(conn, driver_id=user["telegram_id"],
                     dest_place_id=body.dest_place_id,
                     dropoff_place_ids=body.dropoff_place_ids,
                     depart_time=body.depart_time, seats=body.seats,
                     days_mask=body.days_mask)
    return _out(conn, get_route(conn, rid))


def _owned(conn, route_id, user):
    r = get_route(conn, route_id)
    if r is None or r["driver_id"] != user["telegram_id"] or not r["active"]:
        raise HTTPException(status_code=404, detail="no such route")
    return r


@router.delete("/routes/{route_id}", status_code=204)
def remove_route(route_id: int, user=Depends(require_driver), conn=Depends(get_conn)):
    _owned(conn, route_id, user)
    deactivate_route(conn, route_id)


@router.post("/routes/{route_id}/post")
def post_route(route_id: int, user=Depends(require_driver), conn=Depends(get_conn)):
    r = _owned(conn, route_id, user)
    depart_dt = tomorrow_departure(r["depart_time"])
    reason = post_block_reason(depart_dt)
    if reason:
        raise HTTPException(status_code=422, detail=reason)
    depart = depart_dt.isoformat(timespec="seconds")
    # A double-tap must not post the same ride twice.
    existing = conn.execute(
        "SELECT id FROM trips WHERE driver_id = ? AND dest_place_id = ?"
        "   AND depart_at = ? AND status = 'open'",
        (user["telegram_id"], r["dest_place_id"], depart)).fetchone()
    already = existing is not None
    trip_id = existing["id"] if already else post_route_tomorrow(conn, r)
    origin = origin_place(conn)
    fares = [{"place_id": s["id"], "slug": s["slug"], "name_am": s["name_am"],
              "fare": fare(conn, origin["id"], s["id"])}
             for s in trip_dropoffs(conn, trip_id)]
    return {"trip_id": trip_id, "already": already, "depart_at": depart,
            "seats": r["seats"],
            "dest_name_am": place_by_id(conn, r["dest_place_id"])["name_am"],
            "fares": fares}
