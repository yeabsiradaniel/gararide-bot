import pytest

from gararide.users import (NotAllowlisted, get_user, import_allowlist,
                            lookup_allowlist, normalise_phone, register,
                            register_rider, set_women_only)


@pytest.fixture
def listed(conn):
    import_allowlist(conn, "seed/allowlist_template.csv")
    return conn


def test_normalise_phone_handles_local_and_international():
    assert normalise_phone("0911223344") == "251911223344"
    assert normalise_phone("+251911223344") == "251911223344"
    assert normalise_phone("251 911 22 33 44") == "251911223344"
    assert normalise_phone("0911 22 33 44") == "251911223344"


def test_import_allowlist_returns_row_count(conn):
    assert import_allowlist(conn, "seed/allowlist_template.csv") == 2


def test_lookup_allowlist_normalises_the_phone(listed):
    assert lookup_allowlist(listed, "+251911223344")["full_name"] == "አበበ ከበደ"


def test_register_copies_verified_details_from_the_allowlist(listed):
    user = register(listed, telegram_id=1001, phone="0911223344")
    assert user["role"] == "driver"
    assert user["full_name"] == "አበበ ከበደ"
    assert user["tower"] == "B4"
    assert user["car_model"] == "Toyota Corolla"
    assert user["plate"] == "3-AA 21457"


def test_register_rejects_a_phone_that_was_never_verified(listed):
    with pytest.raises(NotAllowlisted):
        register(listed, telegram_id=1002, phone="0900000000")


def test_register_is_idempotent_for_the_same_person(listed):
    a = register(listed, telegram_id=1001, phone="0911223344")
    b = register(listed, telegram_id=1001, phone="0911223344")
    assert a["telegram_id"] == b["telegram_id"]


def test_register_marks_the_allowlist_row_as_claimed(listed):
    register(listed, telegram_id=1001, phone="0911223344")
    assert lookup_allowlist(listed, "0911223344")["claimed_by"] == 1001


def test_a_claimed_row_cannot_be_used_by_a_second_telegram_account(listed):
    register(listed, telegram_id=1001, phone="0911223344")
    with pytest.raises(NotAllowlisted):
        register(listed, telegram_id=9999, phone="0911223344")


def test_get_user_returns_none_for_a_stranger(conn):
    assert get_user(conn, 4242) is None


def test_register_rider_self_registers_without_the_allowlist(conn):
    # No allowlist import — riders arrive via the link, not the desk.
    user = register_rider(conn, telegram_id=2001, phone="0933445566",
                          full_name="Fan Tesfaye")
    assert user["role"] == "rider"
    assert user["full_name"] == "Fan Tesfaye"
    assert user["tower"] == ""          # riders carry no tower
    assert user["telegram_id"] == 2001


def test_register_rider_is_idempotent(conn):
    a = register_rider(conn, telegram_id=2001, phone="0933445566", full_name="Fan")
    b = register_rider(conn, telegram_id=2001, phone="0933445566", full_name="Fan")
    assert a["telegram_id"] == b["telegram_id"]


def test_allowlist_and_register_carry_car_seats(conn):
    import_allowlist(conn, "seed/allowlist_template.csv")
    entry = lookup_allowlist(conn, "0911223344")
    assert entry["car_seats"] == 4
    user = register(conn, telegram_id=1001, phone="0911223344")
    assert user["car_seats"] == 4


def test_self_registered_rider_has_no_car_seats(conn):
    user = register_rider(conn, telegram_id=2001, phone="0933445566",
                          full_name="Fan")
    assert user["car_seats"] is None


def test_set_women_only_preferences(listed):
    register(listed, telegram_id=1002, phone="0912334455")
    set_women_only(listed, 1002, women_only=True, women_present=False)
    user = get_user(listed, 1002)
    assert user["women_only"] == 1
    assert user["women_present"] == 0
