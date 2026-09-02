from gararide.blocks import block, blocked_pairs


def test_block_is_recorded(people):
    conn, driver, rider = people
    block(conn, rider["telegram_id"], driver["telegram_id"])
    assert driver["telegram_id"] in blocked_pairs(conn, rider["telegram_id"])


def test_a_block_hides_in_both_directions(people):
    conn, driver, rider = people
    block(conn, rider["telegram_id"], driver["telegram_id"])
    # The driver never learns about it, but must not be matched either.
    assert rider["telegram_id"] in blocked_pairs(conn, driver["telegram_id"])


def test_block_is_idempotent(people):
    conn, driver, rider = people
    block(conn, rider["telegram_id"], driver["telegram_id"])
    block(conn, rider["telegram_id"], driver["telegram_id"])
    assert len(blocked_pairs(conn, rider["telegram_id"])) == 1


def test_no_blocks_by_default(people):
    conn, _, rider = people
    assert blocked_pairs(conn, rider["telegram_id"]) == set()
