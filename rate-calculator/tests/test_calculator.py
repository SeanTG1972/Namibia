from datetime import date

import pytest

from calculator import load_rates, quote

RATES = load_rates()


def test_single_adult_one_high_night():
    q = quote(1, 0, 0, date(2027, 6, 1), date(2027, 6, 2), rates=RATES)
    assert q.total == 1600


def test_whole_party_matches_sheet_total_per_night():
    # Direct USD sheet: 18 guests, high season, whole reserve = 9,290 per night
    q = quote(18, 0, 0, date(2027, 5, 1), date(2027, 5, 2), rates=RATES)
    assert q.total == 9290
    q = quote(18, 0, 0, date(2027, 1, 1), date(2027, 1, 2), rates=RATES)
    assert q.total == 7480


def test_children_take_last_positions_at_half_price_and_babies_free():
    q = quote(2, 2, 1, date(2027, 7, 1), date(2027, 7, 3), rates=RATES)
    by_label = {line.label: line for line in q.lines}
    assert by_label["Child 1"].position == 3
    assert by_label["Child 1"].total == 1030 * 0.5 * 2
    assert by_label["Child 2"].total == 830 * 0.5 * 2
    assert by_label["Baby 1"].total == 0
    assert q.total == (1600 + 1280 + 515 + 415) * 2


def test_stay_across_season_change_prices_each_night():
    # 30 Mar and 31 Mar are low season, 1 Apr and 2 Apr are high season
    q = quote(1, 0, 0, date(2027, 3, 30), date(2027, 4, 3), rates=RATES)
    assert (q.low_nights, q.high_nights) == (2, 2)
    assert q.total == 2 * 1280 + 2 * 1600


def test_other_rate_card():
    q = quote(1, 0, 0, date(2027, 6, 1), date(2027, 6, 2), "DirectRates (NAD)", RATES)
    assert q.currency == "NAD" and q.total == 25990


def test_warns_outside_rate_year():
    q = quote(1, 0, 0, date(2027, 12, 30), date(2028, 1, 2), rates=RATES)
    assert q.warnings


@pytest.mark.parametrize("args", [
    (0, 1, 0, date(2027, 6, 1), date(2027, 6, 2)),   # no adult
    (10, 9, 0, date(2027, 6, 1), date(2027, 6, 2)),  # too many guests
    (2, 0, 0, date(2027, 6, 2), date(2027, 6, 2)),   # zero nights
])
def test_invalid_input(args):
    with pytest.raises(ValueError):
        quote(*args, rates=RATES)


def test_no_discount_under_five_nights():
    q = quote(1, 0, 0, date(2027, 6, 1), date(2027, 6, 5), rates=RATES)
    assert q.discount_rate == 0 and q.total == 4 * 1600


def test_long_stay_discount():
    q = quote(1, 0, 0, date(2027, 6, 1), date(2027, 6, 6), rates=RATES)
    assert q.discount_rate == 0.2
    assert q.subtotal == 5 * 1600 and q.total == 5 * 1600 * 0.8


def test_repeat_guest_discount():
    q = quote(2, 0, 0, date(2027, 6, 1), date(2027, 6, 2), rates=RATES, repeat_guest=True)
    assert q.discount_rate == 0.1 and q.total == (1600 + 1280) * 0.9


def test_repeat_guest_long_stay_gets_30_percent():
    q = quote(1, 1, 1, date(2027, 6, 1), date(2027, 6, 8), rates=RATES, repeat_guest=True)
    assert q.discount_rate == 0.3
    child = next(line for line in q.lines if line.guest_type == "Child")
    assert child.total == pytest.approx(1280 * 0.5 * 7 * 0.7)
    assert q.total == pytest.approx((1600 + 640) * 7 * 0.7)


def test_average_per_person_per_night_includes_children_and_babies():
    q = quote(2, 1, 1, date(2027, 6, 1), date(2027, 6, 3), rates=RATES)
    assert q.total == (1600 + 1280 + 515) * 2
    assert q.avg_pppn == round(q.total / 4 / 2, 2)
