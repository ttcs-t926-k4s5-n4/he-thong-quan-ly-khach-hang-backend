# SCRUM-102 — Customer interaction timeline

Append-only interaction timeline for a customer: activities, opportunity changes and sent quotes can be queried together in chronological order, filtered by event kind and actor, with pagination.

Run `pip install -r requirements.txt` then `uvicorn main:app --app-dir scrum_102_customer_timeline --reload`; docs at `/docs`.
