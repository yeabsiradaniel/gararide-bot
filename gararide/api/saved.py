"""Saved-trip endpoints (the repeat/commute convenience layer)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..places import place_by_id
from ..saved import deactivate_saved, save_trip, saved_for
from .deps import current_user, get_conn

router = APIRouter()


@router.get("/me/saved")
def my_saved(user=Depends(current_user), conn=Depends(get_conn)):
    return [{"id": s["id"], "dest_place_id": s["dest_place_id"],
             "dest_name_am": place_by_id(conn, s["dest_place_id"])["name_am"],
             "depart_time": s["depart_time"], "days_mask": s["days_mask"]}
            for s in saved_for(conn, user["telegram_id"])]


class NewSaved(BaseModel):
    dest_place_id: int
    depart_time: str
    days_mask: int


@router.post("/me/saved", status_code=201)
def add_saved(body: NewSaved, user=Depends(current_user), conn=Depends(get_conn)):
    sid = save_trip(conn, user_id=user["telegram_id"],
                    dest_place_id=body.dest_place_id, depart_time=body.depart_time,
                    days_mask=body.days_mask)
    return {"id": sid}


@router.post("/me/saved/{saved_id}/deactivate", status_code=204)
def remove_saved(saved_id: int, user=Depends(current_user), conn=Depends(get_conn)):
    deactivate_saved(conn, saved_id)
