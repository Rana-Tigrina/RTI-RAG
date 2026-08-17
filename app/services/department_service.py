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


def resolve_department(issue_type: str) -> str:
    return DEPARTMENT_MAP.get(issue_type, "General Administration")


def resolve_municipal_body(city: str, issue_type: str) -> str:
    norm_city = (city or "").strip().lower()
    
    # Check Delhi overrides
    if norm_city in ("delhi", "new delhi") and issue_type in DELHI_ISSUE_BODY_OVERRIDE:
        return DELHI_ISSUE_BODY_OVERRIDE[issue_type]
        
    if norm_city in CITY_MAP:
        return CITY_MAP[norm_city]
        
    return "Municipal Corporation (verify local body)"
