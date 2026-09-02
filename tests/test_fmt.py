from datetime import datetime, timedelta

from gararide.fmt import fmt_day, fmt_money, fmt_person, fmt_time, fmt_when


def test_fmt_time_shows_both_clocks():
    assert fmt_time(datetime(2026, 9, 3, 7, 0)) == "07:00 (1:00 ጠዋት)"


def test_fmt_time_ethiopian_hour_wraps_at_twelve():
    # 06:45 western -> 12:45 Ethiopian (the hour before 1:00)
    assert fmt_time(datetime(2026, 9, 3, 6, 45)) == "06:45 (12:45 ጠዋት)"


def test_fmt_time_afternoon_uses_the_afternoon_word():
    assert fmt_time(datetime(2026, 9, 3, 17, 30)) == "17:30 (11:30 ከሰዓት)"


def test_fmt_day_today_and_tomorrow():
    now = datetime.now()
    assert fmt_day(now) == "ዛሬ"
    assert fmt_day(now + timedelta(days=1)) == "ነገ"


def test_fmt_day_further_out_uses_a_date():
    far = datetime.now() + timedelta(days=9)
    assert fmt_day(far) == far.strftime("%b %d")


def test_fmt_when_combines_day_and_both_clocks():
    tomorrow = (datetime.now() + timedelta(days=1)).replace(
        hour=7, minute=0, second=0, microsecond=0)
    assert fmt_when(tomorrow) == "ነገ 07:00 (1:00 ጠዋት)"


def test_fmt_money():
    assert fmt_money(55) == "55 ብር"


def test_fmt_person_shows_tower_never_floor():
    row = {"full_name": "አበበ ከበደ", "tower": "B4"}
    out = fmt_person(row)
    assert out == "አበበ ከበደ · Tower B4"
    assert "floor" not in out.lower()


def test_fmt_person_rider_without_tower_shows_name_only():
    # Riders self-register with no tower; show the name alone, no dangling "Tower".
    assert fmt_person({"full_name": "ፋን", "tower": ""}) == "ፋን"
