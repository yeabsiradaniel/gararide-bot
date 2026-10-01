"""Single source of 'now' for the pilot — always Addis Ababa (EAT, UTC+3).

Trip times are entered in Addis local time from the phone, but the server may run
in UTC (Render). Comparing the two directly skews every cutoff, window, reminder
and scheduled job by three hours. Routing all 'now' calls through here keeps the
server's own timezone irrelevant. Returns naive local time to match how times are
stored everywhere else.
"""
from __future__ import annotations

from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    ADDIS = ZoneInfo("Africa/Addis_Ababa")
except Exception:  # pragma: no cover - falls back to system local if tzdata missing
    ADDIS = None


def now() -> datetime:
    return datetime.now(ADDIS).replace(tzinfo=None) if ADDIS else datetime.now()
