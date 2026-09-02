"""Rider endpoints. Role-agnostic — a verified driver may also ride.

Search never returns a bare empty list: when nothing matches exactly it also
carries near-misses and the count of neighbours waiting (spec §5).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..blocks import block
from ..bookings import (NotOffered, TripFull, book, bookings_for_rider,
                        cancel_booking)
from ..matching import find_trips, near_misses
from ..places import place_by_id
from ..requests import demand_count, post_request
from ..trips import get_trip
from ..users import get_user, set_women_only
from .deps import current_user, get_conn

router = APIRouter()

BAY = "Bay Alpha"


def _window(when: str) -> tuple[datetime, datetime]:
    now = datetime.now()
    if when == "today":
        return now, now.replace(hour=23, minute=59, second=59, microsecond=0)
    if when == "weekend":
        days = (5 - now.weekday()) % 7
        sat = (now + timedelta(days=days)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        return sat, (sat + timedelta(days=1)).replace(
            hour=23, minute=59, second=59, microsecond=0)
    base = now + timedelta(days=1)  # tomorrow_morning (default)
    return (base.replace(hour=6, minute=0, second=0, microsecond=0),
            base.replace(hour=9, minute=0, second=0, microsecond=0))


@router.get("/trips/search")
def search(dest_place_id: int, when: str = "tomorrow_morning",
           user=Depends(current_user), conn=Depends(get_conn)):
    start, end = _window(when)
    rid = user["telegram_id"]
    matches = find_trips(conn, rider_id=rid, dest_place_id=dest_place_id,
                         window_start=start, window_end=end)
    conn.execute(
        "INSERT INTO search_log (rider_id, dest_place_id, window_start,"
        " window_end, results, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (rid, dest_place_id, start.isoformat(timespec="seconds"),
         end.isoformat(timespec="seconds"), len(matches),
         datetime.now().isoformat(timespec="seconds")))
    conn.commit()

    def m2(m):
        d = get_user(conn, m.driver_id)
        return {"trip_id": m.trip_id, "driver_name": d["full_name"],
                "driver_tower": d["tower"] or None,
                "depart_at": m.depart_at.isoformat(timespec="seconds"),
                "seats_left": m.seats_left, "fare": m.fare}

    result = {"matches": [m2(m) for m in matches], "near_misses": [],
              "demand_count": 0}
    if not matches:
        nms = near_misses(conn, rider_id=rid, dest_place_id=dest_place_id,
                          window_start=start, window_end=end)[:4]
        result["near_misses"] = [{
            "trip_id": m.trip_id, "driver_name": get_user(conn, m.driver_id)["full_name"],
            "depart_at": m.depart_at.isoformat(timespec="seconds"), "fare": m.fare,
            "dest_place_id": m.dest_place_id,
            "dest_name_am": place_by_id(conn, m.dest_place_id)["name_am"],
            "reason": m.reason} for m in nms]
        result["demand_count"] = demand_count(conn, dest_place_id, start, end)
    return result


class Booking(BaseModel):
    trip_id: int
    to_place_id: int


def _card(conn, booking) -> dict:
    trip = get_trip(conn, booking["trip_id"])
    d = get_user(conn, trip["driver_id"])
    dest = place_by_id(conn, booking["to_place_id"])
    return {"booking_id": booking["id"], "trip_id": trip["id"],
            "depart_at": trip["depart_at"], "bay": BAY,
            "driver_name": d["full_name"], "driver_tower": d["tower"],
            "car_model": d["car_model"], "plate": d["plate"], "phone": d["phone"],
            "dest_place_id": dest["id"], "dest_name_am": dest["name_am"],
            "fare": booking["fare"]}


@router.post("/bookings", status_code=201)
def create_booking(body: Booking, user=Depends(current_user),
                   conn=Depends(get_conn)):
    try:
        b = book(conn, trip_id=body.trip_id, rider_id=user["telegram_id"],
                 to_place_id=body.to_place_id)
    except (TripFull, NotOffered):
        raise HTTPException(status_code=409, detail="seat unavailable")
    return _card(conn, b)


@router.post("/bookings/{booking_id}/cancel", status_code=204)
def cancel_my_booking(booking_id: int, user=Depends(current_user),
                      conn=Depends(get_conn)):
    cancel_booking(conn, booking_id)


@router.get("/bookings/mine")
def my_bookings(user=Depends(current_user), conn=Depends(get_conn)):
    return [_card(conn, b) for b in bookings_for_rider(conn, user["telegram_id"])]


class NewRequest(BaseModel):
    dest_place_id: int
    window_start: str
    window_end: str


@router.post("/requests", status_code=201)
def create_request(body: NewRequest, user=Depends(current_user),
                   conn=Depends(get_conn)):
    rid = post_request(conn, rider_id=user["telegram_id"],
                       dest_place_id=body.dest_place_id,
                       window_start=datetime.fromisoformat(body.window_start),
                       window_end=datetime.fromisoformat(body.window_end))
    return {"request_id": rid}


class BlockBody(BaseModel):
    trip_id: int


@router.post("/blocks", status_code=204)
def block_driver(body: BlockBody, user=Depends(current_user),
                 conn=Depends(get_conn)):
    trip = get_trip(conn, body.trip_id)
    if trip is not None:
        block(conn, user["telegram_id"], trip["driver_id"])


class WomenOnly(BaseModel):
    women_only: bool
    women_present: bool


@router.post("/me/women-only", status_code=204)
def women_only(body: WomenOnly, user=Depends(current_user),
               conn=Depends(get_conn)):
    set_women_only(conn, user["telegram_id"], women_only=body.women_only,
                   women_present=body.women_present)
