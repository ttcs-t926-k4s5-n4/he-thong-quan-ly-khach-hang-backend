# SCRUM-92 — Weighted sales forecast

Forecast is sum(opportunity amount × stage probability), grouped by expected-close month, quarter, owner, or team. API compares forecast with configured target and closed-won actual revenue.

Run `pip install -r requirements.txt` then `uvicorn main:app --app-dir scrum_92_sales_forecast --reload`; docs at `/docs`.
