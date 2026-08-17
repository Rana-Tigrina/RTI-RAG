import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from app.rag.seed_kb import seed_database

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield


def test_api_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Civic RTI Drafter API" in data["message"]
    assert "legal advice" in data["disclaimer"]


def test_get_stats_endpoint():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_cases" in data
    assert "status_counts" in data
    assert "total_legal_chunks" in data
    assert data["total_legal_chunks"] >= 7


def test_create_case_needs_clarification():
    payload = {
        "user_text": "Garbage near park",
        "city": "Delhi",
    }
    response = client.post("/cases", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "NEEDS_CLARIFICATION"
    assert data["issue_type"] == "solid_waste_management"
    assert data["department"] == "Solid Waste Management"
    assert data["municipal_body"] == "MCD"
    assert len(data["questions"]) > 0


def test_create_case_classified():
    payload = {
        "user_text": "There has been huge pile of garbage uncollected near the main society gate since last week",
        "city": "Delhi",
    }
    response = client.post("/cases", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ISSUE_CLASSIFIED"
    assert data["issue_type"] == "solid_waste_management"
    assert data["department"] == "Solid Waste Management"
    assert data["municipal_body"] == "MCD"
    assert len(data["questions"]) == 0


def test_draft_and_approve_lifecycle():
    # 1. Create Case
    create_res = client.post("/cases", json={
        "user_text": "Water pipeline burst and no drinking water supplied to houses in block C",
        "city": "Delhi",
    })
    assert create_res.status_code == 201
    case_id = create_res.json()["case_id"]
    assert create_res.json()["municipal_body"] == "Delhi Jal Board (DJB)"

    # 2. Generate Draft
    draft_res = client.post(f"/cases/{case_id}/draft", json={})
    assert draft_res.status_code == 200
    draft_data = draft_res.json()
    assert draft_data["status"] == "DRAFT_READY"
    assert "APPLICATION UNDER SECTION 6(1)" in draft_data["draft_markdown"]
    assert draft_data["fee"]["amount"] == 10
    assert draft_data["fee"]["citation"]["id"] == "delhi-r5-fee"

    # 3. Approve Draft
    app_res = client.post(f"/cases/{case_id}/approve")
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "USER_APPROVED"

    # 4. Submit Case
    sub_res = client.post(f"/cases/{case_id}/submit", json={"submitted_on": "2026-08-20"})
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["status"] == "SUBMITTED"
    assert sub_data["response_due_date"] == "2026-09-19"
    assert sub_data["overdue_from"] == "2026-09-20"
    assert sub_data["appeal_eligible_from"] == "2026-09-20"
    assert sub_data["appeal_file_by"] == "2026-10-19"

    # 5. Get Case Detail
    get_res = client.get(f"/cases/{case_id}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["case_id"] == case_id
    assert detail["submission_date"] == "2026-08-20"
    assert detail["draft_markdown"] is not None

    # 6. Attempt First Appeal when not overdue -> 400 Bad Request
    early_appeal_res = client.post(f"/cases/{case_id}/appeal", json={"as_of": "2026-09-10"})
    assert early_appeal_res.status_code == 400

    # 7. Generate First Appeal when overdue -> 200 OK
    overdue_appeal_res = client.post(f"/cases/{case_id}/appeal", json={"as_of": "2026-09-26"})
    assert overdue_appeal_res.status_code == 200
    appeal_data = overdue_appeal_res.json()
    assert appeal_data["status"] == "FIRST_APPEAL_READY"
    assert appeal_data["days_overdue"] == 7
    assert "Section 19(1)" in appeal_data["appeal_markdown"]
    assert "Section 7(6)" in appeal_data["appeal_markdown"]

    # 8. Check Case Event Audit Trail
    events_res = client.get(f"/cases/{case_id}/events")
    assert events_res.status_code == 200
    events = events_res.json()
    event_names = [e["event_type"] for e in events]
    assert "CASE_CREATED" in event_names
    assert "DRAFT_GENERATED" in event_names
    assert "DRAFT_APPROVED" in event_names
    assert "CASE_SUBMITTED" in event_names
    assert "APPEAL_GENERATED" in event_names

    # 9. Update Case
    patch_res = client.patch(f"/cases/{case_id}", json={"city": "Bengaluru"})
    assert patch_res.status_code == 200
    assert patch_res.json()["city"] == "Bengaluru"

    # 10. Delete Case
    del_res = client.delete(f"/cases/{case_id}")
    assert del_res.status_code == 200
    assert client.get(f"/cases/{case_id}").status_code == 404


def test_legal_knowledge_endpoints():
    # 1. List chunks
    chunks_res = client.get("/legal/chunks")
    assert chunks_res.status_code == 200
    chunks = chunks_res.json()
    assert len(chunks) >= 7

    # 2. Get specific chunk by ID
    single_res = client.get("/legal/chunks/rti-s7-1")
    assert single_res.status_code == 200
    assert single_res.json()["section"] == "Section 7(1)"

    # 3. Not found chunk
    nf_res = client.get("/legal/chunks/non-existent-id")
    assert nf_res.status_code == 404

    # 4. Search BM25
    search_res = client.get("/legal/search?q=time+limit+response+30+days")
    assert search_res.status_code == 200
    assert len(search_res.json()) > 0
    assert any(c["id"] == "rti-s7-1" for c in search_res.json())
