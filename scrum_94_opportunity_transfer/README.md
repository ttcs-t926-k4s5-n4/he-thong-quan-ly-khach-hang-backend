# SCRUM-94 — Transfer opportunity ownership

Transfer one or multiple opportunities atomically. Each transfer records the previous/new owner, actor, reason and timestamp. New owners see opportunities through their owner-filtered list; activity records remain linked and accessible.

Run `pip install -r requirements.txt` then `uvicorn main:app --app-dir scrum_94_opportunity_transfer --reload`; docs at `/docs`.
