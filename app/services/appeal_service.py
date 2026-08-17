import datetime
import re
from pathlib import Path
from typing import Union
from jinja2 import Template
from app.services.deadline_service import _parse_date, is_overdue
from app.rag.retriever import get_retriever


def _sanitize_text(text: str) -> str:
    """Sanitize user input text to prevent control characters and formatting corruption."""
    if not text:
        return ""
    clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    clean = clean.replace("\r\n", "\n").replace("\r", "\n").strip()
    return clean


def _load_template() -> Template:
    template_path = Path(__file__).resolve().parent.parent / "templates" / "appeal_template.md"
    with open(template_path, "r", encoding="utf-8") as f:
        return Template(f.read())


def generate_first_appeal(case: dict, as_of: Union[str, datetime.date, None] = None) -> dict:
    submission_date_str = case.get("submission_date")
    response_due_date_str = case.get("response_due_date")

    if not submission_date_str or not response_due_date_str:
        raise ValueError("Case has not been submitted yet or lacks statutory response due date.")

    due_date = _parse_date(response_due_date_str)
    
    if as_of is None:
        as_of_date = datetime.date.today()
    else:
        as_of_date = _parse_date(as_of)

    if not is_overdue(due_date, as_of=as_of_date):
        raise ValueError(
            f"Case is not overdue. Statutory response deadline is {due_date.isoformat()}, "
            f"evaluated as of {as_of_date.isoformat()}."
        )

    days_overdue = (as_of_date - due_date).days

    retriever = get_retriever()
    required_ids = ["rti-s7-1", "rti-s7-6", "rti-s19-1"]
    citations = []

    for cid in required_ids:
        chunk = retriever.get_by_id(cid)
        if chunk:
            citations.append({
                "id": chunk["id"],
                "source": chunk.get("source", "RTI Act 2005"),
                "section": chunk.get("section", ""),
                "title": chunk.get("title", ""),
            })
        else:
            defaults = {
                "rti-s7-1": {"source": "RTI Act 2005", "section": "Section 7(1)", "title": "Time limit for RTI response"},
                "rti-s7-6": {"source": "RTI Act 2005", "section": "Section 7(6)", "title": "Information free after delay"},
                "rti-s19-1": {"source": "RTI Act 2005", "section": "Section 19(1)", "title": "First appeal"},
            }
            if cid in defaults:
                citations.append({
                    "id": cid,
                    "source": defaults[cid]["source"],
                    "section": defaults[cid]["section"],
                    "title": defaults[cid]["title"],
                })

    sanitized_user_text = _sanitize_text(case.get("user_text", ""))

    template = _load_template()
    appeal_markdown = template.render(
        department=case.get("department", "General Administration"),
        municipal_body=case.get("municipal_body", "Municipal Corporation (verify local body)"),
        applicant_name_placeholder="[APPLICANT NAME — PLACEHOLDER]",
        submission_date=submission_date_str,
        user_text=sanitized_user_text,
        days_overdue=days_overdue,
        response_due_date=response_due_date_str,
        signature_placeholder="[SIGNATURE / APPLICANT SIGN]",
        draft_date=as_of_date.isoformat(),
        citations=citations,
    )

    return {
        "appeal_markdown": appeal_markdown,
        "days_overdue": days_overdue,
        "legal_citations": citations,
    }
