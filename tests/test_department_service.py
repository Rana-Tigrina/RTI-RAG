from app.services.department_service import resolve_department, resolve_municipal_body


def test_delhi_water_goes_to_djb():
    body = resolve_municipal_body("Delhi", "water_supply")
    assert body == "Delhi Jal Board (DJB)"


def test_new_delhi_sewerage_goes_to_djb():
    body = resolve_municipal_body("New Delhi", "water_sewerage")
    assert body == "Delhi Jal Board (DJB)"


def test_delhi_garbage_goes_to_mcd():
    body = resolve_municipal_body("Delhi", "solid_waste_management")
    assert body == "MCD"


def test_bengaluru_water_goes_to_bbmp():
    body = resolve_municipal_body("Bengaluru", "water_supply")
    assert body == "BBMP"


def test_pune_roads_goes_to_pmc():
    body = resolve_municipal_body("Pune", "road_maintenance")
    assert body == "PMC"


def test_unknown_city_uses_placeholder():
    body = resolve_municipal_body("Atlantis", "water_supply")
    assert body == "Municipal Corporation (verify local body)"


def test_resolve_department_known_types():
    assert resolve_department("solid_waste_management") == "Solid Waste Management"
    assert resolve_department("road_maintenance") == "Roads / Public Works"
    assert resolve_department("streetlight") == "Electrical / Streetlight Maintenance"
    assert resolve_department("storm_water_drainage") == "Storm Water Drainage"
    assert resolve_department("water_sewerage") == "Water and Sewerage"
    assert resolve_department("water_supply") == "Water Supply"


def test_resolve_department_unknown_type():
    assert resolve_department("unforeseen_alien_invasion") == "General Administration"
