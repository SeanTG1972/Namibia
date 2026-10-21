# Sandfontein rate calculator

Quotes a stay at Sandfontein Lodge & Nature Reserve, showing what each guest pays and the grand total.

Enter the number of adults, children (6–15, 50% off), babies (0–5, free) and the check-in and check-out dates. The calculator prices every night at the high season (Apr–Oct) or low season (Nov–Mar) rate, so stays that cross a season change are priced correctly.

## How pricing works

It is for bookings made directly with Sandfontein, so it uses the 2027 direct rates only (`rates.json`, USD by default, with NAD, EUR and GBP available). Agent and STO rates are deliberately not included because this repo is public. Each guest's nightly rate depends on their position in the party: the 1st guest pays the most, the 2nd less, and so on. Adults take the first positions, children are counted as the last paying guests at half the rate for their position, and babies are free and take no position.

Discounts apply to the whole booking: 20% for stays of 5 nights or more, and 10% when the guests are repeat guests. They add together, so repeat guests staying 5+ nights get 30% off. The table then shows each guest's subtotal, discount and total.

## Run it

```bash
cd rate-calculator
pip install -r requirements.txt
streamlit run app.py          # web calculator
python calculator.py --adults 4 --children 2 --babies 1 --check-in 2027-03-29 --check-out 2027-04-03 --repeat
pytest                        # tests
```

## Publish it

The quickest way to make it public is [Streamlit Community Cloud](https://share.streamlit.io): sign in with GitHub, choose the `SeanTG1972/Namibia` repo, branch `main` and main file path `rate-calculator/app.py`, and deploy. It is free and gives you a URL you can link from the website.

## Update rates for a new year

```bash
python extract_rates.py path/to/Sandfontein-Rates-print-ready.xlsx
```

This rewrites `rates.json` and `../docs/rates.js` from the "Actual cost paid by each guest" columns of the direct rate tabs.
