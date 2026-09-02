from datetime import datetime, timedelta

from gararide.bookings import book
from gararide.places import place_by_slug
from gararide.saved import (deactivate_saved, save_trip, saved_for,
                            should_offer_save)
from gararide.trips import post_trip


def _book_kaz(conn, driver_id, rider_id, kaz, days):
    depart = (datetime.now() + timedelta(days=days)).replace(
        hour=7, minute=0, second=0, microsecond=0)
    tid = post_trip(conn, driver_id=driver_id, dest_place_id=kaz,
                    dropoff_place_ids=[kaz], depart_at=depart, seats=3)
    book(conn, trip_id=tid, rider_id=rider_id, to_place_id=kaz)


def test_offer_save_after_threshold_identical_trips(people):
    conn, driver, rider = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    for d in range(1, 4):
        _book_kaz(conn, driver["telegram_id"], rider["telegram_id"], kaz, d)
    assert should_offer_save(conn, rider["telegram_id"], kaz, "07:00") is False
    _book_kaz(conn, driver["telegram_id"], rider["telegram_id"], kaz, 4)
    assert should_offer_save(conn, rider["telegram_id"], kaz, "07:00") is True


def test_save_and_list_and_deactivate(people):
    conn, _, rider = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    sid = save_trip(conn, user_id=rider["telegram_id"], dest_place_id=kaz,
                    depart_time="07:00", days_mask=0b0011111)
    rows = saved_for(conn, rider["telegram_id"])
    assert len(rows) == 1 and rows[0]["depart_time"] == "07:00"
    deactivate_saved(conn, sid)
    assert saved_for(conn, rider["telegram_id"]) == []


def test_already_saved_is_not_offered_again(people):
    conn, driver, rider = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    for d in range(1, 5):
        _book_kaz(conn, driver["telegram_id"], rider["telegram_id"], kaz, d)
    save_trip(conn, user_id=rider["telegram_id"], dest_place_id=kaz,
              depart_time="07:00", days_mask=0b0011111)
    assert should_offer_save(conn, rider["telegram_id"], kaz, "07:00") is False
