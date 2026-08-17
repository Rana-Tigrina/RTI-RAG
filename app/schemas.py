from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CitationSchema(BaseModel):
    id: str
    source: str
    section: str
    title: str


class FeeSchema(BaseModel):
    amount: int
    currency: str = "INR"
    notes: str
    citation: Optional[CitationSchema] = None


class CaseCreateRequest(BaseModel):
    user_text: str = Field(..., min_length=1, description="Description of the civic issue")
    city: Optional[str] = Field(None, description="City name e.g. Delhi, Bengaluru")


class CaseCreateResponse(BaseModel):
    case_id: str
    status: str
    issue_type: str
    department: str
    municipal_body: str
    questions: List[str] = Field(default_factory=list)


class CaseUpdateRequest(BaseModel):
    user_text: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None


class DraftGenerateRequest(BaseModel):
    submitted_on: Optional[str] = Field(None, description="YYYY-MM-DD date if known")


class DraftGenerateResponse(BaseModel):
    case_id: str
    status: str
    draft_markdown: str
    fee: FeeSchema
    legal_citations: List[CitationSchema] = Field(default_factory=list)


class ApproveDraftResponse(BaseModel):
    case_id: str
    status: str


class CaseSubmitRequest(BaseModel):
    submitted_on: str = Field(..., description="Date of submission in YYYY-MM-DD format")


class CaseSubmitResponse(BaseModel):
    case_id: str
    status: str
    submitted_on: str
    response_due_date: str
    overdue_from: str
    appeal_eligible_from: str
    appeal_file_by: str


class AppealGenerateRequest(BaseModel):
    as_of: Optional[str] = Field(None, description="Current evaluation date in YYYY-MM-DD format")


class AppealGenerateResponse(BaseModel):
    case_id: str
    status: str
    appeal_markdown: str
    days_overdue: int
    legal_citations: List[CitationSchema] = Field(default_factory=list)


class CaseEventResponse(BaseModel):
    id: str
    case_id: str
    event_type: str
    payload: Optional[Dict[str, Any]] = None
    created_at: str


class LegalChunkResponse(BaseModel):
    id: str
    jurisdiction: str
    act: str
    section: str
    topic: str
    title: str
    text: str
    source: str
    updated_at: Optional[str] = None


class SystemStatsResponse(BaseModel):
    total_cases: int
    status_counts: Dict[str, int]
    issue_type_counts: Dict[str, int]
    city_counts: Dict[str, int]
    total_legal_chunks: int


class CaseDetailResponse(BaseModel):
    id: str
    case_id: Optional[str] = None
    user_text: str
    city: Optional[str] = None
    jurisdiction: Optional[str] = None
    issue_type: str
    department: str
    municipal_body: str
    status: str
    fee_amount: Optional[int] = None
    fee_json: Optional[Dict[str, Any]] = None
    submission_date: Optional[str] = None
    response_due_date: Optional[str] = None
    overdue_from: Optional[str] = None
    appeal_eligible_from: Optional[str] = None
    appeal_file_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    draft_markdown: Optional[str] = None
    appeal_markdown: Optional[str] = None
