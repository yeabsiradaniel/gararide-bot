from datetime import datetime, timedelta

import pytest

from gararide.places import origin_place, place_by_slug
from gararide.scheduler import due_confirmations, due_reminders
from gararide.trips import post_trip


@pytest.fixture
def booked(people):
    conn, driver, rider = people
    kaz = place_by_slug(conn, "kazanchis")["id"]

    def make(depart):
        # Insert the booking directly: these tests exercise the scheduler's
        # due-detection, not the booking cutoff (which is wall-clock sensitive).
        trip_id = post_trip(conn, driver_id=driver["telegram_id"],
                            dest_place_id=kaz, dropoff_place_ids=[kaz],
                            depart_at=depart, seats=3)
        cur = conn.execute(
            "INSERT INTO bookings (trip_id, rider_id, from_place_id, to_place_id,"
            " fare, created_at) VALUES (?,?,?,?,?,?)",
            (trip_id, rider["telegram_id"], origin_place(conn)["id"], kaz, 25,
             datetime.now().isoformat(timespec="seconds")))
        conn.commit()
        return cur.lastrowid

    return conn, make


def test_a_booking_thirty_minutes_out_is_due_for_a_reminder(booked):
    conn, make = booked
    now = datetime.now()
    bid = make(now + timedelta(minutes=25))
    assert bid in due_reminders(conn, now)


def test_a_booking_two_hours_out_is_not_yet_due(booked):
    conn, make = booked
    now = datetime.now()
    bid = make(now + timedelta(hours=2))
    assert bid not in due_reminders(conn, now)


def test_a_departed_trip_is_not_due(booked):
    conn, make = booked
    now = datetime.now()
    bid = make(now - timedelta(minutes=10))  # booked earlier, trip has since departed
    assert bid not in due_reminders(conn, now)


def test_tomorrow_mornings_bookings_are_due_for_the_evening_confirm(booked):
    conn, make = booked
    now = datetime.now().replace(hour=20, minute=0, second=0, microsecond=0)
    bid = make((now + timedelta(days=1)).replace(hour=7, minute=0))
    assert bid in due_confirmations(conn, now)


def test_a_booking_for_next_week_is_not_in_tonights_confirm(booked):
    conn, make = booked
    now = datetime.now().replace(hour=20, minute=0, second=0, microsecond=0)
    bid = make((now + timedelta(days=5)).replace(hour=7, minute=0))
    assert bid not in due_confirmations(conn, now)
