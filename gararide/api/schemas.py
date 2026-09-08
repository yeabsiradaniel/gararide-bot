"""Response shapes. Drivers expose tower; riders never do (spec §3)."""
from __future__ import annotations

from pydantic import BaseModel


class Me(BaseModel):
    telegram_id: int
    full_name: str
    role: str
    tower: str | None
    car_model: str | None
    plate: str | None
    car_seats: int | None
    women_only: bool
    women_present: bool
    is_admin: bool
    lang: str


class Place(BaseModel):
    id: int
    slug: str
    name_am: str
    name_en: str
    sort_order: int
