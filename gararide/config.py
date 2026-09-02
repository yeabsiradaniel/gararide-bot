"""Pilot restrictions live here and nowhere else.

Phase 2 flips these switches. If a pilot limitation appears anywhere
outside this file or the seed data, it is a bug (UX spec section 4).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PilotConfig:
    # Which corridor's stops are available.
    corridor_id: int = 1

    # Phase 1: every trip starts at (or returns to) Ayat 49.
    lock_origin: bool = True
    origin_slug: str = "ayat49"

    # Phase 1: destinations come from the seeded stop list only.
    open_destinations: bool = False

    # Phase 1: a driver must already be making the trip. Beacon mode is Phase 2.
    allow_beacon: bool = False

    # Morning commute slots. "Another time" is always available for other trips.
    departure_slots: tuple[str, ...] = ("06:45", "07:00", "07:15")

    # Operational rules from the execution plan.
    dwell_minutes: int = 4
    booking_cutoff_hour: int = 20
    reminder_minutes_before: int = 30

    # Near-miss search widens the requested window by this much on each side.
    near_miss_window_minutes: int = 90

    # A saved trip is offered after this many identical trips.
    save_prompt_threshold: int = 4


CONFIG = PilotConfig()


import os

ADMIN_IDS: frozenset[int] = frozenset(
    int(x) for x in os.environ.get("GARARIDE_ADMINS", "").split(",") if x.strip()
)
