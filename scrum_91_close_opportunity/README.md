# SCRUM-91 — Close opportunity

Standalone FastAPI service for winning/losing opportunities. Wins require actual deal value and signed date; losses require a loss reason and optionally the winning competitor. Closed opportunities are locked. Only a manager can reopen, with a required reason. Won revenue is attributed to the current owner.

Run with `pip install -r requirements.txt` then `uvicorn main:app --app-dir scrum_91_close_opportunity --reload`. Interactive API docs: `/docs`.
