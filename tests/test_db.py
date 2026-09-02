from gararide.db import connect, init_schema


def test_init_schema_creates_all_tables():
    conn = connect(":memory:")
    init_schema(conn)
    names = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert names >= {
        "places", "fares", "allowlist", "users", "trips",
        "trip_dropoffs", "bookings", "requests", "blocks",
        "saved_trips", "search_log",
    }


def test_init_schema_is_idempotent():
    conn = connect(":memory:")
    init_schema(conn)
    init_schema(conn)
    count = conn.execute(
        "SELECT COUNT(*) AS c FROM sqlite_master WHERE type='table'").fetchone()["c"]
    assert count >= 11


def test_rows_are_dict_like():
    conn = connect(":memory:")
    init_schema(conn)
    conn.execute(
        "INSERT INTO places (slug, name_am, name_en, corridor_id, sort_order)"
        " VALUES ('x', 'ኤክስ', 'X', 1, 0)")
    row = conn.execute("SELECT * FROM places").fetchone()
    assert row["slug"] == "x"
    assert row["name_en"] == "X"
