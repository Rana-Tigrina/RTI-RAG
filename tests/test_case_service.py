import pytest
import datetime
from app.database import SessionLocal, Base, engine
from app.models import Case, CaseEvent
from app.rag.seed_kb import seed_database
from app.services import case_service


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield


def test_case_service_lifecycle_full():
    db = SessionLocal()
    try:
        # 1. Create case
        case, questions = case_service.create_case(
            db,
            user_text="Broken sewage pipe leaking foul water onto street",
            city="Delhi",
        )
        assert case.id is not None
        assert case.issue_type == "water_sewerage"
        assert case.municipal_body == "Delhi Jal Board (DJB)"
        assert case.department == "Water and Sewerage"
        assert case.status == "ISSUE_CLASSIFIED"
        assert len(questions) == 0

        # 2. Generate Draft
        case, draft_res = case_service.generate_and_save_draft(db, case.id)
        assert case.status == "DRAFT_READY"
        assert "APPLICATION UNDER SECTION 6(1)" in draft_res["draft_markdown"]
        assert draft_res["fee"]["amount"] == 10

        # 3. Approve Draft
        case = case_service.approve_draft(db, case.id)
        assert case.status == "USER_APPROVED"

        # 4. Submit Case
        past_date = (datetime.date.today() - datetime.timedelta(days=35)).isoformat()
        case = case_service.submit_case(db, case.id, submitted_on=past_date)
        assert case.status == "SUBMITTED"
        assert case.submission_date == past_date
        assert case.response_due_date is not None

        # 5. Detail check - auto transition to OVERDUE
        detail = case_service.get_case_detail(db, case.id)
        assert detail["status"] == "OVERDUE"
        assert detail["draft_markdown"] is not None

        # 6. Generate Appeal
        case, appeal_res = case_service.generate_and_save_appeal(
            db, case.id, as_of=datetime.date.today().isoformat()
        )
        assert case.status == "FIRST_APPEAL_READY"
        assert appeal_res["days_overdue"] == 5
        assert "Section 19(1)" in appeal_res["appeal_markdown"]

        # 7. Check Case Events recorded
        events = db.query(CaseEvent).filter(CaseEvent.case_id == case.id).all()
        event_types = [e.event_type for e in events]
        assert "CASE_CREATED" in event_types
        assert "DRAFT_GENERATED" in event_types
        assert "DRAFT_APPROVED" in event_types
        assert "CASE_SUBMITTED" in event_types
        assert "APPEAL_GENERATED" in event_types

    finally:
        db.close()


def test_case_service_not_found_errors():
    db = SessionLocal()
    try:
        fake_id = "non-existent-case-id"

        with pytest.raises(ValueError, match="not found"):
            case_service.generate_and_save_draft(db, fake_id)

        with pytest.raises(ValueError, match="not found"):
            case_service.approve_draft(db, fake_id)

        with pytest.raises(ValueError, match="not found"):
            case_service.submit_case(db, fake_id, submitted_on="2026-08-20")

        with pytest.raises(ValueError, match="not found"):
            case_service.generate_and_save_appeal(db, fake_id)

        assert case_service.get_case_detail(db, fake_id) is None
    finally:
        db.close()


def test_list_cases_with_overdue_transition():
    db = SessionLocal()
    try:
        case, _ = case_service.create_case(
            db,
            user_text="Overdue test street light repair",
            city="Hyderabad",
        )
        past_date = (datetime.date.today() - datetime.timedelta(days=40)).isoformat()
        case_service.submit_case(db, case.id, submitted_on=past_date)

        all_cases = case_service.list_cases(db)
        matching = [c for c in all_cases if c["id"] == case.id]
        assert len(matching) == 1
        assert matching[0]["status"] == "OVERDUE"
    finally:
        db.close()
