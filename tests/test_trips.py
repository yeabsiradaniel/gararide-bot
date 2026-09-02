from datetime import datetime, timedelta

import pytest

from gararide.places import place_by_slug
from gararide.trips import (InvalidDropoff, cancel_trip, default_dropoffs,
                            dropoffs, get_trip, intermediate_dropoffs,
                            post_trip, seats_left, trips_by_driver)


def _tomorrow_at(hour, minute=0):
    return (datetime.now() + timedelta(days=1)).replace(
        hour=hour, minute=minute, second=0, microsecond=0)


def test_default_dropoffs_are_every_stop_up_to_the_destination(people):
    conn, _, _ = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    slugs = [place_by_slug(conn, s)["slug"] for s in
             ("cmc", "megenagna", "aratkilo", "kazanchis")]
    got = [conn.execute("SELECT slug FROM places WHERE id = ?", (i,)).fetchone()["slug"]
           for i in default_dropoffs(conn, kaz)]
    assert got == slugs


def test_default_dropoffs_for_a_near_destination(people):
    conn, _, _ = people
    cmc = place_by_slug(conn, "cmc")["id"]
    assert len(default_dropoffs(conn, cmc)) == 1


def test_intermediate_dropoffs_exclude_the_destination(people):
    conn, _, _ = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    got = [conn.execute("SELECT slug FROM places WHERE id=?", (i,)).fetchone()["slug"]
           for i in intermediate_dropoffs(conn, kaz)]
    assert got == ["cmc", "megenagna", "aratkilo"]   # kazanchis excluded


def test_intermediate_dropoffs_empty_for_the_nearest_stop(people):
    conn, _, _ = people
    cmc = place_by_slug(conn, "cmc")["id"]
    assert intermediate_dropoffs(conn, cmc) == []


def test_post_trip_stores_the_declared_dropoffs(people):
    conn, driver, _ = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    meg = place_by_slug(conn, "megenagna")["id"]
    trip_id = post_trip(conn, driver_id=driver["telegram_id"],
                        dest_place_id=kaz, dropoff_place_ids=[meg, kaz],
                        depart_at=_tomorrow_at(7), seats=3)
    assert [d["slug"] for d in dropoffs(conn, trip_id)] == ["megenagna", "kazanchis"]


def test_a_driver_may_offer_only_the_final_destination(people):
    conn, driver, _ = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    trip_id = post_trip(conn, driver_id=driver["telegram_id"],
                        dest_place_id=kaz, dropoff_place_ids=[kaz],
                        depart_at=_tomorrow_at(7), seats=3)
    assert [d["slug"] for d in dropoffs(conn, trip_id)] == ["kazanchis"]


def test_the_destination_is_always_a_dropoff(people):
    conn, driver, _ = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    meg = place_by_slug(conn, "megenagna")["id"]
    trip_id = post_trip(conn, driver_id=driver["telegram_id"],
                        dest_place_id=kaz, dropoff_place_ids=[meg],
                        depart_at=_tomorrow_at(7), seats=3)
    assert "kazanchis" in [d["slug"] for d in dropoffs(conn, trip_id)]


def test_a_dropoff_beyond_the_destination_is_rejected(people):
    conn, driver, _ = people
    meg = place_by_slug(conn, "megenagna")["id"]
    kaz = place_by_slug(conn, "kazanchis")["id"]
    with pytest.raises(InvalidDropoff):
        post_trip(conn, driver_id=driver["telegram_id"],
                  dest_place_id=meg, dropoff_place_ids=[kaz],
                  depart_at=_tomorrow_at(7), seats=3)


def test_seats_left_starts_at_the_posted_total(people):
    conn, driver, _ = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    trip_id = post_trip(conn, driver_id=driver["telegram_id"],
                        dest_place_id=kaz, dropoff_place_ids=[kaz],
                        depart_at=_tomorrow_at(7), seats=3)
    assert seats_left(conn, trip_id) == 3


def test_trips_by_driver_excludes_cancelled_trips(people):
    conn, driver, _ = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    trip_id = post_trip(conn, driver_id=driver["telegram_id"],
                        dest_place_id=kaz, dropoff_place_ids=[kaz],
                        depart_at=_tomorrow_at(7), seats=3)
    cancel_trip(conn, trip_id)
    assert trips_by_driver(conn, driver["telegram_id"]) == []
    assert get_trip(conn, trip_id)["status"] == "cancelled"


def test_the_origin_is_the_locked_pilot_origin(people):
    conn, driver, _ = people
    kaz = place_by_slug(conn, "kazanchis")["id"]
    trip_id = post_trip(conn, driver_id=driver["telegram_id"],
                        dest_place_id=kaz, dropoff_place_ids=[kaz],
                        depart_at=_tomorrow_at(7), seats=3)
    origin_id = get_trip(conn, trip_id)["origin_place_id"]
    assert conn.execute("SELECT slug FROM places WHERE id = ?",
                        (origin_id,)).fetchone()["slug"] == "ayat49"
