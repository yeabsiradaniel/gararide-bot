import pytest

from gararide.db import connect, init_schema
from gararide.places import seed_corridor
from gararide.users import import_allowlist, register


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
