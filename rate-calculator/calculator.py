"""Sandfontein guest rate calculator.

Pricing rules (from the 2027 rate sheets):
  * Exclusive use; each guest's nightly rate depends on their position in the
    party (1st guest pays most, 2nd less, ...) and on the season of that night
    (high season Apr-Oct, low season Nov-Mar).
  * Adults fill the first positions. Children (6-15) are counted as the last
    paying guests and pay 50% of the rate for their position.
  * Babies (0-5) stay free and do not take a paying position.
  * Stays of 5 nights or more get 20% off; repeat guests get 10% off. The two
    add together, so a repeat guest staying 5+ nights gets 30% off.

Command line:
    python calculator.py --adults 4 --children 2 --babies 1 \
        --check-in 2027-03-29 --check-out 2027-04-03 --repeat
"""
import argparse
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

RATES_FILE = Path(__file__).with_name("rates.json")
DEFAULT_CARD = "DirectRates (USD)"


def load_rates(path=RATES_FILE):
    return json.loads(Path(path).read_text())


@dataclass
class GuestLine:
    label: str
    guest_type: str  # "Adult", "Child" or "Baby"
    position: int | None  # rate-sheet position, None for babies
    high_nights: int
    low_nights: int
    high_rate: float  # per night, after any child discount
    low_rate: float
    subtotal: float  # before the booking discount
    discount: float
    total: float


@dataclass
class Quote:
    rate_card: str
    currency: str
    check_in: date
    check_out: date
    nights: int
    high_nights: int
    low_nights: int
    lines: list[GuestLine]
    discount_rate: float
    discount_reasons: list[str]
    subtotal: float
    discount: float
    total: float
    warnings: list[str] = field(default_factory=list)


def is_high_season(night, rates):
    return night.month in rates["high_season_months"]


def booking_discount(nights, repeat_guest, rates):
    """Return (rate, reasons) for the discount applied to the whole booking."""
    rate, reasons = 0.0, []
    if nights >= rates["long_stay_nights"]:
        rate += rates["long_stay_discount"]
        reasons.append(f"{rates['long_stay_discount']:.0%} for {rates['long_stay_nights']}+ nights")
    if repeat_guest:
        rate += rates["repeat_guest_discount"]
        reasons.append(f"{rates['repeat_guest_discount']:.0%} repeat guest")
    return round(rate, 4), reasons


def quote(adults, children, babies, check_in, check_out, rate_card=DEFAULT_CARD, rates=None,
          repeat_guest=False):
    rates = rates or load_rates()
    if rate_card not in rates["rate_cards"]:
        raise ValueError(f"Unknown rate card {rate_card!r}")
    card = rates["rate_cards"][rate_card]
    max_guests = rates["max_guests"]

    if min(adults, children, babies) < 0:
        raise ValueError("Guest numbers cannot be negative.")
    if adults < 1:
        raise ValueError("At least one adult is required.")
    if adults + children > max_guests:
        raise ValueError(f"Sandfontein sleeps at most {max_guests} paying guests.")
    if check_out <= check_in:
        raise ValueError("Check-out must be after check-in.")

    nights = [check_in + timedelta(days=i) for i in range((check_out - check_in).days)]
    high_nights = sum(is_high_season(n, rates) for n in nights)
    low_nights = len(nights) - high_nights

    warnings = []
    year = rates["year"]
    if any(n.year != year for n in nights):
        warnings.append(f"Some nights fall outside {year}; {year} rates have been used for them.")
    if adults + children + babies > max_guests:
        warnings.append(f"The party (including babies) is larger than the {max_guests} beds available.")

    discount_rate, discount_reasons = booking_discount(len(nights), repeat_guest, rates)

    lines = []
    party = [("Adult", 1.0)] * adults + [("Child", 1 - rates["child_discount"])] * children
    counts = {"Adult": 0, "Child": 0, "Baby": 0}
    for position, (guest_type, factor) in enumerate(party, start=1):
        counts[guest_type] += 1
        high_rate = card["high"][position - 1] * factor
        low_rate = card["low"][position - 1] * factor
        subtotal = round(high_rate * high_nights + low_rate * low_nights, 2)
        discount = round(subtotal * discount_rate, 2)
        lines.append(GuestLine(
            label=f"{guest_type} {counts[guest_type]}",
            guest_type=guest_type,
            position=position,
            high_nights=high_nights,
            low_nights=low_nights,
            high_rate=high_rate,
            low_rate=low_rate,
            subtotal=subtotal,
            discount=discount,
            total=round(subtotal - discount, 2),
        ))
    for i in range(1, babies + 1):
        lines.append(GuestLine(f"Baby {i}", "Baby", None, high_nights, low_nights, 0.0, 0.0, 0.0, 0.0, 0.0))

    return Quote(
        rate_card=rate_card,
        currency=card["currency"],
        check_in=check_in,
        check_out=check_out,
        nights=len(nights),
        high_nights=high_nights,
        low_nights=low_nights,
        lines=lines,
        discount_rate=discount_rate,
        discount_reasons=discount_reasons,
        subtotal=round(sum(line.subtotal for line in lines), 2),
        discount=round(sum(line.discount for line in lines), 2),
        total=round(sum(line.total for line in lines), 2),
        warnings=warnings,
    )


def format_table(q):
    cur = q.currency
    discounted = q.discount_rate > 0
    head = f"{'Guest':<10} {'Sheet position':>14} {'Nightly rate':>22} {'Nights':>7}"
    if discounted:
        head += f" {'Subtotal':>12} {'Discount':>12}"
    head += f" {'Total ' + cur:>14}"
    rows = [head, "-" * len(head)]
    for line in q.lines:
        position = "free" if line.position is None else f"{line.position}"
        if q.high_nights and q.low_nights:
            rate = f"{line.high_rate:,.0f} hi / {line.low_rate:,.0f} lo"
        else:
            rate = f"{(line.high_rate if q.high_nights else line.low_rate):,.2f}"
        row = f"{line.label:<10} {position:>14} {rate:>22} {q.nights:>7}"
        if discounted:
            row += f" {line.subtotal:>12,.2f} {0 - line.discount:>12,.2f}"
        rows.append(row + f" {line.total:>14,.2f}")
    rows.append("-" * len(head))
    total = f"{'GRAND TOTAL':<{len(head) - 15}} {q.total:>14,.2f}"
    if discounted:
        total = (f"{'GRAND TOTAL':<{len(head) - 41}} {q.subtotal:>12,.2f} "
                 f"{0 - q.discount:>12,.2f} {q.total:>14,.2f}")
    rows.append(total)
    return "\n".join(rows)


def main():
    rates = load_rates()
    parser = argparse.ArgumentParser(description="Quote a Sandfontein stay per guest.")
    parser.add_argument("--adults", type=int, required=True)
    parser.add_argument("--children", type=int, default=0, help="aged 6-15, 50%% off")
    parser.add_argument("--babies", type=int, default=0, help="aged 0-5, free")
    parser.add_argument("--check-in", type=date.fromisoformat, required=True, help="YYYY-MM-DD")
    parser.add_argument("--check-out", type=date.fromisoformat, required=True, help="YYYY-MM-DD")
    parser.add_argument("--repeat", action="store_true", help="repeat guests, 10%% off")
    parser.add_argument("--rate-card", default=DEFAULT_CARD, choices=list(rates["rate_cards"]))
    args = parser.parse_args()
    try:
        q = quote(args.adults, args.children, args.babies, args.check_in, args.check_out,
                  args.rate_card, rates, args.repeat)
    except ValueError as e:
        parser.error(str(e))
    print(f"{q.rate_card}: {q.check_in} to {q.check_out}, {q.nights} nights "
          f"({q.high_nights} high season, {q.low_nights} low season)")
    if q.discount_reasons:
        print(f"Discount: {q.discount_rate:.0%} ({' + '.join(q.discount_reasons)})")
    print()
    print(format_table(q))
    for w in q.warnings:
        print(f"\nNote: {w}")


if __name__ == "__main__":
    main()
