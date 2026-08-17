from app.services.fee_service import calculate_fee
from app.rag.seed_kb import seed_database


def test_default_fee_amount():
    fee = calculate_fee("Unknown City")
    assert fee["amount"] == 10
    assert fee["currency"] == "INR"
    assert "Verify current rules" in fee["notes"]


def test_delhi_fee_has_citation_when_available():
    seed_database()
    fee = calculate_fee("Delhi")
    assert fee["amount"] == 10
    assert fee["currency"] == "INR"
    assert "Delhi RTI Rules" in fee["notes"]
    if fee["citation"] is not None:
        assert fee["citation"]["id"] == "delhi-r5-fee"
        assert fee["citation"]["section"] == "Fee Rules"
