import pytest
import datetime
from app.database import Base, engine, db_context
from app.models import Case
from app.rag.seed_kb import seed_database
from app.rag.retriever import get_retriever
from app.services.deadline_service import calculate_deadline, is_overdue, calculate_first_appeal_deadline, _parse_date
from app.services.issue_service import classify_civic_issue, needs_clarification
from app.services.draft_service import generate_rti_draft
from app.services.appeal_service import generate_first_appeal
from app.services import case_service


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield


# -------------------------------------------------------------
# FAILURE POINT 1 TESTS: Multi-format & Resilient Date Parsing
# -------------------------------------------------------------
def test_date_parser_resilience():
    # Standard ISO
    assert _parse_date("2026-08-20") == datetime.date(2026, 8, 20)
    # Common Indian / European format DD-MM-YYYY
    assert _parse_date("20-08-2026") == datetime.date(2026, 8, 20)
    # Slashes format DD/MM/YYYY
    assert _parse_date("20/08/2026") == datetime.date(2026, 8, 20)
    # Slashes format YYYY/MM/DD
    assert _parse_date("2026/08/20") == datetime.date(2026, 8, 20)
    # ISO with timestamp
    assert _parse_date("2026-08-20T14:30:00Z") == datetime.date(2026, 8, 20)
    # Whitespace padded
    assert _parse_date("   2026-08-20   ") == datetime.date(2026, 8, 20)
    # Direct date object
    assert _parse_date(datetime.date(2026, 8, 20)) == datetime.date(2026, 8, 20)

    # Invalid dates raise clean ValueError
    with pytest.raises(ValueError, match="Invalid date format"):
        _parse_date("invalid-date-string")
    with pytest.raises(ValueError, match="cannot be null or empty"):
        _parse_date(None)
    with pytest.raises(ValueError, match="cannot be blank"):
        _parse_date("   ")


# -------------------------------------------------------------
# FAILURE POINT 2 TESTS: Database Transaction & Rollback Safety
# -------------------------------------------------------------
def test_db_context_manager_auto_commit_and_rollback():
    # Successful commit via context manager
    with db_context() as db:
        case, _ = case_service.create_case(db, user_text="Garbage pile near market", city="Delhi")
        case_id = case.id

    # Verify committed
    with db_context() as db:
        saved = case_service.get_case_detail(db, case_id)
        assert saved is not None
        assert saved["city"] == "Delhi"

    # Test auto rollback on exception before commit
    with pytest.raises(RuntimeError):
        with db_context() as db:
            c = db.query(Case).filter(Case.id == case_id).first()
            c.city = "CorruptedCity"
            db.flush()
            raise RuntimeError("Forced simulation error")

    # Verify rollback kept previous value
    with db_context() as db:
        reloaded = case_service.get_case_detail(db, case_id)
        assert reloaded["city"] == "Delhi"


# -------------------------------------------------------------
# FAILURE POINT 3 TESTS: Template Injection & Formatting Safety
# -------------------------------------------------------------
def test_template_injection_safety():
    # User input contains Jinja2 syntax and control characters
    malicious_input = (
        "Pothole issue on road {{ 7 * 7 }} {% if True %}broken{% endif %} \x00\x08 "
        "and <script>alert('xss')</script>"
    )
    case_dict = {
        "city": "Delhi",
        "user_text": malicious_input,
        "department": "Roads / Public Works",
        "municipal_body": "MCD",
        "issue_type": "road_maintenance",
        "submission_date": "2026-08-20",
    }
    draft = generate_rti_draft(case_dict)
    assert draft["draft_markdown"] is not None
    # Ensure Jinja variables are treated as literal strings and not executed as code
    assert "{{ 7 * 7 }}" in draft["draft_markdown"]
    assert "\x00" not in draft["draft_markdown"]


# -------------------------------------------------------------
# FAILURE POINT 4 TESTS: Unicode & Punctuation Robustness in BM25 / NLP
# -------------------------------------------------------------
def test_keyword_punctuation_and_unicode_handling():
    # Punctuation attached to keywords
    res1 = classify_civic_issue("Urgent: pothole, road-maintenance needed!")
    assert res1["issue_type"] == "road_maintenance"

    # Slashes separating keywords
    res2 = classify_civic_issue("Severe garbage/waste problem in locality")
    assert res2["issue_type"] == "solid_waste_management"

    # Multi-word priority
    res3 = classify_civic_issue("Broken street light in residential sector")
    assert res3["issue_type"] == "streetlight"
    assert res3["matched_keyword"] == "street light"

    # BM25 empty and special-character search safety
    retriever = get_retriever()
    empty_results = retriever.search("")
    assert len(empty_results) > 0  # Returns top candidates gracefully

    punct_results = retriever.search("!@#$%^&*()_+")
    assert isinstance(punct_results, list)


# -------------------------------------------------------------
# FAILURE POINT 5 TESTS: State Machine & Cascade Delete Safety
# -------------------------------------------------------------
def test_case_lifecycle_and_cascade_delete_integrity():
    with db_context() as db:
        # Create case
        case, _ = case_service.create_case(db, user_text="Water pipeline burst", city="Delhi")
        case_id = case.id

        # Generate draft
        case_service.generate_and_save_draft(db, case_id)
        # Approve
        case_service.approve_draft(db, case_id)
        # Submit with past date
        case_service.submit_case(db, case_id, submitted_on="2026-08-01")

        # Generate appeal
        case_service.generate_and_save_appeal(db, case_id, as_of="2026-09-10")

        detail = case_service.get_case_detail(db, case_id)
        assert detail["status"] == "FIRST_APPEAL_READY"
        assert detail["draft_markdown"] is not None
        assert detail["appeal_markdown"] is not None

        # Verify cascade deletion removes all linked drafts and events atomically
        success = case_service.delete_case(db, case_id)
        assert success is True

        assert case_service.get_case_detail(db, case_id) is None
        events = case_service.get_case_events(db, case_id)
        assert len(events) == 0
