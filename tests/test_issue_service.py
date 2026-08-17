from app.services.issue_service import classify_civic_issue, needs_clarification


def test_garbage_maps_to_solid_waste():
    result = classify_civic_issue("Garbage not collected near park")
    assert result["issue_type"] == "solid_waste_management"
    assert result["matched_keyword"] == "garbage"


def test_pothole_maps_to_road_maintenance():
    result = classify_civic_issue("Potholes on the main road are dangerous")
    assert result["issue_type"] == "road_maintenance"
    assert result["matched_keyword"] in ("potholes", "pothole", "road")


def test_streetlight_maps_to_streetlight():
    result = classify_civic_issue("The street light in our lane is broken")
    assert result["issue_type"] == "streetlight"
    assert result["matched_keyword"] in ("street light", "streetlight")


def test_water_maps_to_water_supply():
    result = classify_civic_issue("No water in our pipeline since yesterday")
    assert result["issue_type"] == "water_supply"
    assert result["matched_keyword"] in ("water", "pipeline")


def test_unknown_issue_maps_to_general():
    result = classify_civic_issue("Something strange happened")
    assert result["issue_type"] == "general_civic_grievance"
    assert result["matched_keyword"] is None


def test_short_text_needs_clarification():
    questions = needs_clarification("Pothole near school")
    assert len(questions) > 0


def test_long_text_no_clarification():
    questions = needs_clarification("There is a massive pothole in front of St Marks School since last Monday")
    assert len(questions) == 0
