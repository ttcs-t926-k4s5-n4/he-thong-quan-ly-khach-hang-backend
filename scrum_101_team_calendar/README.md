# SCRUM-101 — Team calendar

Store meetings and due-dated tasks and retrieve day/week/month views. Meeting creation rejects overlapping meetings for the same attendee; team members can inspect a colleague's schedule and managers can inspect the team. Times must include a timezone offset.

Run `pip install -r requirements.txt` then `uvicorn main:app --app-dir scrum_101_team_calendar --reload`; docs at `/docs`.
