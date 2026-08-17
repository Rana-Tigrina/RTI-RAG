from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    CaseCreateRequest,
    CaseCreateResponse,
    CaseUpdateRequest,
    DraftGenerateRequest,
    DraftGenerateResponse,
    ApproveDraftResponse,
    CaseSubmitRequest,
    CaseSubmitResponse,
    AppealGenerateRequest,
    AppealGenerateResponse,
    CaseDetailResponse,
    CaseEventResponse,
)
from app.services import case_service

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseCreateResponse, status_code=status.HTTP_201_CREATED)
def create_case_endpoint(req: CaseCreateRequest, db: Session = Depends(get_db)):
    case, questions = case_service.create_case(db, user_text=req.user_text, city=req.city)
    return CaseCreateResponse(
        case_id=case.id,
        status=case.status,
        issue_type=case.issue_type,
        department=case.department,
        municipal_body=case.municipal_body,
        questions=questions,
    )


@router.post("/{case_id}/draft", response_model=DraftGenerateResponse)
def generate_draft_endpoint(
    case_id: str,
    req: Optional[DraftGenerateRequest] = None,
    db: Session = Depends(get_db),
):
    submitted_on = req.submitted_on if req else None
    try:
        case, draft_result = case_service.generate_and_save_draft(db, case_id=case_id, submitted_on=submitted_on)
        return DraftGenerateResponse(
            case_id=case.id,
            status=case.status,
            draft_markdown=draft_result["draft_markdown"],
            fee=draft_result["fee"],
            legal_citations=draft_result["legal_citations"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{case_id}/approve", response_model=ApproveDraftResponse)
def approve_draft_endpoint(case_id: str, db: Session = Depends(get_db)):
    try:
        case = case_service.approve_draft(db, case_id=case_id)
        return ApproveDraftResponse(case_id=case.id, status=case.status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{case_id}/submit", response_model=CaseSubmitResponse)
def submit_case_endpoint(
    case_id: str,
    req: CaseSubmitRequest,
    db: Session = Depends(get_db),
):
    try:
        case = case_service.submit_case(db, case_id=case_id, submitted_on=req.submitted_on)
        return CaseSubmitResponse(
            case_id=case.id,
            status=case.status,
            submitted_on=case.submission_date,
            response_due_date=case.response_due_date,
            overdue_from=case.overdue_from,
            appeal_eligible_from=case.appeal_eligible_from,
            appeal_file_by=case.appeal_file_by,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{case_id}/appeal", response_model=AppealGenerateResponse)
def generate_appeal_endpoint(
    case_id: str,
    req: Optional[AppealGenerateRequest] = None,
    db: Session = Depends(get_db),
):
    as_of = req.as_of if req else None
    try:
        case, appeal_result = case_service.generate_and_save_appeal(db, case_id=case_id, as_of=as_of)
        return AppealGenerateResponse(
            case_id=case.id,
            status=case.status,
            appeal_markdown=appeal_result["appeal_markdown"],
            days_overdue=appeal_result["days_overdue"],
            legal_citations=appeal_result["legal_citations"],
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_case_endpoint(case_id: str, db: Session = Depends(get_db)):
    detail = case_service.get_case_detail(db, case_id=case_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")
    return detail


@router.patch("/{case_id}", response_model=CaseDetailResponse)
def update_case_endpoint(
    case_id: str,
    req: CaseUpdateRequest,
    db: Session = Depends(get_db),
):
    updates = req.model_dump(exclude_unset=True)
    try:
        case = case_service.update_case(db, case_id=case_id, updates=updates)
        detail = case_service.get_case_detail(db, case_id=case.id)
        return detail
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{case_id}", status_code=status.HTTP_200_OK)
def delete_case_endpoint(case_id: str, db: Session = Depends(get_db)):
    try:
        case_service.delete_case(db, case_id=case_id)
        return {"message": f"Case {case_id} successfully deleted"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{case_id}/events", response_model=List[CaseEventResponse])
def get_case_events_endpoint(case_id: str, db: Session = Depends(get_db)):
    events = case_service.get_case_events(db, case_id=case_id)
    return [
        CaseEventResponse(
            id=e["id"],
            case_id=e["case_id"],
            event_type=e["event_type"],
            payload=e["payload"],
            created_at=e["created_at"],
        )
        for e in events
    ]


@router.get("", response_model=List[dict])
def list_cases_endpoint(
    status: Optional[str] = Query(None, description="Filter by case status"),
    city: Optional[str] = Query(None, description="Filter by city name"),
    db: Session = Depends(get_db),
):
    return case_service.list_cases(db, status=status, city=city)
