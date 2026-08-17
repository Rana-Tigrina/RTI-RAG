import pytest
import datetime
from app.services.appeal_service import generate_first_appeal
from app.rag.seed_kb import seed_database


def test_appeal_requires_overdue_case():
    seed_database()
    case = {
        "user_text": "Broken street light",
        "department": "Electrical / Streetlight Maintenance",
        "municipal_body": "MCD",
        "submission_date": "2026-08-20",
        "response_due_date": "2026-09-19",
    }
    # Evaluated before due date -> should raise ValueError
    with pytest.raises(ValueError, match="is not overdue"):
        generate_first_appeal(case, as_of="2026-09-15")


def test_appeal_requires_submission_date():
    case = {
        "user_text": "Broken street light",
        "department": "Electrical / Streetlight Maintenance",
        "municipal_body": "MCD",
    }
    with pytest.raises(ValueError, match="has not been submitted"):
        generate_first_appeal(case)


def test_appeal_includes_sections():
    seed_database()
    case = {
        "user_text": "Potholes not repaired",
        "department": "Roads / Public Works",
        "municipal_body": "MCD",
        "submission_date": "2026-08-20",
        "response_due_date": "2026-09-19",
    }
    # Evaluated as of 2026-09-25 (6 days overdue)
    result = generate_first_appeal(case, as_of="2026-09-25")
    assert result["days_overdue"] == 6
    
    citation_ids = [c["id"] for c in result["legal_citations"]]
    assert "rti-s7-1" in citation_ids
    assert "rti-s7-6" in citation_ids
    assert "rti-s19-1" in citation_ids
    
    markdown = result["appeal_markdown"]
    assert "Section 19(1)" in markdown
    assert "Section 7(6)" in markdown
    assert "6 days have elapsed" in markdown
    assert "First Appellate Authority" in markdown
