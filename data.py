"""Corridor data, demo seed content, pricing, and the shared store.

Persistence: the store mirrors itself to a small JSON file on every mutation
so restarts don't wipe posted rides and bookings. Delete the file to reset.
"""
from __future__ import annotations

import json
import random
import string as _string
from datetime import datetime, timedelta
from pathlib import Path

# Fixed stops on the Megenagna-Bole corridor. Order matters: a ride goes
# from a lower index to a higher one (m2b) or the reverse (b2m).
STOPS = [
    {"id": "megenagna",   "name": "መገናኛ"},
    {"id": "hayahulet",   "name": "ሀያሁለት (22 ማዞሪያ)"},
    {"id": "edna",        "name": "ኤድና ሞል"},
    {"id": "medhanialem", "name": "ቦሌ ሜድሃኒአለም"},
    {"id": "dildiy",      "name": "ቦሌ ድልድይ"},
    {"id": "airport",     "name": "ቦሌ አየር ማረፊያ"},
]

DIRECTIONS = {
    "m2b": "መገናኛ → ቦሌ",
    "b2m": "ቦሌ → መገናኛ",
}

STORE_FILE = Path(__file__).parent / "gararide_data.json"


def direction_of(from_idx: int, to_idx: int) -> str:
    return "m2b" if to_idx > from_idx else "b2m"


def fare_per_seat(from_idx: int, to_idx: int) -> int:
    """Segment-based pricing: base + per-segment, in Birr."""
    segments = abs(to_idx - from_idx)
    return max(40, 25 + 25 * segments)


def solo_estimate(from_idx: int, to_idx: int) -> int:
    """What the same trip would cost alone on a ride-hailing app."""
    segments = abs(to_idx - from_idx)
    return 60 + 60 * segments


def new_code(prefix: str) -> str:
    return prefix + "-" + "".join(random.choices(_string.ascii_uppercase + _string.digits, k=4))


def covers(ride: dict, from_idx: int, to_idx: int) -> bool:
    """True if the ride passes through the rider's whole segment, same direction."""
    if direction_of(from_idx, to_idx) != ride["direction"]:
        return False
    lo, hi = sorted((from_idx, to_idx))
    rlo, rhi = sorted((ride["from"], ride["to"]))
    return rlo <= lo and rhi >= hi


class Store:
    """Rides + bookings with JSON-file persistence. Good enough for a demo."""

    def __init__(self, path: Path | None = STORE_FILE) -> None:
        self.path = path
        self.rides: dict[str, dict] = {}
        self.bookings: dict[str, dict] = {}
        if self.path and self.path.exists():
            self._load()

    # ---------------------------------------------------------- persistence

    def _save(self) -> None:
        if not self.path:
            return
        payload = {
            "rides": [{**r, "depart_at": r["depart_at"].isoformat()} for r in self.rides.values()],
            "bookings": [{**b, "booked_at": b["booked_at"].isoformat()} for b in self.bookings.values()],
        }
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    def _load(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        cutoff = datetime.now() - timedelta(days=1)
        for r in payload.get("rides", []):
            r["depart_at"] = datetime.fromisoformat(r["depart_at"])
            if r["depart_at"] > cutoff:
                self.rides[r["id"]] = r
        for b in payload.get("bookings", []):
            if b["ride_id"] in self.rides:
                b["booked_at"] = datetime.fromisoformat(b["booked_at"])
                self.bookings[b["code"]] = b

    # --------------------------------------------------------------- rides

    def add_ride(self, from_idx: int, to_idx: int, depart_at: datetime,
                 seats: int, driver: dict, driver_id: int | None = None) -> dict:
        ride = {
            "id": new_code("R"),
            "from": from_idx,
            "to": to_idx,
            "direction": direction_of(from_idx, to_idx),
            "depart_at": depart_at,
            "seats_total": seats,
            "seats_taken": 0,
            "driver": driver,
            "driver_id": driver_id,
        }
        self.rides[ride["id"]] = ride
        self._save()
        return ride

    def open_rides(self, direction: str | None = None, include_full: bool = False) -> list[dict]:
        cutoff = datetime.now() - timedelta(minutes=10)
        rides = [
            r for r in self.rides.values()
            if r["depart_at"] > cutoff
            and (include_full or r["seats_taken"] < r["seats_total"])
            and (direction is None or r["direction"] == direction)
        ]
        return sorted(rides, key=lambda r: r["depart_at"])

    def matching_rides(self, from_idx: int, to_idx: int) -> list[dict]:
        """Open rides that cover the rider's whole segment."""
        return [r for r in self.open_rides(direction_of(from_idx, to_idx))
                if covers(r, from_idx, to_idx)]

    def rides_by_driver(self, driver_id: int) -> list[dict]:
        return sorted((r for r in self.rides.values() if r.get("driver_id") == driver_id),
                      key=lambda r: r["depart_at"])

    def cancel_ride(self, ride_id: str) -> tuple[dict | None, list[dict]]:
        """Remove a ride and all its bookings. Returns (ride, bookings)."""
        ride = self.rides.pop(ride_id, None)
        if ride is None:
            return None, []
        dropped = [b for b in list(self.bookings.values()) if b["ride_id"] == ride_id]
        for b in dropped:
            del self.bookings[b["code"]]
        self._save()
        return ride, dropped

    # ------------------------------------------------------------ bookings

    def book(self, ride_id: str, rider_name: str, rider_id: int | None = None,
             from_idx: int | None = None, to_idx: int | None = None) -> dict:
        ride = self.rides.get(ride_id)
        if ride is None:
            raise ValueError("not_found")
        if ride["seats_taken"] >= ride["seats_total"]:
            raise ValueError("full")
        ride["seats_taken"] += 1
        frm = ride["from"] if from_idx is None else from_idx
        to = ride["to"] if to_idx is None else to_idx
        booking = {
            "code": new_code("GR"),
            "ride_id": ride_id,
            "rider": rider_name,
            "rider_id": rider_id,
            "from": frm,
            "to": to,
            "fare": fare_per_seat(frm, to),
            "booked_at": datetime.now(),
        }
        self.bookings[booking["code"]] = booking
        self._save()
        return booking

    def cancel_booking(self, code: str) -> dict | None:
        booking = self.bookings.pop(code, None)
        if booking is None:
            return None
        ride = self.rides.get(booking["ride_id"])
        if ride and ride["seats_taken"] > 0:
            ride["seats_taken"] -= 1
        self._save()
        return booking

    def bookings_by_rider(self, rider_id: int) -> list[dict]:
        return sorted((b for b in self.bookings.values() if b.get("rider_id") == rider_id),
                      key=lambda b: b["booked_at"])

    def bookings_for_ride(self, ride_id: str) -> list[dict]:
        return [b for b in self.bookings.values() if b["ride_id"] == ride_id]

    # --------------------------------------------------------------- stats

    def stats(self) -> dict:
        seats = sum(r["seats_taken"] for r in self.rides.values())
        savings = sum(solo_estimate(b["from"], b["to"]) - b["fare"]
                      for b in self.bookings.values())
        return {
            "rides_posted": len(self.rides),
            "rides_active": len(self.open_rides(include_full=True)),
            "bookings": len(self.bookings),
            "seats_filled": seats,
            "rider_savings": savings,
        }

    # ---------------------------------------------------------------- seed

    def seed(self) -> None:
        """Fake drivers so the demo always looks alive."""
        now = datetime.now()
        drivers = [
            # name, car, plate, rating, phone, from, to, +minutes, seats, taken
            ("አበበ ከበደ",   "Toyota Corolla",  "3-AA 21457", 4.8, "0911 22 33 44", 0, 5, 35, 3, 0),
            ("ሠላም ተስፋዬ",  "Suzuki Dzire",    "3-AA 88712", 4.9, "0912 34 45 56", 1, 3, 65, 2, 0),
            ("ዳዊት ሞላ",    "Hyundai Accent",  "3-AA 55203", 4.7, "0913 45 56 67", 5, 0, 95, 3, 0),
            ("ሄኖክ ገብሬ",   "Toyota Vitz",     "3-AA 30918", 4.6, "0914 56 67 78", 4, 1, 140, 2, 1),
            ("ብርሃኑ አለሙ",  "Toyota Corolla",  "3-AA 76240", 4.5, "0915 67 78 89", 0, 3, 180, 2, 2),
            ("ምህረት ወላደ",   "Suzuki Swift",    "3-AA 64182", 4.9, "0916 78 89 90", 2, 5, 220, 3, 1),
        ]
        for name, car, plate, rating, phone, frm, to, mins, seats, taken in drivers:
            ride = self.add_ride(
                frm, to, now + timedelta(minutes=mins), seats,
                {"name": name, "car": car, "plate": plate, "rating": rating, "phone": phone},
            )
            ride["seats_taken"] = taken
        self._save()


def ride_json(ride: dict) -> dict:
    frm, to = ride["from"], ride["to"]
    return {
        "id": ride["id"],
        "direction": ride["direction"],
        "from_idx": frm,
        "to_idx": to,
        "from_name": STOPS[frm]["name"],
        "to_name": STOPS[to]["name"],
        "depart_at": ride["depart_at"].isoformat(),
        "seats_total": ride["seats_total"],
        "seats_left": ride["seats_total"] - ride["seats_taken"],
        "fare": fare_per_seat(frm, to),
        "solo": solo_estimate(frm, to),
        "driver": ride["driver"],
    }


def booking_json(booking: dict) -> dict:
    return {
        "code": booking["code"],
        "ride_id": booking["ride_id"],
        "rider": booking["rider"],
        "rider_id": booking.get("rider_id"),
        "from_idx": booking["from"],
        "to_idx": booking["to"],
        "fare": booking["fare"],
    }
