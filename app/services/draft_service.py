import datetime
import re
from pathlib import Path
from jinja2 import Template
from app.services.fee_service import calculate_fee
from app.services.deadline_service import calculate_deadline
from app.rag.retriever import get_retriever


def _sanitize_text(text: str) -> str:
    """Sanitize user input text to prevent control characters and formatting corruption."""
    if not text:
        return ""
    # Remove null bytes and non-printable control characters (except newline, tab)
    clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Normalize newlines
    clean = clean.replace("\r\n", "\n").replace("\r", "\n").strip()
    return clean


def _load_template() -> Template:
    template_path = Path(__file__).resolve().parent.parent / "templates" / "rti_template.md"
    with open(template_path, "r", encoding="utf-8") as f:
        return Template(f.read())


def generate_rti_draft(case: dict, submitted_on: str | None = None) -> dict:
    city = _sanitize_text(case.get("city") or "Local Area")
    fee = calculate_fee(city)
    
    retriever = get_retriever()
    required_ids = ["rti-s6-1", "rti-s6-3", "rti-s7-1"]
    legal_citations = []
    
    for cid in required_ids:
        chunk = retriever.get_by_id(cid)
        if chunk:
            legal_citations.append({
                "id": chunk["id"],
                "source": chunk.get("source", "RTI Act 2005"),
                "section": chunk.get("section", ""),
                "title": chunk.get("title", ""),
            })
        else:
            defaults = {
                "rti-s6-1": {"source": "RTI Act 2005", "section": "Section 6(1)", "title": "Right to request information"},
                "rti-s6-3": {"source": "RTI Act 2005", "section": "Section 6(3)", "title": "Transfer of RTI application"},
                "rti-s7-1": {"source": "RTI Act 2005", "section": "Section 7(1)", "title": "Time limit for RTI response"},
            }
            if cid in defaults:
                legal_citations.append({
                    "id": cid,
                    "source": defaults[cid]["source"],
                    "section": defaults[cid]["section"],
                    "title": defaults[cid]["title"],
                })

    effective_submission = submitted_on or case.get("submission_date")
    if effective_submission:
        deadline_info = calculate_deadline(effective_submission)
        response_notice = (
            f"Submitted on {effective_submission}. Statutory response deadline is "
            f"{deadline_info['response_due_date']} under Section 7(1) of the RTI Act, 2005."
        )
    else:
        response_notice = "Response is due within 30 days from submission under Section 7(1)."

    sanitized_user_text = _sanitize_text(case.get("user_text", ""))

    template = _load_template()
    draft_markdown = template.render(
        department=case.get("department", "General Administration"),
        municipal_body=case.get("municipal_body", "Municipal Corporation (verify local body)"),
        issue_type_display=(case.get("issue_type", "civic issue")).replace("_", " ").title(),
        city=city,
        user_text=sanitized_user_text,
        fee=fee,
        response_notice=response_notice,
        applicant_name_placeholder="[APPLICANT NAME — PLACEHOLDER]",
        signature_placeholder="[SIGNATURE / APPLICANT SIGN]",
        draft_date=datetime.date.today().isoformat(),
        legal_citations=legal_citations,
    )

    return {
        "draft_markdown": draft_markdown,
        "fee": fee,
        "legal_citations": legal_citations,
    }
