"""Streamlit web front end for the Sandfontein rate calculator.

Run locally:  streamlit run app.py
"""
from datetime import date, timedelta

import streamlit as st

from calculator import DEFAULT_CARD, load_rates, quote

rates = load_rates()
cards = list(rates["rate_cards"])

st.set_page_config(page_title="Sandfontein Rate Calculator", page_icon="🌄")
st.title("Sandfontein rate calculator")
st.caption(
    f"{rates['year']} exclusive-use rates. High season Apr–Oct, low season Nov–Mar. "
    "Children aged 6–15 pay 50%; babies aged 0–5 stay free. "
    "Stays of 5+ nights get 20% off, repeat guests 10% off (30% for both)."
)

rate_card = st.selectbox("Currency", cards, index=cards.index(DEFAULT_CARD),
                         format_func=lambda name: rates["rate_cards"][name]["currency"])

col1, col2, col3 = st.columns(3)
adults = col1.number_input("Adults", min_value=1, max_value=rates["max_guests"], value=2)
children = col2.number_input("Children (6–15)", min_value=0, max_value=rates["max_guests"], value=0)
babies = col3.number_input("Babies (0–5)", min_value=0, max_value=rates["max_guests"], value=0)

default_in = max(date.today(), date(rates["year"], 1, 1))
col4, col5 = st.columns(2)
check_in = col4.date_input("Check-in", value=default_in, format="YYYY-MM-DD")
check_out = col5.date_input("Check-out", value=check_in + timedelta(days=3), format="YYYY-MM-DD")

repeat_guest = st.checkbox("Repeat guests (10% off)")

try:
    q = quote(int(adults), int(children), int(babies), check_in, check_out, rate_card, rates,
              repeat_guest)
except ValueError as e:
    st.error(str(e))
    st.stop()

cur = q.currency
st.subheader(f"{q.nights} night{'s' * (q.nights != 1)}: "
             f"{q.high_nights} high season, {q.low_nights} low season")
if q.discount_reasons:
    st.success(f"{q.discount_rate:.0%} discount applied: {' + '.join(q.discount_reasons)}")
discounted = q.discount_rate > 0

def money(x):
    return f"{x:,.2f}"


rows = []
for line in q.lines:
    row = {"Guest": line.label}
    if q.high_nights:
        row[f"High season {cur}/night"] = money(line.high_rate)
    if q.low_nights:
        row[f"Low season {cur}/night"] = money(line.low_rate)
    row["Nights"] = str(q.nights)
    if discounted:
        row[f"Subtotal {cur}"] = money(line.subtotal)
        row[f"Discount {cur}"] = money(0 - line.discount)
    row[f"Total {cur}"] = money(line.total)
    rows.append(row)
blank = {k: "" for k in rows[0]}
total_row = {**blank, "Guest": "**Grand total**", f"Total {cur}": f"**{money(q.total)}**"}
if discounted:
    total_row[f"Subtotal {cur}"] = f"**{money(q.subtotal)}**"
    total_row[f"Discount {cur}"] = f"**{money(0 - q.discount)}**"
rows.append(total_row)

# A markdown table keeps the grand total row visually part of the table.
header = "| " + " | ".join(rows[0]) + " |"
align = "|" + "|".join([":--"] + ["--:"] * (len(rows[0]) - 1)) + "|"
body = "\n".join("| " + " | ".join(r.values()) + " |" for r in rows)
st.markdown(f"{header}\n{align}\n{body}")
st.metric("Grand total", f"{cur} {q.total:,.2f}")
st.metric("Average per person per night", f"{cur} {q.avg_pppn:,.2f}")
st.caption("Grand total divided by paying guests (adults and children) and nights. Babies are not counted.")

for w in q.warnings:
    st.warning(w)
st.caption("Fully inclusive of reserve activities, meals, drinks, laundry, VAT and levies. "
           "Excludes transport to and from Sandfontein, off-reserve activities, insurance and gratuities.")
