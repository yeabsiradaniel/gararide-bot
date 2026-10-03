"""Rider endpoints. Role-agnostic — a verified driver may also ride.

Search never returns a bare empty list: when nothing matches exactly it also
carries near-misses and the count of neighbours waiting (spec §5).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from .. import clock

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..blocks import block
from ..ratelimit import allow
from ..ratings import rate, rating_for_booking
from ..reports import REASONS, file_report
from ..fmt import fmt_when
from .. import waitlist
from ..bookings import (BookingClosed, NotOffered, TripFull, book,
                        bookings_for_rider, cancel_booking,
                        cancelled_upcoming_for_rider, history_for_rider)
from ..config import CONFIG
from ..copy import strings as copy
from ..matching import find_trips, near_misses
from ..places import place_by_id
from ..requests import demand_count, fill_own_request, post_request
from ..trips import get_trip
from ..users import get_user, set_women_only
from .deps import current_user, get_conn
from .push import notify

router = APIRouter()

BAY = "Bay Alpha"


def _place_name(conn, place_id: int, lang: str) -> str:
    p = place_by_id(conn, place_id)
    return p["name_en"] if lang == "en" else p["name_am"]


def _window(when: str) -> tuple[datetime, datetime]:
    now = clock.now()
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
         clock.now().isoformat(timespec="seconds")))
    conn.commit()

    def _driver_bits(driver_id):  # what the pre-book preview may show — never phone
        d = get_user(conn, driver_id)
        return {"driver_name": d["full_name"], "driver_tower": d["tower"] or None,
                "car_model": d["car_model"], "car_color": d["car_color"], "plate": d["plate"]}

    def m2(m):
        return {"trip_id": m.trip_id,
                "depart_at": m.depart_at.isoformat(timespec="seconds"),
                "seats_left": m.seats_left, "fare": m.fare, **_driver_bits(m.driver_id)}

    result = {"matches": [m2(m) for m in matches], "near_misses": [],
              "demand_count": 0}
    if not matches:
        nms = near_misses(conn, rider_id=rid, dest_place_id=dest_place_id,
                          window_start=start, window_end=end)[:4]
        result["near_misses"] = [{
            "trip_id": m.trip_id,
            "depart_at": m.depart_at.isoformat(timespec="seconds"), "fare": m.fare,
            "dest_place_id": m.dest_place_id,
            "dest_name_am": place_by_id(conn, m.dest_place_id)["name_am"],
            "dest_name_en": place_by_id(conn, m.dest_place_id)["name_en"],
            "reason": m.reason, **_driver_bits(m.driver_id)} for m in nms]
        result["demand_count"] = demand_count(conn, dest_place_id, start, end)
    return result


class Booking(BaseModel):
    trip_id: int
    to_place_id: int


def _card(conn, booking, cancelled: bool = False) -> dict:
    trip = get_trip(conn, booking["trip_id"])
    d = get_user(conn, trip["driver_id"])
    dest = place_by_id(conn, booking["to_place_id"])
    return {"booking_id": booking["id"], "trip_id": trip["id"],
            "depart_at": trip["depart_at"], "bay": BAY,
            "driver_name": d["full_name"], "driver_tower": d["tower"],
            "car_model": d["car_model"], "car_color": d["car_color"],
            "plate": d["plate"], "phone": d["phone"],
            "dest_place_id": dest["id"], "dest_name_am": dest["name_am"],
            "dest_name_en": dest["name_en"],
            "fare": booking["fare"], "cancelled": cancelled,
            "arrived_at": trip["arrived_at"], "dwell_minutes": CONFIG.dwell_minutes,
            "otw_at": trip["otw_at"], "otw_eta": trip["otw_eta"]}


@router.post("/bookings", status_code=201)
def create_booking(body: Booking, request: Request, user=Depends(current_user),
                   conn=Depends(get_conn)):
    # A rider can't hold two bookings whose departures overlap — no being in two
    # cars at once. Checked against existing active bookings on other trips.
    target = get_trip(conn, body.trip_id)
    if target is not None and target["driver_id"] == user["telegram_id"]:
        raise HTTPException(status_code=409, detail="own_trip")  # can't ride your own car
    if target is not None:
        window = CONFIG.overlap_window_minutes * 60
        clash = conn.execute(
            "SELECT 1 FROM bookings b JOIN trips t ON t.id = b.trip_id"
            " WHERE b.rider_id = ? AND b.status = 'booked' AND b.trip_id <> ?"
            "   AND ABS(strftime('%s', t.depart_at) - strftime('%s', ?)) < ?",
            (user["telegram_id"], body.trip_id, target["depart_at"], window),
        ).fetchone()
        if clash is not None:
            raise HTTPException(status_code=409, detail="time_conflict")
    try:
        b = book(conn, trip_id=body.trip_id, rider_id=user["telegram_id"],
                 to_place_id=body.to_place_id)
    except BookingClosed:
        raise HTTPException(status_code=409, detail="booking_closed")
    except (TripFull, NotOffered):
        raise HTTPException(status_code=409, detail="seat unavailable")
    trip = get_trip(conn, b["trip_id"])
    # Booking a seat closes the rider's own open request for the same trip, so it
    # stops inflating the demand count and double-signalling.
    fill_own_request(conn, rider_id=user["telegram_id"],
                     dest_place_id=b["to_place_id"], at=trip["depart_at"])
    # Tell the driver a seat just went.
    driver = get_user(conn, trip["driver_id"])
    if driver:
        notify(request.app, driver["telegram_id"], copy(driver["lang"]).SEAT_BOOKED.format(
            name=user["full_name"],
            dest=_place_name(conn, b["to_place_id"], driver["lang"])))
    return _card(conn, b)


@router.post("/bookings/{booking_id}/cancel", status_code=204)
def cancel_my_booking(booking_id: int, request: Request, user=Depends(current_user),
                      conn=Depends(get_conn)):
    row = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if row is None or row["rider_id"] != user["telegram_id"]:
        raise HTTPException(status_code=404, detail="no such booking")  # not yours
    cancel_booking(conn, booking_id)
    trip = get_trip(conn, row["trip_id"])
    driver = get_user(conn, trip["driver_id"]) if trip else None
    if driver:
        notify(request.app, driver["telegram_id"], copy(driver["lang"]).BOOKING_CANCELLED.format(
            name=user["full_name"],
            dest=_place_name(conn, row["to_place_id"], driver["lang"])))
    _ping_waitlist(request.app, conn, trip)


def _ping_waitlist(app, conn, trip) -> None:
    """A seat just freed on this trip — let anyone waiting grab it."""
    if trip is None:
        return
    when = fmt_when(datetime.fromisoformat(trip["depart_at"]))
    for w in waitlist.for_trip(conn, trip["id"]):
        r = get_user(conn, w["rider_id"])
        if r:
            c = copy(r["lang"])
            notify(app, r["telegram_id"], c.SEAT_FREED.format(
                dest=_place_name(conn, w["to_place_id"], r["lang"]), when=when),
                buttons=[[(c.BTN_BOOK_NOW, f"wlbook:{trip['id']}:{w['to_place_id']}")]])


@router.post("/bookings/{booking_id}/coming", status_code=204)
def im_coming(booking_id: int, request: Request, user=Depends(current_user),
              conn=Depends(get_conn)):
    """Rider tells the driver they're on the way to the pickup."""
    b = conn.execute(
        "SELECT * FROM bookings WHERE id = ? AND rider_id = ? AND status = 'booked'",
        (booking_id, user["telegram_id"])).fetchone()
    if b is None:
        raise HTTPException(status_code=404, detail="no such booking")
    trip = get_trip(conn, b["trip_id"])
    driver = get_user(conn, trip["driver_id"]) if trip else None
    if driver:
        notify(request.app, driver["telegram_id"],
               copy(driver["lang"]).RIDER_COMING.format(name=user["full_name"]))


class WaitlistBody(BaseModel):
    trip_id: int
    to_place_id: int


@router.post("/waitlist", status_code=204)
def join_waitlist(body: WaitlistBody, user=Depends(current_user), conn=Depends(get_conn)):
    if get_trip(conn, body.trip_id) is not None:
        waitlist.join(conn, body.trip_id, user["telegram_id"], body.to_place_id)


@router.get("/bookings/mine")
def my_bookings(user=Depends(current_user), conn=Depends(get_conn)):
    active = [_card(conn, b) for b in bookings_for_rider(conn, user["telegram_id"])]
    cancelled = [_card(conn, b, cancelled=True)
                 for b in cancelled_upcoming_for_rider(conn, user["telegram_id"])]
    return active + cancelled


@router.get("/bookings/history")
def my_history(user=Depends(current_user), conn=Depends(get_conn)):
    out = []
    for b in history_for_rider(conn, user["telegram_id"]):
        trip = get_trip(conn, b["trip_id"])
        d = get_user(conn, trip["driver_id"])
        dest = place_by_id(conn, b["to_place_id"])
        out.append({"booking_id": b["id"], "depart_at": trip["depart_at"], "bay": BAY,
                    "dest_place_id": b["to_place_id"],
                    "driver_name": d["full_name"] if d else "—",
                    "driver_tower": (d["tower"] or None) if d else None,
                    "car_model": d["car_model"] if d else None,
                    "car_color": d["car_color"] if d else None,
                    "plate": d["plate"] if d else None,
                    "dest_name_am": dest["name_am"], "dest_name_en": dest["name_en"],
                    "fare": b["fare"],
                    "status": b["status"], "paid": bool(b["paid"]),
                    "rating": rating_for_booking(conn, b["id"])})
    return out


class RateBody(BaseModel):
    value: int


@router.post("/bookings/{booking_id}/rate", status_code=204)
def rate_ride(booking_id: int, body: RateBody, user=Depends(current_user),
              conn=Depends(get_conn)):
    if body.value not in (1, -1):
        raise HTTPException(status_code=422, detail="value must be 1 or -1")
    b = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if b is None or b["rider_id"] != user["telegram_id"]:
        raise HTTPException(status_code=404, detail="no such booking")  # not yours
    if b["status"] != "completed":
        raise HTTPException(status_code=400, detail="only completed rides can be rated")
    trip = get_trip(conn, b["trip_id"])
    rate(conn, booking_id=booking_id, rater_id=user["telegram_id"],
         ratee_id=trip["driver_id"], value=body.value)


@router.post("/bookings/{booking_id}/driver-no-show", status_code=204)
def driver_no_show(booking_id: int, request: Request, user=Depends(current_user),
                   conn=Depends(get_conn)):
    """Rider taps 'driver didn't show'. Files a report (reason driver_no_show) that
    reaches admins — the mirror of the driver marking a rider a no-show."""
    if not allow(f"report:{user['telegram_id']}", 5, 300):
        raise HTTPException(status_code=429, detail="rate_limited")
    b = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if b is None or b["rider_id"] != user["telegram_id"]:
        raise HTTPException(status_code=404, detail="no such booking")  # not yours
    trip = get_trip(conn, b["trip_id"])
    if trip is None:
        raise HTTPException(status_code=404, detail="no such trip")
    if datetime.fromisoformat(trip["depart_at"]) > clock.now():
        raise HTTPException(status_code=400, detail="the trip hasn't departed yet")
    reported_id = trip["driver_id"]
    file_report(conn, reporter_id=user["telegram_id"], reported_id=reported_id,
                reason="driver_no_show", trip_id=b["trip_id"])
    reported = get_user(conn, reported_id)
    for admin_id in request.app.state.admin_ids:
        adm = get_user(conn, admin_id)
        c = copy(adm["lang"] if adm else "am")
        notify(request.app, admin_id, c.ADMIN_NEW_REPORT.format(
            reporter=user["full_name"],
            reported=reported["full_name"] if reported else "—",
            reason=c.REPORT_REASON_LABELS.get("driver_no_show", "driver no-show")))


class NewRequest(BaseModel):
    dest_place_id: int
    window_start: str
    window_end: str


@router.post("/requests", status_code=201)
def create_request(body: NewRequest, request: Request, user=Depends(current_user),
                   conn=Depends(get_conn)):
    rid = post_request(conn, rider_id=user["telegram_id"],
                       dest_place_id=body.dest_place_id,
                       window_start=datetime.fromisoformat(body.window_start),
                       window_end=datetime.fromisoformat(body.window_end))
    # Nudge drivers whose usual run goes there: one tap re-posts it.
    count = demand_count(conn, body.dest_place_id,
                         datetime.fromisoformat(body.window_start),
                         datetime.fromisoformat(body.window_end))
    for r in conn.execute(
            "SELECT dr.id, u.telegram_id, u.lang FROM driver_routes dr"
            " JOIN users u ON u.telegram_id = dr.driver_id"
            " WHERE dr.active = 1 AND dr.dest_place_id = ?", (body.dest_place_id,)):
        c = copy(r["lang"])
        notify(request.app, r["telegram_id"],
               c.DEMAND_NUDGE.format(count=count,
                                     dest=_place_name(conn, body.dest_place_id, r["lang"])),
               buttons=[[(c.BTN_POST_TODAY, f"postroute:{r['id']}")]])
    return {"request_id": rid}


class BlockBody(BaseModel):
    trip_id: int


@router.post("/blocks", status_code=204)
def block_driver(body: BlockBody, user=Depends(current_user),
                 conn=Depends(get_conn)):
    trip = get_trip(conn, body.trip_id)
    if trip is not None:
        block(conn, user["telegram_id"], trip["driver_id"])


class ReportBody(BaseModel):
    trip_id: int
    reason: str
    note: str | None = None


@router.post("/reports", status_code=201)
def report_driver(body: ReportBody, request: Request, user=Depends(current_user),
                  conn=Depends(get_conn)):
    if body.reason not in REASONS:
        raise HTTPException(status_code=422, detail="unknown reason")
    if not allow(f"report:{user['telegram_id']}", 5, 300):
        raise HTTPException(status_code=429, detail="rate_limited")
    trip = get_trip(conn, body.trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="no such trip")
    reported_id = trip["driver_id"]
    if reported_id == user["telegram_id"]:
        raise HTTPException(status_code=400, detail="you can't report yourself")
    note = (body.note or "").strip()[:500] or None
    rid = file_report(conn, reporter_id=user["telegram_id"], reported_id=reported_id,
                      reason=body.reason, trip_id=body.trip_id, note=note)
    # Reach every admin on the bot. The reported party is never told.
    reported = get_user(conn, reported_id)
    for admin_id in request.app.state.admin_ids:
        adm = get_user(conn, admin_id)
        lang = adm["lang"] if adm else "am"
        c = copy(lang)
        reason_label = c.REPORT_REASON_LABELS.get(body.reason, body.reason)
        notify(request.app, admin_id, c.ADMIN_NEW_REPORT.format(
            reporter=user["full_name"],
            reported=reported["full_name"] if reported else "—",
            reason=reason_label))
    return {"report_id": rid}


class WomenOnly(BaseModel):
    women_only: bool
    women_present: bool


@router.post("/me/women-only", status_code=204)
def women_only(body: WomenOnly, user=Depends(current_user),
               conn=Depends(get_conn)):
    set_women_only(conn, user["telegram_id"], women_only=body.women_only,
                   women_present=body.women_present)
