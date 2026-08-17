# 🏛️ Civic RTI & First Appeal Drafter

> **Deterministic, local-first civic grievance to Right to Information (RTI) & First Appeal drafting engine.**
> Transforms everyday citizen grievances—potholes, garbage dumps, dark streetlights, sewage blockages, water disruptions—into legally structured, statutory RTI applications and First Appeals with deterministic municipal routing, fixed fee rules, and strict 30-day deadline countdowns under the Right to Information Act, 2005.

---

## 📌 Core Capabilities & Guarantees

1. **Zero External AI / Vector DBs (YAGNI & Determinism)**:
   - **Classification:** Pure keyword mapping across civic domains (Solid Waste, Roads/Public Works, Streetlights, Water & Sewerage, Storm Water Drainage).
   - **Routing:** Static dictionary mapping (`MCD`, `BBMP`, `PMC`, `GHMC`) with explicit Delhi Jal Board (`DJB`) routing overrides for water and sewerage issues in Delhi.
   - **Fee Math:** Rule-based fixed tables (₹10 default) with state-specific exemption rules.
   - **Deadlines:** Pure date arithmetic for 30-day response mandates under Section 7(1) and 30-day appeal windows under Section 19(1).
2. **Local BM25 Legal Grounding**:
   - Uses `rank_bm25` (BM25Okapi) over SQLite `legal_chunks` solely to attach statutory legal citations (Sections 6(1), 6(2), 6(3), 7(1), 7(6), 7(8), 19(1), 19(3), 20(1) of RTI Act 2005 & Delhi RTI Rules).
3. **Legal Safety & No Hallucinations**:
   - Explicit placeholders for unknown officers/addresses (`[APPLICANT NAME — PLACEHOLDER]`, `[OFFICE ADDRESS — PLACEHOLDER]`).
   - Mandatory statutory disclaimer: *"This is a drafting assistant and does not provide legal advice."*
4. **Complete Multi-Channel Access**:
   - ⚡ **FastAPI REST API** with interactive Swagger & ReDoc documentation.
   - 💻 **Interactive CLI Runner** (`scripts/cli.py`) for command-line power users.
   - 🎨 **6-Tab Streamlit Web Application** for a guided civic citizen experience.

---

## 🛠️ Tech Stack

- **Language:** Python 3.11+
- **Backend API:** FastAPI & Uvicorn
- **Database & ORM:** SQLite & SQLAlchemy
- **Data Validation:** Pydantic v2
- **Templating:** Jinja2
- **Information Retrieval:** `rank_bm25` (BM25Okapi)
- **Frontend UI:** Streamlit
- **Test Suite:** Pytest

---

## 📂 Project Structure

```text
civic-rti-drafter/
├── README.md
├── requirements.txt
├── pytest.ini
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers/
│   │   ├── cases.py
│   │   └── legal.py
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
│   ├── test_appeal_service.py
│   ├── test_case_service.py
│   └── test_api.py
└── scripts/
    ├── cli.py
    └── seed_demo_data.py
```

---

## 🚀 Quickstart Guide

### 1. Setup Virtual Environment & Install Dependencies

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Seed Legal Knowledge Base

Seed the SQLite database with statutory chunks from RTI Act 2005 and Delhi RTI Rules:

```bash
python -m app.rag.seed_kb
```

### 3. Run FastAPI Backend

```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 4. Run Streamlit Web Interface

```bash
streamlit run frontend/streamlit_app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### 5. CLI Tool Usage (No Browser Required)

```bash
# 1. Create a case
python scripts/cli.py create --text "Garbage dumping on main road" --city "Delhi"

# 2. Generate RTI application draft
python scripts/cli.py draft <CASE_ID> --output draft.md

# 3. Mark case as submitted
python scripts/cli.py submit <CASE_ID> --date 2026-08-20

# 4. Generate First Appeal (when overdue)
python scripts/cli.py appeal <CASE_ID> --as-of 2026-09-25 --output appeal.md

# 5. Search legal knowledge base via BM25
python scripts/cli.py search-legal "transfer to other authority"
```

### 6. Run Test Suite

```bash
pytest -v
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/cases` | Create civic grievance case with keyword classification |
| `GET` | `/cases` | List all tracked cases (filterable by `status` and `city`) |
| `GET` | `/cases/{id}` | Get full case state with draft & appeal previews |
| `PATCH` | `/cases/{id}` | Update case details or status |
| `DELETE` | `/cases/{id}` | Delete case and associated drafts/events |
| `POST` | `/cases/{id}/draft` | Generate structured RTI application draft |
| `POST` | `/cases/{id}/approve` | Mark RTI draft as approved for filing |
| `POST` | `/cases/{id}/submit` | Record submission & calculate 30-day statutory deadlines |
| `POST` | `/cases/{id}/appeal` | Generate First Appeal under Section 19(1) (overdue only) |
| `GET` | `/cases/{id}/events` | Chronological audit trail of all lifecycle events |
| `GET` | `/legal/chunks` | List all indexed statutory chunks |
| `GET` | `/legal/chunks/{id}` | Lookup specific legal chunk by ID |
| `GET` | `/legal/search` | BM25 search over RTI Act and State Rules |
| `GET` | `/stats` | System summary statistics |

---

## ⚖️ Statutory Legal Disclaimer

> *This application is an automated civic drafting assistant and does not provide formal legal advice. Officer names, designations, and public authority office addresses must be verified independently before physical or portal submission.*
