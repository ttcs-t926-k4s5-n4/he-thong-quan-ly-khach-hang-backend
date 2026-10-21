import asyncio
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, SessionLocal, engine, get_db

Base.metadata.create_all(bind=engine)
app = FastAPI(title="SCRUM-83 Lead Assignment API", version="1.0.0")
worker_task = None
worker_stop = asyncio.Event()
MAX_JOB_ATTEMPTS = 5


def same(value_a, value_b):
    return (value_a or "").strip().casefold() == (value_b or "").strip().casefold()


def matching_rule(db: Session, lead: models.Lead):
    rules = db.query(models.AssignmentRule).order_by(models.AssignmentRule.priority.asc()).all()
    for rule in rules:
        if rule.region and not same(rule.region, lead.region):
            continue
        if rule.industry and not same(rule.industry, lead.industry):
            continue
        return rule
    return None


def process_one_job(db: Session) -> bool:
    job = (
        db.query(models.AssignmentJob)
        .filter(models.AssignmentJob.status == "pending")
        .order_by(models.AssignmentJob.queued_at.asc(), models.AssignmentJob.id.asc())
        .first()
    )
    if job is None:
        return False
    lead = db.query(models.Lead).filter_by(id=job.lead_id).first()
    if lead is None:
        job.status = "failed"
        job.error = "Lead không tồn tại"
        job.finished_at = datetime.utcnow()
        db.commit()
        return True

    try:
        rule = matching_rule(db, lead)
        if rule is None:
            lead.assignment_status = "manual_queue"
            job.status = "manual_queue"
            job.finished_at = datetime.utcnow()
        else:
            if rule.mode == "round_robin":
                index = rule.rotation_index % len(rule.assignees)
                lead.assigned_to = rule.assignees[index]
                rule.rotation_index = (index + 1) % len(rule.assignees)
            else:
                lead.assigned_to = rule.assignees[0]
            lead.assignment_status = "assigned"
            lead.assigned_by_rule_id = rule.id
            lead.assigned_at = datetime.utcnow()
            job.status = "completed"
            job.finished_at = datetime.utcnow()
        job.attempts += 1
        job.error = None
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.query(models.AssignmentJob).filter_by(id=job.id).first()
        if job is not None:
            job.attempts += 1
            job.error = str(exc)[:2000]
            if job.attempts >= MAX_JOB_ATTEMPTS:
                lead = db.query(models.Lead).filter_by(id=job.lead_id).first()
                if lead is not None:
                    lead.assignment_status = "manual_queue"
                job.status = "manual_queue"
                job.finished_at = datetime.utcnow()
            db.commit()
    return True


async def assignment_worker():
    """Persistent database-backed worker; pending work survives API process restarts."""
    while not worker_stop.is_set():
        db = SessionLocal()
        try:
            found_job = process_one_job(db)
        finally:
            db.close()
        if not found_job:
            try:
                await asyncio.wait_for(worker_stop.wait(), timeout=1)
            except asyncio.TimeoutError:
                pass
        else:
            await asyncio.sleep(0)


@app.on_event("startup")
async def start_worker():
    global worker_task
    worker_stop.clear()
    worker_task = asyncio.create_task(assignment_worker())


@app.on_event("shutdown")
async def stop_worker():
    worker_stop.set()
    if worker_task is not None:
        await worker_task


@app.get("/health")
def health():
    return {"status": "ok", "worker": "running" if worker_task and not worker_task.done() else "stopped"}


@app.put("/assignment/rules", response_model=List[schemas.AssignmentRuleOut])
def replace_rules(rule_set: schemas.RuleSet, db: Session = Depends(get_db)):
    try:
        db.query(models.AssignmentRule).delete(synchronize_session=False)
        rules = [models.AssignmentRule(**rule.dict()) for rule in rule_set.rules]
        db.add_all(rules)
        db.commit()
        return db.query(models.AssignmentRule).order_by(models.AssignmentRule.priority.asc()).all()
    except Exception:
        db.rollback()
        raise


@app.get("/assignment/rules", response_model=List[schemas.AssignmentRuleOut])
def get_rules(db: Session = Depends(get_db)):
    return db.query(models.AssignmentRule).order_by(models.AssignmentRule.priority.asc()).all()


@app.post("/leads", response_model=schemas.LeadOut, status_code=201)
def create_lead(lead_data: schemas.LeadCreate, db: Session = Depends(get_db)):
    lead = models.Lead(**(lead_data.dict()))
    db.add(lead)
    db.flush()
    db.add(models.AssignmentJob(lead_id=lead.id, status="pending"))
    db.commit()
    db.refresh(lead)
    return lead


@app.get("/assignment/jobs/{job_id}")
def get_assignment_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.AssignmentJob).filter_by(id=job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Assignment job không tồn tại")
    return {
        "id": job.id,
        "lead_id": job.lead_id,
        "status": job.status,
        "attempts": job.attempts,
        "error": job.error,
        "queued_at": job.queued_at,
        "finished_at": job.finished_at,
    }


@app.get("/assignment/jobs/lead/{lead_id}")
def get_lead_assignment_job(lead_id: int, db: Session = Depends(get_db)):
    job = (
        db.query(models.AssignmentJob)
        .filter_by(lead_id=lead_id)
        .order_by(models.AssignmentJob.id.desc())
        .first()
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy job cho lead này")
    return {
        "id": job.id,
        "lead_id": job.lead_id,
        "status": job.status,
        "attempts": job.attempts,
        "error": job.error,
        "queued_at": job.queued_at,
        "finished_at": job.finished_at,
    }


@app.get("/assignment/queue", response_model=List[schemas.LeadOut])
def get_manual_queue(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Lead)
        .filter(models.Lead.assignment_status == "manual_queue")
        .order_by(models.Lead.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.post("/leads/{lead_id}/assign", response_model=schemas.LeadOut)
def manually_assign(lead_id: int, request: schemas.ManualAssignment, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter_by(id=lead_id).first()
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead không tồn tại")
    lead.assigned_to = request.assignee.strip()
    lead.assignment_status = "assigned"
    lead.assigned_by_rule_id = None
    lead.assigned_at = datetime.utcnow()
    job = (
        db.query(models.AssignmentJob)
        .filter(models.AssignmentJob.lead_id == lead_id, models.AssignmentJob.status == "manual_queue")
        .order_by(models.AssignmentJob.id.desc())
        .first()
    )
    if job is not None:
        job.status = "completed"
        job.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return lead


@app.get("/leads/{lead_id}", response_model=schemas.LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter_by(id=lead_id).first()
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead không tồn tại")
    return lead
