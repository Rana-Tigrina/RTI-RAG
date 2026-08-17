from app.rag.retriever import get_retriever

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


def calculate_fee(city: str) -> dict:
    norm_city = (city or "").strip().lower()
    fee_data = CITY_FEE_OVERRIDES.get(norm_city, DEFAULT_FEE).copy()
    
    citation = None
    if norm_city in ("delhi", "new delhi"):
        retriever = get_retriever()
        chunk = retriever.get_by_id("delhi-r5-fee")
        if chunk:
            citation = {
                "id": chunk["id"],
                "source": chunk.get("source", "Delhi RTI Rules"),
                "section": chunk.get("section", "Fee Rules"),
                "title": chunk.get("title", "Delhi RTI application fee"),
            }

    return {
        "amount": fee_data["amount"],
        "currency": fee_data["currency"],
        "notes": fee_data["notes"],
        "citation": citation,
    }
