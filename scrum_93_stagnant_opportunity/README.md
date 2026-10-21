# SCRUM-93 — Stagnant opportunity alerts

Configure inactivity days by stage and flag open opportunities with no logged activity or overdue expected-close dates. Run the daily evaluator with `POST /alerts/evaluate` (intended for a daily scheduler); team leads can view flagged opportunities at `GET /alerts`.

Run `pip install -r requirements.txt` then `uvicorn main:app --app-dir scrum_93_stagnant_opportunity --reload`; docs at `/docs`.
