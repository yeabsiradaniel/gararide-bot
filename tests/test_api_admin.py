import pytest
from fastapi.testclient import TestClient

from gararide.api.app import create_app
from gararide.places import place_by_slug
from gararide.users import import_allowlist, register, register_rider
from tests.test_api_auth import BOT_TOKEN, make_init_data


@pytest.fixture
def client(seeded):
    import_allowlist(seeded, "seed/allowlist_template.csv")
    register(seeded, telegram_id=1001, phone="0911223344")       # admin driver
    register_rider(seeded, telegram_id=2001, phone="0999999999", full_name="Fan")
    app = create_app(seeded, BOT_TOKEN, admin_ids=frozenset({1001}))
    return seeded, TestClient(app)


def _auth(uid):
    return {"Authorization": "tma " + make_init_data({"id": uid})}


def test_non_admin_is_forbidden(client):
    _, c = client
    assert c.get("/admin/ops", headers=_auth(2001)).status_code == 403


def test_admin_gets_the_ops_counts(client):
    _, c = client
    r = c.get("/admin/ops", headers=_auth(1001))
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"trips", "seats", "no_shows", "open_requests", "users"}
    assert body["users"] == 2


def test_unmatched_search_becomes_a_recruitment_row(client):
    conn, c = client
    kaz = place_by_slug(conn, "kazanchis")["id"]
    # A rider searches with no trips posted -> a results=0 search_log row.
    c.get("/trips/search", params={"dest_place_id": kaz}, headers=_auth(2001))
    rows = c.get("/admin/unmatched", headers=_auth(1001)).json()
    assert rows and rows[0]["dest_name"] == "Kazanchis" and rows[0]["riders"] >= 1


def test_admin_adds_a_driver_to_the_roster(client):
    conn, c = client
    r = c.post("/admin/drivers", headers=_auth(1001), json={
        "phone": "0912345678", "full_name": "Test Driver", "tower": "B4",
        "car_model": "Toyota Corolla", "plate": "3-AA 21457", "car_seats": 4})
    assert r.status_code == 201
    body = r.json()
    assert body["full_name"] == "Test Driver" and body["car_seats"] == 4
    assert body["onboarded"] is False  # not yet claimed via the bot

    # The new driver can now register through the bot and lands as a driver.
    from gararide.users import register
    u = register(conn, telegram_id=3003, phone="0912345678")
    assert u["role"] == "driver" and u["car_seats"] == 4

    # And they show up in the roster, now onboarded.
    roster = c.get("/admin/drivers", headers=_auth(1001)).json()
    yeab = next(d for d in roster if d["full_name"] == "Test Driver")
    assert yeab["onboarded"] is True


def test_add_driver_rejects_bad_input(client):
    _, c = client
    # missing name
    assert c.post("/admin/drivers", headers=_auth(1001), json={
        "phone": "0912345678", "full_name": "  ", "tower": "B4",
        "car_seats": 4}).status_code == 422
    # nonsense seat count
    assert c.post("/admin/drivers", headers=_auth(1001), json={
        "phone": "0912345678", "full_name": "Test Driver", "tower": "B4",
        "car_seats": 99}).status_code == 422


def test_car_color_is_stored_and_reaches_the_rider(client):
    conn, c = client
    from gararide.places import place_by_slug
    from gararide.trips import post_trip
    from gararide.users import register, register_rider
    c.post("/admin/drivers", headers=_auth(1001), json={
        "phone": "0912345678", "full_name": "Test Driver", "tower": "B4",
        "car_model": "Vitz", "car_color": "Silver", "plate": "3-AA 9", "car_seats": 4})
    # roster keeps the colour
    roster = c.get("/admin/drivers", headers=_auth(1001)).json()
    assert next(d for d in roster if d["full_name"] == "Test Driver")["car_color"] == "Silver"
    # it flows onto the driver's record, then onto the rider's trip card
    drv = register(conn, telegram_id=4004, phone="0912345678")
    assert drv["car_color"] == "Silver"
    register_rider(conn, telegram_id=2002, phone="0900000002", full_name="R")
    kaz = place_by_slug(conn, "kazanchis")["id"]
    tid = post_trip(conn, driver_id=4004, dest_place_id=kaz, dropoff_place_ids=[kaz],
                    depart_at=__import__("datetime").datetime(2999, 1, 1, 7), seats=2)
    card = c.post("/bookings", headers=_auth(2002),
                  json={"trip_id": tid, "to_place_id": kaz}).json()
    assert card["car_color"] == "Silver"


def test_admin_edits_a_driver_and_it_reaches_the_live_record(client):
    conn, c = client
    from gararide.users import get_user, register
    c.post("/admin/drivers", headers=_auth(1001), json={
        "phone": "0912345678", "full_name": "Old", "tower": "B4",
        "car_model": "Vitz", "car_color": "Silver", "plate": "3-AA 9", "car_seats": 4})
    register(conn, telegram_id=5005, phone="0912345678")  # already onboarded
    r = c.patch("/admin/drivers/0912345678", headers=_auth(1001), json={
        "phone": "0912345678", "full_name": "New Name", "tower": "C1",
        "car_model": "Corolla", "car_color": "Blue", "plate": "3-AA 10", "car_seats": 3})
    assert r.status_code == 200
    d = next(x for x in c.get("/admin/drivers", headers=_auth(1001)).json()
             if x["phone"].endswith("912345678"))
    assert d["full_name"] == "New Name" and d["tower"] == "C1" and d["car_color"] == "Blue" and d["car_seats"] == 3
    u = get_user(conn, 5005)  # live user updated too
    assert u["full_name"] == "New Name" and u["car_color"] == "Blue" and u["car_seats"] == 3


def test_editing_an_unknown_driver_is_404(client):
    _, c = client
    assert c.patch("/admin/drivers/0900000000", headers=_auth(1001), json={
        "phone": "0900000000", "full_name": "X", "tower": "B", "car_seats": 4}).status_code == 404


def test_non_admin_cannot_edit_a_driver(client):
    _, c = client
    assert c.patch("/admin/drivers/0912345678", headers=_auth(2001), json={
        "phone": "0912345678", "full_name": "X", "tower": "B", "car_seats": 4}).status_code == 403


def test_non_admin_cannot_add_a_driver(client):
    _, c = client
    r = c.post("/admin/drivers", headers=_auth(2001), json={
        "phone": "0912345678", "full_name": "Test Driver", "tower": "B4", "car_seats": 4})
    assert r.status_code == 403


def test_rider_added_to_the_roster_is_promoted_on_next_app_open(client):
    # 2001 registered as a rider (phone 0999999999). Admin now desk-verifies that
    # same phone as a driver — the rider should become a driver next time /me loads.
    _, c = client
    assert c.get("/me", headers=_auth(2001)).json()["role"] == "rider"
    r = c.post("/admin/drivers", headers=_auth(1001), json={
        "phone": "0999999999", "full_name": "Promoted", "tower": "C3",
        "car_model": "Vitz", "plate": "3-AA 9", "car_seats": 4})
    assert r.status_code == 201
    me = c.get("/me", headers=_auth(2001)).json()
    assert me["role"] == "driver" and me["car_seats"] == 4 and me["tower"] == "C3"
    # and they can now use a driver-only endpoint
    assert c.get("/trips/mine", headers=_auth(2001)).status_code == 200


def test_admin_removes_a_pending_driver(client):
    _, c = client
    c.post("/admin/drivers", headers=_auth(1001), json={
        "phone": "0912345678", "full_name": "Test Driver", "tower": "B4", "car_seats": 4})
    r = c.delete("/admin/drivers/0912345678", headers=_auth(1001))
    assert r.status_code == 200 and r.json()["was_onboarded"] is False
    roster = c.get("/admin/drivers", headers=_auth(1001)).json()
    assert not any(d["full_name"] == "Test Driver" for d in roster)


def test_removing_an_onboarded_driver_cancels_trips_and_locks_them_out(client):
    conn, c = client
    from gararide.places import place_by_slug
    from gararide.users import register
    # add + onboard a driver, then have them post a trip
    c.post("/admin/drivers", headers=_auth(1001), json={
        "phone": "0912345678", "full_name": "Test Driver", "tower": "B4", "car_seats": 4})
    register(conn, telegram_id=3003, phone="0912345678")
    kaz = place_by_slug(conn, "kazanchis")["id"]
    posted = c.post("/trips", headers=_auth(3003), json={
        "dest_place_id": kaz, "dropoff_place_ids": [], "seats": 2,
        "depart_at": "2999-01-01T07:00:00"})
    assert posted.status_code == 201

    r = c.delete("/admin/drivers/0912345678", headers=_auth(1001))
    assert r.status_code == 200
    body = r.json()
    assert body["was_onboarded"] is True and body["trips_cancelled"] == 1
    # the trip is gone and the driver can no longer use the app
    assert c.get("/trips/mine", headers=_auth(3003)).status_code == 404
    assert c.get("/me", headers=_auth(3003)).status_code == 404


def test_admin_cannot_remove_themselves(client):
    _, c = client
    # 1001 registered from allowlist_template — remove by their own phone
    from gararide.users import get_user
    conn, _ = client
    me = get_user(conn, 1001)
    assert c.delete(f"/admin/drivers/{me['phone']}", headers=_auth(1001)).status_code == 400


def test_removing_a_phone_not_on_roster_is_404(client):
    _, c = client
    assert c.delete("/admin/drivers/0900000000", headers=_auth(1001)).status_code == 404


def test_non_admin_cannot_remove_a_driver(client):
    _, c = client
    assert c.delete("/admin/drivers/0912345678", headers=_auth(2001)).status_code == 403
