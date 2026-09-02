from datetime import datetime, timedelta

import pytest

from gararide.bookings import (NotOffered, TripFull, book, bookings_for_rider,
                               bookings_for_trip, cancel_booking, mark_no_show,
                               mark_paid)
from gararide.places import place_by_slug
from gararide.trips import post_trip, seats_left


def _at(hour, minute=0):
    return (datetime.now() + timedelta(days=1)).replace(
        hour=hour, minute=minute, second=0, microsecond=0)


def _add_rider(conn, telegram_id):
    """A real users row so bookings.rider_id satisfies its foreign key."""
    conn.execute(
        "INSERT INTO users (telegram_id, phone, full_name, tower, role, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (telegram_id, f"25190000{telegram_id}", f"Rider {telegram_id}", "Z9",
         "rider", datetime.now().isoformat(timespec="seconds")))
    conn.commit()


@pytest.fixture
def trip(people):
    conn, driver, rider = people
    ids = {s: place_by_slug(conn, s)["id"]
           for s in ("ayat49", "cmc", "megenagna", "kazanchis")}
    trip_id = post_trip(conn, driver_id=driver["telegram_id"],
                        dest_place_id=ids["kazanchis"],
                        dropoff_place_ids=[ids["megenagna"], ids["kazanchis"]],
                        depart_at=_at(7), seats=2)
    return conn, driver, rider, ids, trip_id


def test_booking_charges_the_segment_fare(trip):
    conn, _, rider, ids, trip_id = trip
    b = book(conn, trip_id=trip_id, rider_id=rider["telegram_id"],
             to_place_id=ids["megenagna"])
    assert b["fare"] == 55


def test_booking_consumes_a_seat(trip):
    conn, _, rider, ids, trip_id = trip
    book(conn, trip_id=trip_id, rider_id=rider["telegram_id"],
         to_place_id=ids["kazanchis"])
    assert seats_left(conn, trip_id) == 1


def test_booking_a_stop_the_driver_declined_is_rejected(trip):
    conn, _, rider, ids, trip_id = trip
    with pytest.raises(NotOffered):
        book(conn, trip_id=trip_id, rider_id=rider["telegram_id"],
             to_place_id=ids["cmc"])


def test_booking_a_full_trip_is_rejected(trip):
    conn, _, rider, ids, trip_id = trip
    _add_rider(conn, 7001)
    _add_rider(conn, 7002)
    book(conn, trip_id=trip_id, rider_id=rider["telegram_id"],
         to_place_id=ids["kazanchis"])
    book(conn, trip_id=trip_id, rider_id=7001, to_place_id=ids["kazanchis"])
    with pytest.raises(TripFull):
        book(conn, trip_id=trip_id, rider_id=7002, to_place_id=ids["kazanchis"])


def test_cancelling_returns_the_seat(trip):
    conn, _, rider, ids, trip_id = trip
    b = book(conn, trip_id=trip_id, rider_id=rider["telegram_id"],
             to_place_id=ids["kazanchis"])
    cancel_booking(conn, b["id"])
    assert seats_left(conn, trip_id) == 2


def test_bookings_for_trip_excludes_cancelled(trip):
    conn, _, rider, ids, trip_id = trip
    b = book(conn, trip_id=trip_id, rider_id=rider["telegram_id"],
             to_place_id=ids["kazanchis"])
    cancel_booking(conn, b["id"])
    assert bookings_for_trip(conn, trip_id) == []


def test_bookings_for_rider_lists_upcoming(trip):
    conn, _, rider, ids, trip_id = trip
    book(conn, trip_id=trip_id, rider_id=rider["telegram_id"],
         to_place_id=ids["kazanchis"])
    assert len(bookings_for_rider(conn, rider["telegram_id"])) == 1


def test_mark_paid_sets_the_flag(trip):
    conn, _, rider, ids, trip_id = trip
    b = book(conn, trip_id=trip_id, rider_id=rider["telegram_id"],
             to_place_id=ids["kazanchis"])
    mark_paid(conn, b["id"])
    row = conn.execute("SELECT paid FROM bookings WHERE id = ?", (b["id"],)).fetchone()
    assert row["paid"] == 1


def test_no_show_frees_the_seat_and_is_recorded(trip):
    conn, _, rider, ids, trip_id = trip
    b = book(conn, trip_id=trip_id, rider_id=rider["telegram_id"],
             to_place_id=ids["kazanchis"])
    mark_no_show(conn, b["id"])
    assert seats_left(conn, trip_id) == 2
    row = conn.execute("SELECT status FROM bookings WHERE id = ?",
                       (b["id"],)).fetchone()
    assert row["status"] == "no_show"
