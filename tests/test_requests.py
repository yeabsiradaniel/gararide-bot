from datetime import datetime, timedelta

import pytest

from gararide.blocks import block
from gararide.places import place_by_slug
from gararide.requests import (cancel_request, demand_count, expire_stale,
                               fill_request, open_requests, post_request,
                               requests_matching_trip)
from gararide.trips import post_trip


def _at(hour, minute=0, days=1):
    return (datetime.now() + timedelta(days=days)).replace(
        hour=hour, minute=minute, second=0, microsecond=0)


def _add_rider(conn, telegram_id):
    """A real users row so requests.rider_id satisfies its foreign key."""
    conn.execute(
        "INSERT INTO users (telegram_id, phone, full_name, tower, role, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (telegram_id, f"25190000{telegram_id}", f"Rider {telegram_id}", "Z9",
         "rider", datetime.now().isoformat(timespec="seconds")))
    conn.commit()


@pytest.fixture
def ctx(people):
    conn, driver, rider = people
    ids = {s: place_by_slug(conn, s)["id"]
           for s in ("ayat49", "cmc", "megenagna", "kazanchis")}
    return conn, driver, rider, ids


def test_open_requests_lists_a_posted_request(ctx):
    conn, _, rider, ids = ctx
    post_request(conn, rider_id=rider["telegram_id"],
                 dest_place_id=ids["kazanchis"],
                 window_start=_at(6, 30), window_end=_at(7, 30))
    assert len(open_requests(conn)) == 1


def test_a_filled_request_is_no_longer_open(ctx):
    conn, _, rider, ids = ctx
    rid = post_request(conn, rider_id=rider["telegram_id"],
                       dest_place_id=ids["kazanchis"],
                       window_start=_at(6, 30), window_end=_at(7, 30))
    fill_request(conn, rid)
    assert open_requests(conn) == []


def test_a_cancelled_request_is_no_longer_open(ctx):
    conn, _, rider, ids = ctx
    rid = post_request(conn, rider_id=rider["telegram_id"],
                       dest_place_id=ids["kazanchis"],
                       window_start=_at(6, 30), window_end=_at(7, 30))
    cancel_request(conn, rid)
    assert open_requests(conn) == []


def test_a_driver_does_not_see_a_request_from_someone_they_blocked(ctx):
    conn, driver, rider, ids = ctx
    post_request(conn, rider_id=rider["telegram_id"],
                 dest_place_id=ids["kazanchis"],
                 window_start=_at(6, 30), window_end=_at(7, 30))
    block(conn, driver["telegram_id"], rider["telegram_id"])
    assert open_requests(conn, for_driver_id=driver["telegram_id"]) == []


def test_requests_matching_trip_finds_riders_the_driver_can_carry(ctx):
    conn, driver, rider, ids = ctx
    post_request(conn, rider_id=rider["telegram_id"],
                 dest_place_id=ids["megenagna"],
                 window_start=_at(6, 30), window_end=_at(7, 30))
    trip_id = post_trip(conn, driver_id=driver["telegram_id"],
                        dest_place_id=ids["kazanchis"],
                        dropoff_place_ids=[ids["megenagna"], ids["kazanchis"]],
                        depart_at=_at(7), seats=3)
    assert len(requests_matching_trip(conn, trip_id)) == 1


def test_requests_matching_trip_ignores_stops_the_driver_declined(ctx):
    conn, driver, rider, ids = ctx
    post_request(conn, rider_id=rider["telegram_id"],
                 dest_place_id=ids["megenagna"],
                 window_start=_at(6, 30), window_end=_at(7, 30))
    trip_id = post_trip(conn, driver_id=driver["telegram_id"],
                        dest_place_id=ids["kazanchis"],
                        dropoff_place_ids=[ids["kazanchis"]],
                        depart_at=_at(7), seats=3)
    assert requests_matching_trip(conn, trip_id) == []


def test_expire_stale_closes_requests_whose_window_has_passed(ctx):
    conn, _, rider, ids = ctx
    post_request(conn, rider_id=rider["telegram_id"],
                 dest_place_id=ids["kazanchis"],
                 window_start=_at(6, 30, days=-2), window_end=_at(7, 30, days=-2))
    assert expire_stale(conn) == 1
    assert open_requests(conn) == []


def test_demand_count_powers_the_three_neighbours_line(ctx):
    conn, _, rider, ids = ctx
    _add_rider(conn, 7001)
    _add_rider(conn, 7002)
    for tid in (rider["telegram_id"], 7001, 7002):
        post_request(conn, rider_id=tid, dest_place_id=ids["kazanchis"],
                     window_start=_at(6, 30), window_end=_at(7, 30))
    assert demand_count(conn, ids["kazanchis"], _at(6, 0), _at(8, 0)) == 3
