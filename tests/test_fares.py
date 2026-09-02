import pytest

from gararide.fares import fare
from gararide.places import place_by_slug, seed_corridor


@pytest.fixture
def seeded(conn):
    seed_corridor(conn, "seed/corridor_ayat49.csv")
    return conn


def test_fare_from_origin_matches_the_ladder(seeded):
    origin = place_by_slug(seeded, "ayat49")["id"]
    expected = {"cmc": 25, "megenagna": 55, "aratkilo": 75, "kazanchis": 85}
    for slug, birr in expected.items():
        assert fare(seeded, origin, place_by_slug(seeded, slug)["id"]) == birr


def test_fare_is_symmetric_for_the_return_leg(seeded):
    a = place_by_slug(seeded, "ayat49")["id"]
    k = place_by_slug(seeded, "kazanchis")["id"]
    assert fare(seeded, k, a) == fare(seeded, a, k)


def test_fare_between_two_intermediate_stops(seeded):
    cmc = place_by_slug(seeded, "cmc")["id"]
    meg = place_by_slug(seeded, "megenagna")["id"]
    assert fare(seeded, cmc, meg) == 30  # 55 - 25


def test_fare_to_same_place_is_zero(seeded):
    cmc = place_by_slug(seeded, "cmc")["id"]
    assert fare(seeded, cmc, cmc) == 0
