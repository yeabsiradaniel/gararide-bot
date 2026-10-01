"""Display helpers.

Every time is shown on both clocks (UX spec section 23). Ethiopian time runs
six hours behind the Western clock, so 07:00 is 1:00 and 06:45 is 12:45.
A 12-hour misunderstanding strands someone in the dark; printing both is free.
"""
from __future__ import annotations

from datetime import datetime
from . import clock

MORNING = "ጠዋት"
AFTERNOON = "ከሰዓት"


def _ethiopian(dt: datetime) -> str:
    hour = (dt.hour - 6) % 12
    if hour == 0:
        hour = 12
    word = MORNING if 0 <= dt.hour < 12 else AFTERNOON
    return f"{hour}:{dt.minute:02d} {word}"


def fmt_time(dt: datetime) -> str:
    return f"{dt:%H:%M} ({_ethiopian(dt)})"


def fmt_day(dt: datetime) -> str:
    today = clock.now().date()
    delta = (dt.date() - today).days
    if delta == 0:
        return "ዛሬ"
    if delta == 1:
        return "ነገ"
    return dt.strftime("%b %d")


def fmt_when(dt: datetime) -> str:
    return f"{fmt_day(dt)} {fmt_time(dt)}"


def fmt_money(birr: int) -> str:
    return f"{birr} ብር"


def fmt_person(row) -> str:
    """Name and tower. Never the floor or unit (UX spec section 18).

    Drivers are desk-verified and carry a tower. Riders self-register from the
    Telegram link with no tower, so show the name alone when there is none.
    """
    if not row["tower"]:
        return f"{row['full_name']}"
    return f"{row['full_name']} · Tower {row['tower']}"
