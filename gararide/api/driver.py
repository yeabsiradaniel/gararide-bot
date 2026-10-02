"""Driver endpoints. All require a driver; a rider calling them gets 403."""
from __future__ import annotations

from datetime import datetime
from .. import clock

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..bookings import bookings_for_trip, mark_no_show, mark_paid
from ..config import CONFIG
from ..copy import strings as copy
from ..fares import fare
from ..fmt import fmt_when
from ..places import origin_place, place_by_id
from ..requests import fill_request, open_requests, requests_matching_trip
from ..trips import (InvalidDropoff, booking_open, cancel_trip, dropoffs,
                     dwell_expired, get_trip, intermediate_dropoffs, mark_arrived,
                     mark_on_way, post_block_reason, post_trip, seats_left,
                     trips_by_driver, update_trip)
from ..users import get_user
from .deps import get_conn, require_driver
from .push import notify

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
def create_trip(body: PostTrip, request: Request, user=Depends(require_driver),
                conn=Depends(get_conn)):
    cap = user["car_seats"] or 0
    if not 1 <= body.seats <= cap:
        raise HTTPException(status_code=422, detail=f"seats must be 1..{cap}")
    reason = post_block_reason(datetime.fromisoformat(body.depart_at))
    if reason:
        raise HTTPException(status_code=422, detail=reason)
    try:
        trip_id = post_trip(
            conn, driver_id=user["telegram_id"], dest_place_id=body.dest_place_id,
            dropoff_place_ids=body.dropoff_place_ids,
            depart_at=datetime.fromisoformat(body.depart_at),
            seats=body.seats, note=body.note)
    except InvalidDropoff:
        raise HTTPException(status_code=422, detail="invalid drop-off")
    _notify_waiting_riders(request.app, conn, trip_id, body.depart_at)
    origin = origin_place(conn)
    fares = [{"place_id": s["id"], "slug": s["slug"], "name_am": s["name_am"],
              "name_en": s["name_en"], "fare": fare(conn, origin["id"], s["id"])}
             for s in dropoffs(conn, trip_id)]
    return {"trip_id": trip_id, "dest_place_id": body.dest_place_id,
            "depart_at": body.depart_at, "seats": body.seats, "fares": fares}


def _notify_waiting_riders(app, conn, trip_id: int, depart_at: str) -> None:
    """A new trip that covers an open request: tell each waiting rider and close
    their request (this is what the '🔔 tell me when it opens' promise resolves to)."""
    when = fmt_when(datetime.fromisoformat(depart_at))
    for req in requests_matching_trip(conn, trip_id):
        rider = get_user(conn, req["rider_id"])
        if rider:
            p = place_by_id(conn, req["dest_place_id"])
            dest = p["name_en"] if rider["lang"] == "en" else p["name_am"]
            notify(app, rider["telegram_id"],
                   copy(rider["lang"]).TRIP_MATCHED.format(dest=dest, when=when))
        fill_request(conn, req["id"])


class EditTrip(BaseModel):
    depart_at: str
    seats: int
    note: str | None = None


@router.patch("/trips/{trip_id}")
def edit_trip(trip_id: int, body: EditTrip, request: Request,
              user=Depends(require_driver), conn=Depends(get_conn)):
    trip = get_trip(conn, trip_id)
    if trip is None or trip["driver_id"] != user["telegram_id"]:
        raise HTTPException(status_code=404, detail="no such trip")
    if trip["status"] != "open" or trip["arrived_at"]:
        raise HTTPException(status_code=409, detail="trip can no longer be edited")
    if not booking_open(datetime.fromisoformat(trip["depart_at"])):
        # The trip is already locked (within 1h of departure, or a next-day trip
        # past the night-before cutoff) — too late to change it.
        raise HTTPException(status_code=409, detail="roster_locked")
    when = datetime.fromisoformat(body.depart_at)
    reason = post_block_reason(when)
    if reason:
        raise HTTPException(status_code=422, detail=reason)
    cap = user["car_seats"] or 0
    booked = len(bookings_for_trip(conn, trip_id))
    if not booked <= body.seats <= cap:
        raise HTTPException(status_code=422,
                            detail=f"seats must be {booked}..{cap} (riders already booked)")
    note = (body.note or "").strip()[:200] or None
    time_changed = trip["depart_at"] != body.depart_at
    update_trip(conn, trip_id, depart_at=when, seats=body.seats, note=note)
    if time_changed:
        for b in bookings_for_trip(conn, trip_id):
            rider = get_user(conn, b["rider_id"])
            if rider:
                p = place_by_id(conn, b["to_place_id"])
                dest = p["name_en"] if rider["lang"] == "en" else p["name_am"]
                notify(request.app, rider["telegram_id"],
                       copy(rider["lang"]).TRIP_UPDATED.format(
                           dest=dest, when=fmt_when(when)))
    return {"trip_id": trip_id, "depart_at": body.depart_at,
            "seats": body.seats, "note": note}


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
                "to_name_en": place_by_id(conn, b["to_place_id"])["name_en"],
                "fare": b["fare"], "phone": r["phone"], "paid": bool(b["paid"])})
        out.append({
            "trip_id": t["id"], "dest_place_id": t["dest_place_id"],
            "dest_name_am": place_by_id(conn, t["dest_place_id"])["name_am"],
            "dest_name_en": place_by_id(conn, t["dest_place_id"])["name_en"],
            "depart_at": t["depart_at"], "seats_total": t["seats_total"],
            "note": t["note"],
            "seats_left": seats_left(conn, t["id"]), "passengers": passengers,
            "arrived_at": t["arrived_at"], "dwell_minutes": CONFIG.dwell_minutes,
            "otw_at": t["otw_at"], "otw_eta": t["otw_eta"]})
    return out


class OnWay(BaseModel):
    eta_minutes: int


@router.post("/trips/{trip_id}/on-my-way")
def on_my_way(trip_id: int, body: OnWay, request: Request,
              user=Depends(require_driver), conn=Depends(get_conn)):
    if not 1 <= body.eta_minutes <= 60:
        raise HTTPException(status_code=422, detail="eta_minutes must be 1..60")
    trip = get_trip(conn, trip_id)
    if trip is None or trip["driver_id"] != user["telegram_id"]:
        raise HTTPException(status_code=404, detail="no such trip")
    at = mark_on_way(conn, trip_id, body.eta_minutes)
    for b in bookings_for_trip(conn, trip_id):
        rider = get_user(conn, b["rider_id"])
        if rider:
            notify(request.app, rider["telegram_id"],
                   copy(rider["lang"]).ON_THE_WAY.format(mins=body.eta_minutes))
    return {"otw_at": at, "otw_eta": body.eta_minutes}


@router.post("/trips/{trip_id}/arrived")
def arrived(trip_id: int, request: Request, user=Depends(require_driver),
            conn=Depends(get_conn)):
    trip = get_trip(conn, trip_id)
    if trip is None or trip["driver_id"] != user["telegram_id"]:
        raise HTTPException(status_code=404, detail="no such trip")
    at = mark_arrived(conn, trip_id)
    # Start the boarding clock for every booked rider.
    for b in bookings_for_trip(conn, trip_id):
        rider = get_user(conn, b["rider_id"])
        if rider:
            notify(request.app, rider["telegram_id"],
                   copy(rider["lang"]).BOARDING_OPEN.format(mins=CONFIG.dwell_minutes))
    return {"arrived_at": at, "dwell_minutes": CONFIG.dwell_minutes}


@router.post("/trips/{trip_id}/cancel", status_code=204)
def cancel(trip_id: int, request: Request, user=Depends(require_driver),
           conn=Depends(get_conn)):
    trip = get_trip(conn, trip_id)
    # Gather the riders before their bookings are cancelled, then tell them.
    riders = [(get_user(conn, b["rider_id"]), b["to_place_id"])
              for b in bookings_for_trip(conn, trip_id)]
    cancel_trip(conn, trip_id)
    when = fmt_when(datetime.fromisoformat(trip["depart_at"])) if trip else ""
    for rider, to_place_id in riders:
        if not rider:
            continue
        p = place_by_id(conn, to_place_id)
        dest = p["name_en"] if rider["lang"] == "en" else p["name_am"]
        notify(request.app, rider["telegram_id"],
               copy(rider["lang"]).TRIP_CANCELLED.format(dest=dest, when=when))


@router.get("/requests/near")
def requests_near(user=Depends(require_driver), conn=Depends(get_conn)):
    out = []
    for req in open_requests(conn, for_driver_id=user["telegram_id"]):
        r = get_user(conn, req["rider_id"])
        out.append({
            "request_id": req["id"], "rider_name": r["full_name"],
            "dest_place_id": req["dest_place_id"],
            "dest_name_am": place_by_id(conn, req["dest_place_id"])["name_am"],
            "dest_name_en": place_by_id(conn, req["dest_place_id"])["name_en"],
            "window_start": req["window_start"], "window_end": req["window_end"]})
    return out


def _own_booking(conn, booking_id: int, driver_id: int):
    b = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    trip = get_trip(conn, b["trip_id"]) if b else None
    if b is None or trip is None or trip["driver_id"] != driver_id:
        raise HTTPException(status_code=404, detail="no such booking")
    return b, trip


@router.post("/bookings/{booking_id}/paid", status_code=204)
def paid(booking_id: int, user=Depends(require_driver), conn=Depends(get_conn)):
    _own_booking(conn, booking_id, user["telegram_id"])
    mark_paid(conn, booking_id)


@router.post("/bookings/{booking_id}/no-show", status_code=204)
def no_show(booking_id: int, user=Depends(require_driver), conn=Depends(get_conn)):
    _, trip = _own_booking(conn, booking_id, user["telegram_id"])
    if not dwell_expired(trip):
        raise HTTPException(status_code=409, detail="too_early")  # wait out the dwell
    mark_no_show(conn, booking_id)
