from datetime import datetime, timedelta

import pytest

from gararide.blocks import block
from gararide.matching import find_trips, near_misses
from gararide.places import place_by_slug
from gararide.trips import post_trip
from gararide.users import set_women_only


def _at(hour, minute=0, days=1):
    return (datetime.now() + timedelta(days=days)).replace(
        hour=hour, minute=minute, second=0, microsecond=0)


@pytest.fixture
def corridor(people):
    conn, driver, rider = people
    ids = {s: place_by_slug(conn, s)["id"]
           for s in ("ayat49", "cmc", "megenagna", "aratkilo", "kazanchis")}
    return conn, driver, rider, ids


def test_a_rider_matches_a_stop_the_driver_offered(corridor):
    conn, driver, rider, ids = corridor
    post_trip(conn, driver_id=driver["telegram_id"], dest_place_id=ids["kazanchis"],
              dropoff_place_ids=[ids["megenagna"], ids["kazanchis"]],
              depart_at=_at(7), seats=3)
    matches = find_trips(conn, rider_id=rider["telegram_id"],
                         dest_place_id=ids["megenagna"],
                         window_start=_at(6, 30), window_end=_at(7, 30))
    assert len(matches) == 1
    assert matches[0].fare == 55


def test_a_rider_does_not_match_a_stop_the_driver_declined(corridor):
    conn, driver, rider, ids = corridor
    post_trip(conn, driver_id=driver["telegram_id"], dest_place_id=ids["kazanchis"],
              dropoff_place_ids=[ids["kazanchis"]],
              depart_at=_at(7), seats=3)
    matches = find_trips(conn, rider_id=rider["telegram_id"],
                         dest_place_id=ids["megenagna"],
                         window_start=_at(6, 30), window_end=_at(7, 30))
    assert matches == []


def test_the_full_destination_always_matches(corridor):
    conn, driver, rider, ids = corridor
    post_trip(conn, driver_id=driver["telegram_id"], dest_place_id=ids["kazanchis"],
              dropoff_place_ids=[ids["kazanchis"]],
              depart_at=_at(7), seats=3)
    matches = find_trips(conn, rider_id=rider["telegram_id"],
                         dest_place_id=ids["kazanchis"],
                         window_start=_at(6, 30), window_end=_at(7, 30))
    assert len(matches) == 1
    assert matches[0].fare == 85


def test_a_trip_outside_the_window_does_not_match(corridor):
    conn, driver, rider, ids = corridor
    post_trip(conn, driver_id=driver["telegram_id"], dest_place_id=ids["kazanchis"],
              dropoff_place_ids=[ids["kazanchis"]], depart_at=_at(9), seats=3)
    assert find_trips(conn, rider_id=rider["telegram_id"],
                      dest_place_id=ids["kazanchis"],
                      window_start=_at(6, 30), window_end=_at(7, 30)) == []


def test_a_full_trip_does_not_match(corridor):
    conn, driver, rider, ids = corridor
    trip_id = post_trip(conn, driver_id=driver["telegram_id"],
                        dest_place_id=ids["kazanchis"],
                        dropoff_place_ids=[ids["kazanchis"]],
                        depart_at=_at(7), seats=1)
    # A filler passenger takes the only seat. 5555 must be a real user because
    # bookings.rider_id has a foreign key to users (PRAGMA foreign_keys = ON).
    conn.execute(
        "INSERT INTO users (telegram_id, phone, full_name, tower, role, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (5555, "251900000005", "Filler Rider", "Z9", "rider",
         datetime.now().isoformat(timespec="seconds")))
    conn.execute(
        "INSERT INTO bookings (trip_id, rider_id, from_place_id, to_place_id,"
        " fare, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (trip_id, 5555, ids["ayat49"], ids["kazanchis"], 85,
         datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    assert find_trips(conn, rider_id=rider["telegram_id"],
                      dest_place_id=ids["kazanchis"],
                      window_start=_at(6, 30), window_end=_at(7, 30)) == []


def test_a_cancelled_trip_does_not_match(corridor):
    conn, driver, rider, ids = corridor
    trip_id = post_trip(conn, driver_id=driver["telegram_id"],
                        dest_place_id=ids["kazanchis"],
                        dropoff_place_ids=[ids["kazanchis"]],
                        depart_at=_at(7), seats=3)
    conn.execute("UPDATE trips SET status = 'cancelled' WHERE id = ?", (trip_id,))
    conn.commit()
    assert find_trips(conn, rider_id=rider["telegram_id"],
                      dest_place_id=ids["kazanchis"],
                      window_start=_at(6, 30), window_end=_at(7, 30)) == []


def test_a_blocked_driver_never_appears(corridor):
    conn, driver, rider, ids = corridor
    post_trip(conn, driver_id=driver["telegram_id"], dest_place_id=ids["kazanchis"],
              dropoff_place_ids=[ids["kazanchis"]], depart_at=_at(7), seats=3)
    block(conn, rider["telegram_id"], driver["telegram_id"])
    assert find_trips(conn, rider_id=rider["telegram_id"],
                      dest_place_id=ids["kazanchis"],
                      window_start=_at(6, 30), window_end=_at(7, 30)) == []


def test_women_only_rider_does_not_match_a_male_driver(corridor):
    conn, driver, rider, ids = corridor
    post_trip(conn, driver_id=driver["telegram_id"], dest_place_id=ids["kazanchis"],
              dropoff_place_ids=[ids["kazanchis"]], depart_at=_at(7), seats=3)
    set_women_only(conn, rider["telegram_id"], women_only=True, women_present=False)
    assert find_trips(conn, rider_id=rider["telegram_id"],
                      dest_place_id=ids["kazanchis"],
                      window_start=_at(6, 30), window_end=_at(7, 30)) == []


def test_near_miss_reports_a_later_trip(corridor):
    conn, driver, rider, ids = corridor
    post_trip(conn, driver_id=driver["telegram_id"], dest_place_id=ids["kazanchis"],
              dropoff_place_ids=[ids["kazanchis"]], depart_at=_at(8), seats=3)
    misses = near_misses(conn, rider_id=rider["telegram_id"],
                         dest_place_id=ids["kazanchis"],
                         window_start=_at(6, 30), window_end=_at(7, 30))
    assert [m.reason for m in misses] == ["later"]


def test_near_miss_reports_a_trip_that_gets_you_partway(corridor):
    conn, driver, rider, ids = corridor
    post_trip(conn, driver_id=driver["telegram_id"], dest_place_id=ids["megenagna"],
              dropoff_place_ids=[ids["cmc"], ids["megenagna"]],
              depart_at=_at(7), seats=3)
    misses = near_misses(conn, rider_id=rider["telegram_id"],
                         dest_place_id=ids["kazanchis"],
                         window_start=_at(6, 30), window_end=_at(7, 30))
    assert [m.reason for m in misses] == ["partway"]
    assert misses[0].fare == 55


def test_a_driver_searching_never_sees_their_own_trip(corridor):
    conn, driver, rider, ids = corridor
    post_trip(conn, driver_id=driver["telegram_id"], dest_place_id=ids["kazanchis"],
              dropoff_place_ids=[ids["kazanchis"]], depart_at=_at(7), seats=3)
    # The driver themselves searches as a rider — their own trip must not appear.
    assert find_trips(conn, rider_id=driver["telegram_id"],
                      dest_place_id=ids["kazanchis"],
                      window_start=_at(6, 30), window_end=_at(7, 30)) == []
    assert near_misses(conn, rider_id=driver["telegram_id"],
                       dest_place_id=ids["kazanchis"],
                       window_start=_at(6, 30), window_end=_at(7, 30)) == []


def test_an_exact_match_is_not_reported_as_a_near_miss(corridor):
    conn, driver, rider, ids = corridor
    post_trip(conn, driver_id=driver["telegram_id"], dest_place_id=ids["kazanchis"],
              dropoff_place_ids=[ids["kazanchis"]], depart_at=_at(7), seats=3)
    assert near_misses(conn, rider_id=rider["telegram_id"],
                       dest_place_id=ids["kazanchis"],
                       window_start=_at(6, 30), window_end=_at(7, 30)) == []
