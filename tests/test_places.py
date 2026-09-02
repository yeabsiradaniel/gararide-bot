from gararide.places import (all_places, origin_place, place_by_id,
                            place_by_slug, seed_corridor)


def test_seed_loads_all_stops_in_order(conn):
    seed_corridor(conn, "seed/corridor_ayat49.csv")
    stops = all_places(conn, 1)
    assert [p["slug"] for p in stops] == [
        "ayat49", "cmc", "megenagna", "aratkilo", "kazanchis"]


def test_seed_is_idempotent(conn):
    seed_corridor(conn, "seed/corridor_ayat49.csv")
    seed_corridor(conn, "seed/corridor_ayat49.csv")
    assert len(all_places(conn, 1)) == 5


def test_place_by_slug(conn):
    seed_corridor(conn, "seed/corridor_ayat49.csv")
    p = place_by_slug(conn, "megenagna")
    assert p["name_en"] == "Megenagna"
    assert p["sort_order"] == 2


def test_place_by_slug_missing_returns_none(conn):
    seed_corridor(conn, "seed/corridor_ayat49.csv")
    assert place_by_slug(conn, "piassa") is None


def test_place_by_id_round_trips(conn):
    seed_corridor(conn, "seed/corridor_ayat49.csv")
    p = place_by_slug(conn, "cmc")
    assert place_by_id(conn, p["id"])["slug"] == "cmc"


def test_origin_place_is_the_locked_origin(conn):
    seed_corridor(conn, "seed/corridor_ayat49.csv")
    assert origin_place(conn)["slug"] == "ayat49"
