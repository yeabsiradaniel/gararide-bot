"""Admin ops endpoints, restricted to app.state.admin_ids.

Unmatched searches are a dated driver-recruitment list (spec §5). Quiet declines
(blocks) are counted elsewhere and never exposed here.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator

from ..places import place_by_id
from ..users import (NotOnRoster, add_to_allowlist, normalise_phone,
                     remove_driver, roster)
from .deps import current_user, get_conn

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
            "role": r["role"], "car_model": r["car_model"], "plate": r["plate"],
            "car_seats": r["car_seats"], "is_female": bool(r["is_female"]),
            "onboarded": bool(r["onboarded"])}


@router.get("/admin/drivers")
def list_drivers(user=Depends(require_admin), conn=Depends(get_conn)):
    return [_roster_row(r) for r in roster(conn)]


@router.post("/admin/drivers", status_code=201)
def add_driver(body: NewDriver, user=Depends(require_admin), conn=Depends(get_conn)):
    if len(normalise_phone(body.phone)) != 12:
        raise HTTPException(status_code=422, detail="phone must be a valid Ethiopian number")
    row = add_to_allowlist(
        conn, phone=body.phone, full_name=body.full_name, tower=body.tower,
        role="driver", car_model=body.car_model, plate=body.plate,
        car_seats=body.car_seats, is_female=body.is_female)
    return {"phone": row["phone"], "full_name": row["full_name"],
            "tower": row["tower"], "role": row["role"],
            "car_model": row["car_model"], "plate": row["plate"],
            "car_seats": row["car_seats"], "is_female": bool(row["is_female"]),
            "onboarded": bool(row["claimed_by"])}


@router.delete("/admin/drivers/{phone}")
def delete_driver(phone: str, user=Depends(require_admin), conn=Depends(get_conn)):
    if normalise_phone(phone) == normalise_phone(user["phone"]):
        raise HTTPException(status_code=400, detail="you can't remove yourself")
    try:
        result = remove_driver(conn, phone)
    except NotOnRoster:
        raise HTTPException(status_code=404, detail="not on the roster")
    return {"removed": normalise_phone(phone), **result}


@router.get("/admin/ops")
def ops(user=Depends(require_admin), conn=Depends(get_conn)):
    today = datetime.now().date().isoformat()
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


@router.get("/admin/unmatched")
def unmatched(user=Depends(require_admin), conn=Depends(get_conn)):
    since = (datetime.now() - timedelta(days=7)).isoformat(timespec="seconds")
    rows = conn.execute(
        "SELECT dest_place_id, COUNT(*) AS c FROM search_log"
        " WHERE results = 0 AND created_at >= ?"
        " GROUP BY dest_place_id ORDER BY c DESC",
        (since,),
    ).fetchall()
    return [{"dest_name": place_by_id(conn, r["dest_place_id"])["name_en"],
             "riders": r["c"]} for r in rows]
