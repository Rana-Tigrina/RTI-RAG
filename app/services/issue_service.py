import re
import unicodedata

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

CLARIFYING_QUESTIONS: list[str] = [
    "What is the nearest landmark or address of the issue?",
    "How long has the issue existed (approximate date first noticed)?",
]


def classify_civic_issue(user_text: str) -> dict:
    raw_text = user_text or ""
    # Normalize unicode and lowercase
    normalized = unicodedata.normalize("NFKD", raw_text).lower()
    
    # Sort keywords by length descending so multi-word keywords like "street light" match before "light"
    sorted_keywords = sorted(ISSUE_MAP.keys(), key=lambda k: len(k), reverse=True)
    
    # First pass: standard word boundary check on raw normalized text
    for kw in sorted_keywords:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, normalized):
            return {
                "issue_type": ISSUE_MAP[kw],
                "matched_keyword": kw,
            }

    # Second pass: normalize punctuation (slashes, hyphens, underscores) to spaces
    punct_cleaned = re.sub(r"[/_\-\.,;:!?\(\)\[\]]", " ", normalized)
    for kw in sorted_keywords:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, punct_cleaned):
            return {
                "issue_type": ISSUE_MAP[kw],
                "matched_keyword": kw,
            }
            
    # Third pass: direct substring fallback
    for kw in sorted_keywords:
        if kw in normalized:
            return {
                "issue_type": ISSUE_MAP[kw],
                "matched_keyword": kw,
            }

    return {
        "issue_type": DEFAULT_ISSUE_TYPE,
        "matched_keyword": None,
    }


def needs_clarification(user_text: str) -> list[str]:
    cleaned = (user_text or "").strip()
    words = [w for w in re.findall(r"\w+", cleaned) if w]
    if len(words) < 6:
        return list(CLARIFYING_QUESTIONS)
    return []
