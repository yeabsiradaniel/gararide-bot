"""Admin ops endpoints, restricted to app.state.admin_ids.

Unmatched searches are a dated driver-recruitment list (spec §5). Quiet declines
(blocks) are counted elsewhere and never exposed here.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from .. import clock

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator

from ..copy import strings as copy
from ..fmt import fmt_when
from ..places import place_by_id
from ..ratings import tally_for_driver
from ..reports import open_reports, resolve_report
from ..users import (NotOnRoster, add_to_allowlist, get_user, lookup_allowlist,
                     normalise_phone, remove_driver, roster, update_driver)
from .deps import current_user, get_conn
from .push import notify

router = APIRouter()


def require_admin(request: Request, user=Depends(current_user)):
    if user["telegram_id"] not in request.app.state.admin_ids:
        raise HTTPException(status_code=403, detail="admins only")
    return user


class NewDriver(BaseModel):
    phone: str
    full_name: str
    tower: str
    car_model: str | None = None
    car_color: str | None = None
    plate: str | None = None
    car_seats: int
    is_female: bool = False

    @field_validator("full_name", "tower")
    @classmethod
    def _required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("required")
        return v.strip()

    @field_validator("car_seats")
    @classmethod
    def _seats_range(cls, v: int) -> int:
        if not 1 <= v <= 14:
            raise ValueError("car_seats must be 1..14")
        return v


def _roster_row(r) -> dict:
    return {"phone": r["phone"], "full_name": r["full_name"], "tower": r["tower"],
            "role": r["role"], "car_model": r["car_model"], "car_color": r["car_color"],
            "plate": r["plate"], "car_seats": r["car_seats"],
            "is_female": bool(r["is_female"]), "onboarded": bool(r["onboarded"])}


@router.get("/admin/drivers")
def list_drivers(user=Depends(require_admin), conn=Depends(get_conn)):
    out = []
    for r in roster(conn):
        row = _roster_row(r)
        # Admin-only rating tally; empty until the driver has onboarded + been rated.
        row["ratings"] = (tally_for_driver(conn, r["claimed_by"])
                          if r["claimed_by"] is not None else {"up": 0, "down": 0})
        out.append(row)
    return out


@router.post("/admin/drivers", status_code=201)
def add_driver(body: NewDriver, user=Depends(require_admin), conn=Depends(get_conn)):
    if len(normalise_phone(body.phone)) != 12:
        raise HTTPException(status_code=422, detail="phone must be a valid Ethiopian number")
    row = add_to_allowlist(
        conn, phone=body.phone, full_name=body.full_name, tower=body.tower,
        role="driver", car_model=body.car_model, car_color=body.car_color,
        plate=body.plate, car_seats=body.car_seats, is_female=body.is_female)
    return {"phone": row["phone"], "full_name": row["full_name"],
            "tower": row["tower"], "role": row["role"],
            "car_model": row["car_model"], "car_color": row["car_color"],
            "plate": row["plate"], "car_seats": row["car_seats"],
            "is_female": bool(row["is_female"]), "onboarded": bool(row["claimed_by"])}


@router.patch("/admin/drivers/{phone}")
def edit_driver(phone: str, body: NewDriver, user=Depends(require_admin),
                conn=Depends(get_conn)):
    try:
        row = update_driver(
            conn, phone, full_name=body.full_name, tower=body.tower,
            car_model=body.car_model, car_color=body.car_color, plate=body.plate,
            car_seats=body.car_seats, is_female=body.is_female)
    except NotOnRoster:
        raise HTTPException(status_code=404, detail="not on the roster")
    return {"phone": row["phone"], "full_name": row["full_name"],
            "tower": row["tower"], "role": row["role"],
            "car_model": row["car_model"], "car_color": row["car_color"],
            "plate": row["plate"], "car_seats": row["car_seats"],
            "is_female": bool(row["is_female"]), "onboarded": bool(row["claimed_by"])}


@router.delete("/admin/drivers/{phone}")
def delete_driver(phone: str, request: Request, user=Depends(require_admin),
                  conn=Depends(get_conn)):
    if normalise_phone(phone) == normalise_phone(user["phone"]):
        raise HTTPException(status_code=400, detail="you can't remove yourself")
    # Capture riders who lose a booking BEFORE remove_driver cancels the trips.
    entry = lookup_allowlist(conn, phone)
    driver_tid = entry["claimed_by"] if entry else None
    affected = []
    if driver_tid is not None:
        affected = conn.execute(
            "SELECT b.rider_id, b.to_place_id, t.depart_at FROM bookings b"
            " JOIN trips t ON t.id = b.trip_id"
            " WHERE t.driver_id = ? AND t.status = 'open' AND b.status = 'booked'",
            (driver_tid,)).fetchall()
    try:
        result = remove_driver(conn, phone)
    except NotOnRoster:
        raise HTTPException(status_code=404, detail="not on the roster")
    for r in affected:
        rider = get_user(conn, r["rider_id"])
        if rider:
            p = place_by_id(conn, r["to_place_id"])
            dest = p["name_en"] if rider["lang"] == "en" else p["name_am"]
            notify(request.app, r["rider_id"], copy(rider["lang"]).TRIP_CANCELLED.format(
                dest=dest, when=fmt_when(datetime.fromisoformat(r["depart_at"]))))
    return {"removed": normalise_phone(phone), **result}


@router.get("/admin/ops")
def ops(user=Depends(require_admin), conn=Depends(get_conn)):
    today = clock.now().date().isoformat()
    s = conn.execute(
        "SELECT"
        " (SELECT COUNT(*) FROM trips WHERE status='open' AND depart_at LIKE ?) AS trips,"
        " (SELECT COUNT(*) FROM bookings b JOIN trips t ON t.id=b.trip_id"
        "   WHERE b.status='booked' AND t.depart_at LIKE ?) AS seats,"
        " (SELECT COUNT(*) FROM bookings b JOIN trips t ON t.id=b.trip_id"
        "   WHERE b.status='no_show' AND t.depart_at LIKE ?) AS no_shows,"
        " (SELECT COUNT(*) FROM requests WHERE status='open') AS open_requests,"
        " (SELECT COUNT(*) FROM users WHERE active=1) AS users",
        (f"{today}%", f"{today}%", f"{today}%"),
    ).fetchone()
    return {"trips": s["trips"], "seats": s["seats"], "no_shows": s["no_shows"],
            "open_requests": s["open_requests"], "users": s["users"]}


@router.get("/admin/reports")
def list_reports(user=Depends(require_admin), conn=Depends(get_conn)):
    return [{"id": r["id"], "reason": r["reason"], "note": r["note"],
             "trip_id": r["trip_id"], "created_at": r["created_at"],
             "reporter_name": r["reporter_name"],
             "reported_name": r["reported_name"],
             "reported_phone": r["reported_phone"],
             "reported_tower": r["reported_tower"]}
            for r in open_reports(conn)]


@router.post("/admin/reports/{report_id}/resolve", status_code=204)
def resolve(report_id: int, user=Depends(require_admin), conn=Depends(get_conn)):
    if not resolve_report(conn, report_id):
        raise HTTPException(status_code=404, detail="no such open report")


class Broadcast(BaseModel):
    audience: str  # 'all' | 'drivers' | 'riders'
    message: str


@router.post("/admin/broadcast")
def broadcast(body: Broadcast, request: Request, user=Depends(require_admin),
              conn=Depends(get_conn)):
    text = (body.message or "").strip()[:1000]
    if not text:
        return {"sent": 0}
    where = {"drivers": "role='driver'", "riders": "role='rider'"}.get(body.audience, "1=1")
    rows = conn.execute(
        f"SELECT telegram_id FROM users WHERE active=1 AND {where}").fetchall()
    for r in rows:
        notify(request.app, r["telegram_id"], f"📢 {text}")
    return {"sent": len(rows)}


@router.get("/admin/unmatched")
def unmatched(user=Depends(require_admin), conn=Depends(get_conn)):
    since = (clock.now() - timedelta(days=7)).isoformat(timespec="seconds")
    rows = conn.execute(
        "SELECT dest_place_id, COUNT(*) AS c FROM search_log"
        " WHERE results = 0 AND created_at >= ?"
        " GROUP BY dest_place_id ORDER BY c DESC",
        (since,),
    ).fetchall()
    return [{"dest_name": place_by_id(conn, r["dest_place_id"])["name_en"],
             "riders": r["c"]} for r in rows]
