import pytest

from gararide.db import connect, init_schema
from gararide.places import seed_corridor
from gararide.users import import_allowlist, register


@pytest.fixture(autouse=True)
def _reset_ratelimit():
    # The limiter is process-global; clear it so tests don't bleed into each other.
    from gararide import ratelimit
    ratelimit._hits.clear()
    yield


@pytest.fixture
def conn():
    c = connect(":memory:")
    init_schema(c)
    yield c
    c.close()


@pytest.fixture
def seeded(conn):
    seed_corridor(conn, "seed/corridor_ayat49.csv")
    return conn


@pytest.fixture
def people(seeded):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    driver = register(seeded, telegram_id=1001, phone="0911223344")
    rider = register(seeded, telegram_id=1002, phone="0912334455")
    return seeded, driver, rider
