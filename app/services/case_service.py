import uuid
import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Case, RTIDraft, AppealDraft, CaseEvent, LegalChunk
from app.services.issue_service import classify_civic_issue, needs_clarification
from app.services.department_service import resolve_department, resolve_municipal_body
from app.services.fee_service import calculate_fee
from app.services.deadline_service import calculate_deadline, calculate_first_appeal_deadline, is_overdue, _parse_date
from app.services.draft_service import generate_rti_draft
from app.services.appeal_service import generate_first_appeal


def record_event(db: Session, case_id: str, event_type: str, payload: Optional[Dict[str, Any]] = None):
    """Record an immutable audit event in the case history."""
    try:
        event = CaseEvent(
            id=str(uuid.uuid4()),
            case_id=case_id,
            event_type=event_type,
            payload=payload or {},
        )
        db.add(event)
    except Exception as e:
        print(f"Warning: Failed to record case event: {e}")


def create_case(db: Session, user_text: str, city: Optional[str] = None) -> tuple[Case, List[str]]:
    """Create and deterministically classify a new civic grievance case."""
    if not user_text or not user_text.strip():
        raise ValueError("Grievance description cannot be empty.")

    classification = classify_civic_issue(user_text)
    issue_type = classification["issue_type"]
    questions = needs_clarification(user_text)
    
    department = resolve_department(issue_type)
    municipal_body = resolve_municipal_body(city or "", issue_type)
    fee = calculate_fee(city or "")

    initial_status = "NEEDS_CLARIFICATION" if questions else "ISSUE_CLASSIFIED"
    case_id = str(uuid.uuid4())

    new_case = Case(
        id=case_id,
        user_text=user_text.strip(),
        city=city.strip() if city else None,
        jurisdiction="delhi" if city and city.lower().strip() in ("delhi", "new delhi") else "india",
        issue_type=issue_type,
        department=department,
        municipal_body=municipal_body,
        status=initial_status,
        fee_amount=fee["amount"],
        fee_json=fee,
    )
    
    try:
        db.add(new_case)
        record_event(db, case_id, "CASE_CREATED", {
            "user_text": user_text.strip(),
            "city": city,
            "issue_type": issue_type,
            "questions": questions,
            "status": initial_status,
        })
        db.commit()
        db.refresh(new_case)
        return new_case, questions
    except Exception:
        db.rollback()
        raise


def generate_and_save_draft(db: Session, case_id: str, submitted_on: Optional[str] = None) -> tuple[Case, dict]:
    """Generate an RTI draft application and record draft ready state."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    case_dict = {
        "id": case.id,
        "user_text": case.user_text,
        "city": case.city,
        "issue_type": case.issue_type,
        "department": case.department,
        "municipal_body": case.municipal_body,
        "submission_date": submitted_on or case.submission_date,
    }

    draft_result = generate_rti_draft(case_dict, submitted_on=submitted_on)
    
    try:
        rti_draft = RTIDraft(
            id=str(uuid.uuid4()),
            case_id=case.id,
            draft_markdown=draft_result["draft_markdown"],
            legal_citations_json=draft_result["legal_citations"],
        )
        db.add(rti_draft)

        case.status = "DRAFT_READY"
        record_event(db, case.id, "DRAFT_GENERATED", {
            "fee": draft_result["fee"],
            "citations_count": len(draft_result["legal_citations"]),
        })
        db.commit()
        db.refresh(case)
        return case, draft_result
    except Exception:
        db.rollback()
        raise


def approve_draft(db: Session, case_id: str) -> Case:
    """Approve draft and advance status to USER_APPROVED."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    try:
        case.status = "USER_APPROVED"
        record_event(db, case.id, "DRAFT_APPROVED", {})
        db.commit()
        db.refresh(case)
        return case
    except Exception:
        db.rollback()
        raise


def submit_case(db: Session, case_id: str, submitted_on: str) -> Case:
    """Record physical/portal submission and calculate statutory deadlines."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    deadline_info = calculate_deadline(submitted_on)
    appeal_info = calculate_first_appeal_deadline(deadline_info["response_due_date"])

    try:
        case.submission_date = deadline_info["submitted_on"]
        case.response_due_date = deadline_info["response_due_date"]
        case.overdue_from = deadline_info["overdue_from"]
        case.appeal_eligible_from = appeal_info["appeal_eligible_from"]
        case.appeal_file_by = appeal_info["appeal_file_by"]
        case.status = "SUBMITTED"

        record_event(db, case.id, "CASE_SUBMITTED", {
            "submitted_on": case.submission_date,
            "response_due_date": case.response_due_date,
            "overdue_from": case.overdue_from,
        })
        db.commit()
        db.refresh(case)
        return case
    except Exception:
        db.rollback()
        raise


def generate_and_save_appeal(db: Session, case_id: str, as_of: Optional[str] = None) -> tuple[Case, dict]:
    """Generate a First Appeal if the case is strictly overdue."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    case_dict = {
        "id": case.id,
        "user_text": case.user_text,
        "city": case.city,
        "issue_type": case.issue_type,
        "department": case.department,
        "municipal_body": case.municipal_body,
        "submission_date": case.submission_date,
        "response_due_date": case.response_due_date,
        "status": case.status,
    }

    appeal_result = generate_first_appeal(case_dict, as_of=as_of)

    try:
        appeal_draft = AppealDraft(
            id=str(uuid.uuid4()),
            case_id=case.id,
            appeal_markdown=appeal_result["appeal_markdown"],
            legal_citations_json=appeal_result["legal_citations"],
        )
        db.add(appeal_draft)

        case.status = "FIRST_APPEAL_READY"
        record_event(db, case.id, "APPEAL_GENERATED", {
            "days_overdue": appeal_result["days_overdue"],
            "citations_count": len(appeal_result["legal_citations"]),
        })
        db.commit()
        db.refresh(case)
        return case, appeal_result
    except Exception:
        db.rollback()
        raise


def update_case(db: Session, case_id: str, updates: dict) -> Case:
    """Update case fields with atomic recalculation."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    try:
        if "user_text" in updates and updates["user_text"]:
            case.user_text = updates["user_text"].strip()
            classification = classify_civic_issue(case.user_text)
            case.issue_type = classification["issue_type"]
            case.department = resolve_department(case.issue_type)
            case.municipal_body = resolve_municipal_body(case.city or "", case.issue_type)

        if "city" in updates and updates["city"]:
            case.city = updates["city"].strip()
            case.jurisdiction = "delhi" if case.city.lower() in ("delhi", "new delhi") else "india"
            case.municipal_body = resolve_municipal_body(case.city, case.issue_type)
            fee = calculate_fee(case.city)
            case.fee_amount = fee["amount"]
            case.fee_json = fee

        if "status" in updates and updates["status"]:
            case.status = updates["status"]

        record_event(db, case.id, "CASE_UPDATED", updates)
        db.commit()
        db.refresh(case)
        return case
    except Exception:
        db.rollback()
        raise


def delete_case(db: Session, case_id: str) -> bool:
    """Atomically delete a case and all associated drafts and audit events."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    try:
        db.query(RTIDraft).filter(RTIDraft.case_id == case_id).delete()
        db.query(AppealDraft).filter(AppealDraft.case_id == case_id).delete()
        db.query(CaseEvent).filter(CaseEvent.case_id == case_id).delete()
        db.delete(case)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def get_case_events(db: Session, case_id: str) -> List[dict]:
    events = db.query(CaseEvent).filter(CaseEvent.case_id == case_id).order_by(CaseEvent.created_at.asc()).all()
    return [
        {
            "id": ev.id,
            "case_id": ev.case_id,
            "event_type": ev.event_type,
            "payload": ev.payload,
            "created_at": str(ev.created_at) if ev.created_at else None,
        }
        for ev in events
    ]


def get_case_detail(db: Session, case_id: str) -> Optional[dict]:
    """Retrieve full case state with dynamic overdue status check."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return None

    # Check if case is submitted and overdue
    if case.status in ("SUBMITTED", "AWAITING_RESPONSE") and case.response_due_date:
        try:
            if is_overdue(case.response_due_date):
                case.status = "OVERDUE"
                db.commit()
                db.refresh(case)
        except Exception:
            pass

    latest_rti = db.query(RTIDraft).filter(RTIDraft.case_id == case.id).order_by(RTIDraft.created_at.desc()).first()
    latest_appeal = db.query(AppealDraft).filter(AppealDraft.case_id == case.id).order_by(AppealDraft.created_at.desc()).first()

    return {
        "id": case.id,
        "case_id": case.id,
        "user_text": case.user_text,
        "city": case.city,
        "jurisdiction": case.jurisdiction,
        "issue_type": case.issue_type,
        "department": case.department,
        "municipal_body": case.municipal_body,
        "status": case.status,
        "fee_amount": case.fee_amount,
        "fee_json": case.fee_json,
        "submission_date": case.submission_date,
        "response_due_date": case.response_due_date,
        "overdue_from": case.overdue_from,
        "appeal_eligible_from": case.appeal_eligible_from,
        "appeal_file_by": case.appeal_file_by,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
        "draft_markdown": latest_rti.draft_markdown if latest_rti else None,
        "appeal_markdown": latest_appeal.appeal_markdown if latest_appeal else None,
    }


def list_cases(db: Session, status: Optional[str] = None, city: Optional[str] = None) -> List[dict]:
    """List cases with optional filters and automated overdue updates."""
    query = db.query(Case)
    if status:
        query = query.filter(Case.status == status)
    if city:
        query = query.filter(Case.city.ilike(f"%{city.strip()}%"))

    cases = query.order_by(Case.created_at.desc()).all()
    results = []
    for c in cases:
        if c.status in ("SUBMITTED", "AWAITING_RESPONSE") and c.response_due_date:
            try:
                if is_overdue(c.response_due_date):
                    c.status = "OVERDUE"
                    db.commit()
                    db.refresh(c)
            except Exception:
                pass
        results.append({
            "id": c.id,
            "case_id": c.id,
            "user_text": c.user_text,
            "city": c.city,
            "issue_type": c.issue_type,
            "department": c.department,
            "municipal_body": c.municipal_body,
            "status": c.status,
            "fee_amount": c.fee_amount,
            "submission_date": c.submission_date,
            "response_due_date": c.response_due_date,
            "created_at": c.created_at,
        })
    return results


def get_system_stats(db: Session) -> dict:
    """Calculate system-wide aggregate metrics."""
    total_cases = db.query(Case).count()
    
    statuses = db.query(Case.status, func.count(Case.id)).group_by(Case.status).all()
    status_counts = {s: count for s, count in statuses}

    issues = db.query(Case.issue_type, func.count(Case.id)).group_by(Case.issue_type).all()
    issue_type_counts = {i: count for i, count in issues}

    cities = db.query(Case.city, func.count(Case.id)).group_by(Case.city).all()
    city_counts = {(c or "Unspecified"): count for c, count in cities}

    total_legal_chunks = db.query(LegalChunk).count()

    return {
        "total_cases": total_cases,
        "status_counts": status_counts,
        "issue_type_counts": issue_type_counts,
        "city_counts": city_counts,
        "total_legal_chunks": total_legal_chunks,
    }
