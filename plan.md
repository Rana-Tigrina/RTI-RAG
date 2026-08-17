# Civic RTI Drafter — Final Claude Code Spec

Implement a deterministic, local-first MVP for a Civic RTI Drafter.

This spec is final. It uses:

- Rule-based issue classification
- Static department and municipal body mapping
- Rule-based fee calculation
- Pure date arithmetic for deadlines
- BM25 RAG only for legal citations and appeal grounding

Do not use LLMs or RAG for issue classification, fee amounts, deadline math, or department resolution.

---

## 1. Core Product Behavior

User describes a civic issue.

The app should:

1. Classify the issue using keyword mapping.
2. Ask clarifying questions if the description is too short.
3. Identify the likely department.
4. Identify the municipal body.
5. Apply Delhi-specific body overrides where needed.
6. Draft an RTI application.
7. Calculate fee using a fixed rule table.
8. Attach a legal citation for the fee using RAG, if available.
9. Calculate the 30-day response deadline after submission.
10. Track case status.
11. Generate a first appeal if the case is overdue.

---

## 2. Non-Negotiable Design Rules

### Deterministic only

Use deterministic logic for:

- Issue classification
- Department mapping
- Municipal body resolution
- Fee amount
- Deadline calculation
- First appeal deadline
- Case state transitions

### RAG only for legal grounding

Use RAG only for:

- Citing RTI Act sections
- Citing Delhi RTI fee rules
- Grounding first appeal text
- Providing legal references in drafts

### No LLM guessing

Do not use LLM or RAG to determine:

- Fee amount
- Response deadline
- Appeal deadline
- Department
- Municipal body

### Legal safety

Always include:

```text
This is a drafting assistant and does not provide legal advice.
```

Never invent:

- PIO name
- First Appellate Authority name
- Office address
- Ward number
- Penalty amount
- Fee amount unless from the fixed fee table

Use placeholders when data is unknown.

---

## 3. Tech Stack

Use:

- Python 3.11+
- FastAPI
- SQLite
- SQLAlchemy
- Pydantic
- Jinja2
- `rank_bm25`
- Streamlit
- Pytest

Do not use:

- Vector databases
- Embedding models
- Paid APIs
- External LLM calls for core functionality

The app must run fully locally.

---

## 4. Project Structure

Create this structure:

```text
civic-rti-drafter/
├── README.md
├── requirements.txt
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers/
│   │   └── cases.py
│   ├── services/
│   │   ├── issue_service.py
│   │   ├── department_service.py
│   │   ├── fee_service.py
│   │   ├── deadline_service.py
│   │   ├── draft_service.py
│   │   ├── appeal_service.py
│   │   └── case_service.py
│   ├── rag/
│   │   ├── retriever.py
│   │   └── seed_kb.py
│   └── templates/
│       ├── rti_template.md
│       └── appeal_template.md
├── kb/
│   └── data/
│       ├── rti_act_2005.jsonl
│       └── delhi_rti_rules.jsonl
├── frontend/
│   └── streamlit_app.py
├── tests/
│   ├── test_issue_service.py
│   ├── test_department_service.py
│   ├── test_fee_service.py
│   ├── test_deadline_service.py
│   ├── test_retriever.py
│   ├── test_draft_service.py
│   └── test_appeal_service.py
└── scripts/
    └── seed_demo_data.py
```

---

## 5. Issue Classification Service

File:

```text
app/services/issue_service.py
```

Use keyword mapping only.

Use this map:

```python
ISSUE_MAP: dict[str, str] = {
    "garbage": "solid_waste_management",
    "trash": "solid_waste_management",
    "waste": "solid_waste_management",
    "pothole": "road_maintenance",
    "potholes": "road_maintenance",
    "road": "road_maintenance",
    "footpath": "road_maintenance",
    "streetlight": "streetlight",
    "street light": "streetlight",
    "lamp": "streetlight",
    "drain": "storm_water_drainage",
    "drainage": "storm_water_drainage",
    "flooding": "storm_water_drainage",
    "sewage": "water_sewerage",
    "sewer": "water_sewerage",
    "manhole": "water_sewerage",
    "water": "water_supply",
    "tap": "water_supply",
    "pipeline": "water_supply",
}

DEFAULT_ISSUE_TYPE = "general_civic_grievance"

CLARIFYING_QUESTIONS = [
    "What is the nearest landmark or address of the issue?",
    "How long has the issue existed (approximate date first noticed)?",
]
```

Implement:

```python
def classify_civic_issue(user_text: str) -> dict:
    pass
```

Return:

```json
{
  "issue_type": "solid_waste_management",
  "matched_keyword": "garbage"
}
```

If no keyword matches:

```json
{
  "issue_type": "general_civic_grievance",
  "matched_keyword": null
}
```

Implement:

```python
def needs_clarification(user_text: str) -> list[str]:
    pass
```

MVP rule:

```text
If user_text has fewer than 6 words, return CLARIFYING_QUESTIONS.
Otherwise return empty list.
```

Do not use RAG here.

---

## 6. Department and Municipal Body Service

File:

```text
app/services/department_service.py
```

Use static mapping only.

Use:

```python
DEPARTMENT_MAP: dict[str, str] = {
    "solid_waste_management": "Solid Waste Management",
    "road_maintenance": "Roads / Public Works",
    "streetlight": "Electrical / Streetlight Maintenance",
    "storm_water_drainage": "Storm Water Drainage",
    "water_sewerage": "Water and Sewerage",
    "water_supply": "Water Supply",
    "general_civic_grievance": "General Administration",
}

CITY_MAP: dict[str, str] = {
    "bengaluru": "BBMP",
    "bangalore": "BBMP",
    "delhi": "MCD",
    "new delhi": "MCD",
    "pune": "PMC",
    "hyderabad": "GHMC",
}

DELHI_ISSUE_BODY_OVERRIDE: dict[str, str] = {
    "water_supply": "Delhi Jal Board (DJB)",
    "water_sewerage": "Delhi Jal Board (DJB)",
}
```

Implement:

```python
def resolve_department(issue_type: str) -> str:
    pass
```

If unknown issue type, return:

```text
General Administration
```

Implement:

```python
def resolve_municipal_body(city: str, issue_type: str) -> str:
    pass
```

Rules:

1. Normalize city using `.strip().lower()`.
2. Use `CITY_MAP`.
3. If city is Delhi or New Delhi and issue type is in `DELHI_ISSUE_BODY_OVERRIDE`, return the override.
4. If city is unknown, return:

```text
Municipal Corporation (verify local body)
```

Examples:

```text
Delhi + water_supply -> Delhi Jal Board (DJB)
Delhi + garbage -> MCD
Bengaluru + water_supply -> BBMP
Unknown city -> Municipal Corporation (verify local body)
```

Do not use RAG here.

---

## 7. Fee Service

File:

```text
app/services/fee_service.py
```

Fee amount must be rule-based.

Use:

```python
DEFAULT_FEE = {
    "amount": 10,
    "currency": "INR",
    "notes": "Fee may vary by state. Verify current rules.",
}

CITY_FEE_OVERRIDES: dict[str, dict] = {
    "delhi": {
        "amount": 10,
        "currency": "INR",
        "notes": (
            "Rs. 10 application fee under Delhi RTI Rules. "
            "BPL applicants are exempt on production of a valid BPL card. "
            "Further fee, such as photocopying, may apply separately. "
            "Verify current rules before relying on this."
        ),
    },
}
```

Implement:

```python
def calculate_fee(city: str) -> dict:
    pass
```

Return:

```json
{
  "amount": 10,
  "currency": "INR",
  "notes": "...",
  "citation": null
}
```

For Delhi, attach a citation only if the legal retriever has chunk:

```text
delhi-r5-fee
```

Citation format:

```json
{
  "id": "delhi-r5-fee",
  "source": "Delhi RTI Rules",
  "section": "Fee Rules",
  "title": "Delhi RTI application fee"
}
```

Important:

```text
The fee amount must never come from RAG.
RAG may only provide the citation.
```

---

## 8. Deadline Service

File:

```text
app/services/deadline_service.py
```

Use pure date arithmetic.

Constants:

```python
RESPONSE_WINDOW_DAYS = 30
FIRST_APPEAL_WINDOW_DAYS = 30
```

Implement:

```python
def calculate_deadline(submitted_on: str | date) -> dict:
    pass
```

Return:

```json
{
  "submitted_on": "2026-08-20",
  "response_due_date": "2026-09-19",
  "overdue_from": "2026-09-20"
}
```

Implement:

```python
def is_overdue(response_due_date: str | date, as_of: date | None = None) -> bool:
    pass
```

Implement:

```python
def calculate_first_appeal_deadline(response_due_date: str | date) -> dict:
    pass
```

Return:

```json
{
  "appeal_eligible_from": "2026-09-20",
  "appeal_file_by": "2026-10-19"
}
```

Do not use RAG here.

---

## 9. Legal RAG Service

File:

```text
app/rag/retriever.py
```

Use BM25 via `rank_bm25`.

Use SQLite as storage.

Do not use embeddings.

Create a retriever class:

```python
class LegalRetriever:
    def get_by_id(self, chunk_id: str):
        pass

    def search(
        self,
        query: str,
        jurisdiction: str | None = None,
        topic: str | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        pass
```

Also implement:

```python
def get_retriever() -> LegalRetriever:
    pass
```

Use a singleton retriever.

---

## 10. Legal Knowledge Base Schema

SQLite table:

```text
legal_chunks
```

Fields:

```text
id TEXT PRIMARY KEY
jurisdiction TEXT
act TEXT
section TEXT
topic TEXT
title TEXT
text TEXT
source TEXT
updated_at TEXT
```

Allowed jurisdictions:

```text
india
delhi
```

Allowed topics include:

```text
request
transfer
deadline
free_if_delay
appeal
fee
water
```

---

## 11. Required Seed Chunks

Seed at least these chunks.

```json
{
  "id": "rti-s6-1",
  "jurisdiction": "india",
  "act": "RTI Act 2005",
  "section": "Section 6(1)",
  "topic": "request",
  "title": "Right to request information",
  "text": "A citizen has the right to request information from a public authority under the Right to Information Act, 2005.",
  "source": "RTI Act 2005"
}
```

```json
{
  "id": "rti-s6-3",
  "jurisdiction": "india",
  "act": "RTI Act 2005",
  "section": "Section 6(3)",
  "topic": "transfer",
  "title": "Transfer of RTI application",
  "text": "If an RTI application relates to another public authority, the Public Information Officer may transfer it to the concerned public authority.",
  "source": "RTI Act 2005"
}
```

```json
{
  "id": "rti-s7-1",
  "jurisdiction": "india",
  "act": "RTI Act 2005",
  "section": "Section 7(1)",
  "topic": "deadline",
  "title": "Time limit for RTI response",
  "text": "The Public Information Officer must provide the information within 30 days of receiving the request, subject to the provisions of the Act.",
  "source": "RTI Act 2005"
}
```

```json
{
  "id": "rti-s7-6",
  "jurisdiction": "india",
  "act": "RTI Act 2005",
  "section": "Section 7(6)",
  "topic": "free_if_delay",
  "title": "Information free after delay",
  "text": "If the public authority fails to provide information within the prescribed time, the information may be provided free of charge.",
  "source": "RTI Act 2005"
}
```

```json
{
  "id": "rti-s19-1",
  "jurisdiction": "india",
  "act": "RTI Act 2005",
  "section": "Section 19(1)",
  "topic": "appeal",
  "title": "First appeal",
  "text": "A citizen may file a first appeal if information is denied, not provided, or not provided within the prescribed time.",
  "source": "RTI Act 2005"
}
```

```json
{
  "id": "delhi-r5-fee",
  "jurisdiction": "delhi",
  "act": "Delhi RTI Rules",
  "section": "Fee Rules",
  "topic": "fee",
  "title": "Delhi RTI application fee",
  "text": "Delhi RTI Rules provide for an application fee and exemptions. BPL applicants may be exempt on production of valid proof. Further copying charges may apply separately. Verify current rules before filing.",
  "source": "Delhi RTI Rules"
}
```

```json
{
  "id": "delhi-djb-water",
  "jurisdiction": "delhi",
  "act": "Delhi Public Authority Directory",
  "section": "Water and Sewerage",
  "topic": "water",
  "title": "Delhi Jal Board responsibility",
  "text": "In Delhi, water supply and sewerage matters are commonly handled by Delhi Jal Board rather than the municipal corporation.",
  "source": "Delhi public authority directory"
}
```

The fee service must be able to call:

```python
get_retriever().get_by_id("delhi-r5-fee")
```

---

## 12. RTI Draft Generator

File:

```text
app/services/draft_service.py
```

Implement:

```python
def generate_rti_draft(case: dict, submitted_on: str | None = None) -> dict:
    pass
```

The draft generator must:

1. Use deterministic case data.
2. Use the fee service for fee amount.
3. Use RAG only for legal citations.
4. Use Jinja2 template.
5. Return draft markdown and citations.

Return:

```json
{
  "draft_markdown": "...",
  "fee": {
    "amount": 10,
    "currency": "INR",
    "notes": "...",
    "citation": {
      "id": "delhi-r5-fee",
      "source": "Delhi RTI Rules",
      "section": "Fee Rules",
      "title": "Delhi RTI application fee"
    }
  },
  "legal_citations": [
    {
      "id": "rti-s6-1",
      "source": "RTI Act 2005",
      "section": "Section 6(1)",
      "title": "Right to request information"
    },
    {
      "id": "rti-s6-3",
      "source": "RTI Act 2005",
      "section": "Section 6(3)",
      "title": "Transfer of RTI application"
    },
    {
      "id": "rti-s7-1",
      "source": "RTI Act 2005",
      "section": "Section 7(1)",
      "title": "Time limit for RTI response"
    }
  ]
}
```

The RTI draft should include:

- Applicant name placeholder
- Applicant address placeholder
- Department
- Municipal body
- Subject
- Issue description
- Requested information list
- Fee note
- 30-day response note
- Signature placeholder
- Disclaimer

Requested information list must include:

```text
1. Please provide the name and designation of the officer responsible for this issue.
2. Please provide the current status of action taken.
3. Please provide the expected timeline for resolution.
4. If this matter belongs to another department or public authority, please transfer this application under Section 6(3) of the RTI Act, 2005.
```

If exact submission date is not known, do not calculate a specific deadline.

Use:

```text
Response is due within 30 days from submission under Section 7(1).
```

---

## 13. First Appeal Generator

File:

```text
app/services/appeal_service.py
```

Implement:

```python
def generate_first_appeal(case: dict, as_of: date | None = None) -> dict:
    pass
```

Only allow appeal generation if:

```text
case is submitted
and current/as_of date is after response_due_date
```

If not overdue, raise a validation error.

Calculate:

```text
days_overdue = as_of - response_due_date
```

Use RAG to retrieve citations for:

- Section 7(1)
- Section 7(6)
- Section 19(1)

Use the appeal template.

Template variables:

```text
department
municipal_body
applicant_name_placeholder
submission_date
user_text
days_overdue
response_due_date
signature_placeholder
draft_date
citations
```

Appeal draft must include:

- First Appellate Authority placeholder
- Subject referencing Section 19(1)
- Original RTI submission date
- Issue description
- Overdue statement
- Request for information
- Request for free information under Section 7(6)
- Placeholder for applicant details
- Legal citations
- Disclaimer

Do not invent:

- First Appellate Authority name
- Office address
- Penalty amount

---

## 14. Appeal Template

Use this template style:

```jinja
To,
The First Appellate Authority,
{{ department }},
{{ municipal_body }}
[OFFICE ADDRESS — PLACEHOLDER, please verify before submission.]

**Subject:** First Appeal under Section 19(1) of the Right to Information Act, 2005

Respected Sir/Madam,

I, {{ applicant_name_placeholder }}, had filed an RTI application dated {{ submission_date }} with the Public Information Officer, {{ department }}, {{ municipal_body }}, seeking information regarding the following issue:

**Issue described:** {{ user_text }}

As of the date of this appeal, {{ days_overdue }} days have elapsed since the statutory response deadline of {{ response_due_date }} under Section 7(1) of the RTI Act, 2005, and no response has been received.

I therefore file this First Appeal under Section 19(1) of the RTI Act, 2005, and request that:

1. The Public Information Officer be directed to furnish the information requested without further delay.
2. Given the delay beyond the statutory 30-day period, the information be provided free of charge, as contemplated under Section 7(6) of the Act.
3. Appropriate action be considered against the Public Information Officer for non-compliance with statutory timelines, if deemed fit.

I have enclosed a copy of my original RTI application and proof of submission dated {{ submission_date }}.

Yours faithfully,

{{ signature_placeholder }}
Name: [APPLICANT NAME — PLACEHOLDER]
Address: [APPLICANT ADDRESS — PLACEHOLDER]
Phone/Email: [CONTACT DETAILS — PLACEHOLDER]
Date: {{ draft_date }}

---
{% if citations %}
**Legal references used in this appeal:**
{% for c in citations %}
- {{ c.source }}, {{ c.section }} — {{ c.title }}
{% endfor %}
{% endif %}

*Disclaimer: This is a drafting assistant and does not provide legal advice. The identity and office address of the First Appellate Authority must be verified before submission.*
```

---

## 15. Database Models

Use SQLAlchemy models.

### Case

Fields:

```text
id TEXT PRIMARY KEY
user_text TEXT
city TEXT
jurisdiction TEXT
issue_type TEXT
department TEXT
municipal_body TEXT
status TEXT
fee_amount INTEGER
fee_json JSON
submission_date TEXT
response_due_date TEXT
overdue_from TEXT
appeal_eligible_from TEXT
appeal_file_by TEXT
created_at TEXT
updated_at TEXT
```

### RTIDraft

Fields:

```text
id TEXT PRIMARY KEY
case_id TEXT
draft_markdown TEXT
legal_citations_json JSON
created_at TEXT
```

### AppealDraft

Fields:

```text
id TEXT PRIMARY KEY
case_id TEXT
appeal_markdown TEXT
legal_citations_json JSON
created_at TEXT
```

### CaseEvent

Fields:

```text
id TEXT PRIMARY KEY
case_id TEXT
event_type TEXT
payload JSON
created_at TEXT
```

### LegalChunk

Fields:

```text
id TEXT PRIMARY KEY
jurisdiction TEXT
act TEXT
section TEXT
topic TEXT
title TEXT
text TEXT
source TEXT
updated_at TEXT
```

---

## 16. Case States

Use:

```text
INTAKE_STARTED
NEEDS_CLARIFICATION
ISSUE_CLASSIFIED
DEPARTMENT_MATCHED
DRAFT_READY
USER_APPROVED
SUBMITTED
AWAITING_RESPONSE
OVERDUE
FIRST_APPEAL_READY
CLOSED
```

Simple transition rules:

```text
Create case:
  if needs_clarification -> NEEDS_CLARIFICATION
  else -> ISSUE_CLASSIFIED

Generate draft:
  -> DRAFT_READY

Approve draft:
  -> USER_APPROVED

Submit:
  -> SUBMITTED

After submission:
  -> AWAITING_RESPONSE

If current date > response_due_date:
  -> OVERDUE

Generate appeal:
  -> FIRST_APPEAL_READY
```

---

## 17. API Endpoints

### Create Case

```text
POST /cases
```

Request:

```json
{
  "user_text": "Garbage not collected near park",
  "city": "Delhi"
}
```

Response:

```json
{
  "case_id": "case-id",
  "status": "NEEDS_CLARIFICATION",
  "issue_type": "solid_waste_management",
  "department": "Solid Waste Management",
  "municipal_body": "MCD",
  "questions": [
    "What is the nearest landmark or address of the issue?",
    "How long has the issue existed (approximate date first noticed)?"
  ]
}
```

If no clarification is needed:

```json
{
  "case_id": "case-id",
  "status": "ISSUE_CLASSIFIED",
  "issue_type": "solid_waste_management",
  "department": "Solid Waste Management",
  "municipal_body": "MCD",
  "questions": []
}
```

---

### Generate Draft

```text
POST /cases/{case_id}/draft
```

Optional body:

```json
{
  "submitted_on": "2026-08-20"
}
```

If `submitted_on` is not provided, do not calculate exact deadline.

Response:

```json
{
  "case_id": "case-id",
  "status": "DRAFT_READY",
  "draft_markdown": "...",
  "fee": {
    "amount": 10,
    "currency": "INR",
    "notes": "...",
    "citation": {
      "id": "delhi-r5-fee",
      "source": "Delhi RTI Rules",
      "section": "Fee Rules",
      "title": "Delhi RTI application fee"
    }
  },
  "legal_citations": [
    {
      "id": "rti-s6-1",
      "source": "RTI Act 2005",
      "section": "Section 6(1)",
      "title": "Right to request information"
    }
  ]
}
```

---

### Approve Draft

```text
POST /cases/{case_id}/approve
```

Response:

```json
{
  "case_id": "case-id",
  "status": "USER_APPROVED"
}
```

---

### Submit Case

```text
POST /cases/{case_id}/submit
```

Request:

```json
{
  "submitted_on": "2026-08-20"
}
```

Response:

```json
{
  "case_id": "case-id",
  "status": "SUBMITTED",
  "submitted_on": "2026-08-20",
  "response_due_date": "2026-09-19",
  "overdue_from": "2026-09-20",
  "appeal_eligible_from": "2026-09-20",
  "appeal_file_by": "2026-10-19"
}
```

---

### Get Case

```text
GET /cases/{case_id}
```

Return full case state.

---

### Generate First Appeal

```text
POST /cases/{case_id}/appeal
```

Optional body:

```json
{
  "as_of": "2026-09-25"
}
```

If case is not overdue, return validation error.

Response:

```json
{
  "case_id": "case-id",
  "status": "FIRST_APPEAL_READY",
  "appeal_markdown": "...",
  "days_overdue": 6,
  "legal_citations": [
    {
      "id": "rti-s7-1",
      "source": "RTI Act 2005",
      "section": "Section 7(1)",
      "title": "Time limit for RTI response"
    },
    {
      "id": "rti-s7-6",
      "source": "RTI Act 2005",
      "section": "Section 7(6)",
      "title": "Information free after delay"
    },
    {
      "id": "rti-s19-1",
      "source": "RTI Act 2005",
      "section": "Section 19(1)",
      "title": "First appeal"
    }
  ]
}
```

---

## 18. Frontend

Build a simple Streamlit app.

Pages:

### Home

Inputs:

- User text
- City

Buttons:

- Create Case

Display:

- Case ID
- Status
- Issue type
- Department
- Municipal body
- Clarifying questions

### Draft

Buttons:

- Generate Draft
- Approve Draft

Display:

- Draft markdown
- Fee
- Fee citation
- Legal citations

### Submission

Inputs:

- Submission date

Buttons:

- Mark Submitted

Display:

- Response due date
- Overdue from date
- Appeal eligible from
- Appeal file by

### Appeal

Buttons:

- Generate First Appeal

Display:

- Appeal markdown
- Days overdue
- Appeal citations

### Cases List

Display:

- Case ID
- City
- Issue type
- Department
- Municipal body
- Status
- Response due date

---

## 19. Required Tests

### Issue classification

```python
def test_garbage_maps_to_solid_waste():
    result = classify_civic_issue("Garbage not collected near park")
    assert result["issue_type"] == "solid_waste_management"
    assert result["matched_keyword"] == "garbage"
```

```python
def test_unknown_issue_maps_to_general():
    result = classify_civic_issue("Something strange happened")
    assert result["issue_type"] == "general_civic_grievance"
```

```python
def test_short_text_needs_clarification():
    questions = needs_clarification("Pothole near school")
    assert len(questions) > 0
```

---

### Department and municipal body

```python
def test_delhi_water_goes_to_djb():
    body = resolve_municipal_body("Delhi", "water_supply")
    assert body == "Delhi Jal Board (DJB)"
```

```python
def test_delhi_garbage_goes_to_mcd():
    body = resolve_municipal_body("Delhi", "solid_waste_management")
    assert body == "MCD"
```

```python
def test_bengaluru_water_goes_to_bbmp():
    body = resolve_municipal_body("Bengaluru", "water_supply")
    assert body == "BBMP"
```

```python
def test_unknown_city_uses_placeholder():
    body = resolve_municipal_body("Atlantis", "water_supply")
    assert body == "Municipal Corporation (verify local body)"
```

---

### Fee

```python
def test_default_fee_amount():
    fee = calculate_fee("Unknown City")
    assert fee["amount"] == 10
    assert fee["currency"] == "INR"
```

```python
def test_delhi_fee_has_citation_when_available():
    fee = calculate_fee("Delhi")
    assert fee["amount"] == 10
    if fee["citation"] is not None:
        assert fee["citation"]["id"] == "delhi-r5-fee"
```

---

### Deadline

```python
def test_deadline_is_30_days():
    result = calculate_deadline("2026-08-20")
    assert result["response_due_date"] == "2026-09-19"
    assert result["overdue_from"] == "2026-09-20"
```

```python
def test_first_appeal_deadline():
    result = calculate_first_appeal_deadline("2026-09-19")
    assert result["appeal_eligible_from"] == "2026-09-20"
    assert result["appeal_file_by"] == "2026-10-19"
```

---

### RAG retriever

```python
def test_get_delhi_fee_chunk():
    retriever = get_retriever()
    chunk = retriever.get_by_id("delhi-r5-fee")
    assert chunk is not None
    assert chunk["section"] == "Fee Rules"
```

```python
def test_search_appeal_sections():
    retriever = get_retriever()
    results = retriever.search("first appeal delayed RTI", topic="appeal")
    assert any(result["id"] == "rti-s19-1" for result in results)
```

---

### Appeal

```python
def test_appeal_requires_overdue_case():
    # submitted case with due date in future should raise error
    pass
```

```python
def test_appeal_includes_sections():
    # overdue case should generate appeal containing Section 19(1) and Section 7(6)
    pass
```

---

## 20. README Requirements

README must include:

1. Project overview
2. Setup instructions
3. How to seed legal KB
4. How to run API
5. How to run Streamlit app
6. How to run tests
7. Example API requests
8. Disclaimer

Run commands:

```bash
pip install -r requirements.txt
python -m app.rag.seed_kb
uvicorn app.main:app --reload
streamlit run frontend/streamlit_app.py
pytest
```

---

## 21. Definition of Done

The MVP is complete when:

1. API runs locally.
2. Streamlit app runs locally.
3. Issue classification is keyword-based.
4. Department mapping is deterministic.
5. Delhi water/sewerage routes to Delhi Jal Board.
6. Fee amount is rule-based.
7. Delhi fee citation can be retrieved by ID.
8. Deadline calculation is pure date arithmetic.
9. First appeal deadline is calculated.
10. RTI draft includes legal citations.
11. First appeal draft is generated only for overdue cases.
12. First appeal includes Section 19(1), Section 7(1), and Section 7(6) citations.
13. No LLM is required.
14. No vector DB is required.
15. Tests pass.
16. README is complete.