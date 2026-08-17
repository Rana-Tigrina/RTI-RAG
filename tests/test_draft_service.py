from app.services.draft_service import generate_rti_draft
from app.rag.seed_kb import seed_database


def test_generate_rti_draft_structure():
    seed_database()
    case = {
        "user_text": "Garbage dumping on roadside near community hall",
        "city": "Delhi",
        "issue_type": "solid_waste_management",
        "department": "Solid Waste Management",
        "municipal_body": "MCD",
    }
    result = generate_rti_draft(case)
    
    assert "draft_markdown" in result
    assert "fee" in result
    assert "legal_citations" in result
    
    assert result["fee"]["amount"] == 10
    assert result["fee"]["currency"] == "INR"
    assert result["fee"]["citation"]["id"] == "delhi-r5-fee"
    
    markdown = result["draft_markdown"]
    assert "APPLICATION UNDER SECTION 6(1)" in markdown
    assert "Solid Waste Management" in markdown
    assert "MCD" in markdown
    assert "Section 6(3)" in markdown
    assert "Disclaimer" in markdown


def test_draft_includes_legal_citations():
    seed_database()
    case = {
        "user_text": "Potholes on road",
        "city": "Bengaluru",
        "issue_type": "road_maintenance",
        "department": "Roads / Public Works",
        "municipal_body": "BBMP",
    }
    result = generate_rti_draft(case)
    citation_ids = [c["id"] for c in result["legal_citations"]]
    assert "rti-s6-1" in citation_ids
    assert "rti-s6-3" in citation_ids
    assert "rti-s7-1" in citation_ids
