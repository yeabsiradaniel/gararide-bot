"""Driver endpoints. All require a driver; a rider calling them gets 403."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..bookings import bookings_for_trip, mark_no_show, mark_paid
from ..fares import fare
from ..places import origin_place, place_by_id
from ..requests import open_requests
from ..trips import (InvalidDropoff, cancel_trip, dropoffs,
                     intermediate_dropoffs, post_trip, seats_left,
                     trips_by_driver)
from ..users import get_user
from .deps import get_conn, require_driver

router = APIRouter()


class PostTrip(BaseModel):
    dest_place_id: int
    dropoff_place_ids: list[int]
    depart_at: str  # ISO naive local time
    seats: int
    note: str | None = None


def _place(p) -> dict:
    return {"id": p["id"], "slug": p["slug"], "name_am": p["name_am"],
            "name_en": p["name_en"], "sort_order": p["sort_order"]}


@router.get("/trips/{dest_id}/dropoff-options")
def dropoff_options(dest_id: int, user=Depends(require_driver),
                    conn=Depends(get_conn)):
    return {
        "intermediate": [_place(place_by_id(conn, i))
                         for i in intermediate_dropoffs(conn, dest_id)],
        "destination": _place(place_by_id(conn, dest_id)),
    }


@router.post("/trips", status_code=201)
def create_trip(body: PostTrip, user=Depends(require_driver),
                conn=Depends(get_conn)):
    cap = user["car_seats"] or 0
    if not 1 <= body.seats <= cap:
        raise HTTPException(status_code=422, detail=f"seats must be 1..{cap}")
    try:
        trip_id = post_trip(
            conn, driver_id=user["telegram_id"], dest_place_id=body.dest_place_id,
            dropoff_place_ids=body.dropoff_place_ids,
            depart_at=datetime.fromisoformat(body.depart_at),
            seats=body.seats, note=body.note)
    except InvalidDropoff:
        raise HTTPException(status_code=422, detail="invalid drop-off")
    origin = origin_place(conn)
    fares = [{"place_id": s["id"], "slug": s["slug"], "name_am": s["name_am"],
              "fare": fare(conn, origin["id"], s["id"])}
             for s in dropoffs(conn, trip_id)]
    return {"trip_id": trip_id, "dest_place_id": body.dest_place_id,
            "depart_at": body.depart_at, "seats": body.seats, "fares": fares}


@router.get("/trips/mine")
def my_trips(user=Depends(require_driver), conn=Depends(get_conn)):
    out = []
    for t in trips_by_driver(conn, user["telegram_id"]):
        passengers = []
        for b in bookings_for_trip(conn, t["id"]):
            r = get_user(conn, b["rider_id"])
            passengers.append({
                "booking_id": b["id"], "name": r["full_name"],
                "tower": r["tower"] or None, "to_place_id": b["to_place_id"],
                "to_name_am": place_by_id(conn, b["to_place_id"])["name_am"],
                "fare": b["fare"], "phone": r["phone"], "paid": bool(b["paid"])})
        out.append({
            "trip_id": t["id"], "dest_place_id": t["dest_place_id"],
            "dest_name_am": place_by_id(conn, t["dest_place_id"])["name_am"],
            "depart_at": t["depart_at"], "seats_total": t["seats_total"],
            "seats_left": seats_left(conn, t["id"]), "passengers": passengers})
    return out


@router.post("/trips/{trip_id}/cancel", status_code=204)
def cancel(trip_id: int, user=Depends(require_driver), conn=Depends(get_conn)):
    cancel_trip(conn, trip_id)


@router.get("/requests/near")
def requests_near(user=Depends(require_driver), conn=Depends(get_conn)):
    out = []
    for req in open_requests(conn, for_driver_id=user["telegram_id"]):
        r = get_user(conn, req["rider_id"])
        out.append({
            "request_id": req["id"], "rider_name": r["full_name"],
            "dest_place_id": req["dest_place_id"],
            "dest_name_am": place_by_id(conn, req["dest_place_id"])["name_am"],
            "window_start": req["window_start"], "window_end": req["window_end"]})
    return out


@router.post("/bookings/{booking_id}/paid", status_code=204)
def paid(booking_id: int, user=Depends(require_driver), conn=Depends(get_conn)):
    mark_paid(conn, booking_id)


@router.post("/bookings/{booking_id}/no-show", status_code=204)
def no_show(booking_id: int, user=Depends(require_driver), conn=Depends(get_conn)):
    mark_no_show(conn, booking_id)
