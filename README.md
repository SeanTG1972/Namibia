# Namibia

Tools for Sandfontein Lodge & Nature Reserve.

- [docs/](docs/): the guest rate calculator as a single web page, published with GitHub Pages at
  **https://seantg1972.github.io/Namibia/**. It quotes a stay guest by guest from the 2027 direct rates.
- [rate-calculator](rate-calculator/): the same calculator in Python (Streamlit web app and command line), with tests
  and the script that reads rates from the rates workbook.

## Turning on GitHub Pages

In the repo on GitHub: **Settings → Pages → Build and deployment**, set Source to "Deploy from a branch",
Branch to `main` and folder to `/docs`, then Save. The page is live a minute or two later.

## Putting the calculator on the website

Link to https://seantg1972.github.io/Namibia/, or embed it in a page:

```html
<iframe src="https://seantg1972.github.io/Namibia/" style="width:100%;height:1100px;border:0" title="Rate calculator"></iframe>
```

Add `?card=DirectRates%20(EUR)` (or NAD, GBP) to the address to open it in another currency.

## Updating rates

```bash
python rate-calculator/extract_rates.py path/to/Sandfontein-Rates-print-ready.xlsx
```

This rewrites `rate-calculator/rates.json` and `docs/rates.js`. The calculator is for direct bookings only, so
only the direct rate tabs are read; agent and STO rates are never exported, because this repo is public.
