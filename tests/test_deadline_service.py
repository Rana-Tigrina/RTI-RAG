import datetime
from app.services.deadline_service import calculate_deadline, calculate_first_appeal_deadline, is_overdue


def test_deadline_is_30_days():
    result = calculate_deadline("2026-08-20")
    assert result["submitted_on"] == "2026-08-20"
    assert result["response_due_date"] == "2026-09-19"
    assert result["overdue_from"] == "2026-09-20"


def test_first_appeal_deadline():
    result = calculate_first_appeal_deadline("2026-09-19")
    assert result["appeal_eligible_from"] == "2026-09-20"
    assert result["appeal_file_by"] == "2026-10-19"


def test_is_overdue_function():
    # Due on Sep 19, check as of Sep 18 (not overdue)
    assert not is_overdue("2026-09-19", as_of=datetime.date(2026, 9, 18))
    # Due on Sep 19, check as of Sep 19 (last day, not overdue)
    assert not is_overdue("2026-09-19", as_of=datetime.date(2026, 9, 19))
    # Due on Sep 19, check as of Sep 20 (overdue)
    assert is_overdue("2026-09-19", as_of=datetime.date(2026, 9, 20))
