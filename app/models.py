import datetime
from sqlalchemy import Column, String, Integer, Text, JSON
from app.database import Base


def utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, index=True)
    user_text = Column(Text, nullable=False)
    city = Column(String, nullable=True)
    jurisdiction = Column(String, nullable=True)
    issue_type = Column(String, nullable=False)
    department = Column(String, nullable=False)
    municipal_body = Column(String, nullable=False)
    status = Column(String, nullable=False)
    fee_amount = Column(Integer, nullable=True)
    fee_json = Column(JSON, nullable=True)
    submission_date = Column(String, nullable=True)
    response_due_date = Column(String, nullable=True)
    overdue_from = Column(String, nullable=True)
    appeal_eligible_from = Column(String, nullable=True)
    appeal_file_by = Column(String, nullable=True)
    created_at = Column(String, default=utc_now_iso)
    updated_at = Column(String, default=utc_now_iso, onupdate=utc_now_iso)


class RTIDraft(Base):
    __tablename__ = "rti_drafts"

    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, index=True, nullable=False)
    draft_markdown = Column(Text, nullable=False)
    legal_citations_json = Column(JSON, nullable=True)
    created_at = Column(String, default=utc_now_iso)


class AppealDraft(Base):
    __tablename__ = "appeal_drafts"

    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, index=True, nullable=False)
    appeal_markdown = Column(Text, nullable=False)
    legal_citations_json = Column(JSON, nullable=True)
    created_at = Column(String, default=utc_now_iso)


class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, index=True, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(String, default=utc_now_iso)


class LegalChunk(Base):
    __tablename__ = "legal_chunks"

    id = Column(String, primary_key=True, index=True)
    jurisdiction = Column(String, nullable=False)
    act = Column(String, nullable=False)
    section = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    title = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    source = Column(String, nullable=False)
    updated_at = Column(String, default=utc_now_iso)
