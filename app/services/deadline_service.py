import datetime
from typing import Union

RESPONSE_WINDOW_DAYS = 30
FIRST_APPEAL_WINDOW_DAYS = 30


def _parse_date(d: Union[str, datetime.date, None]) -> datetime.date:
    """Robustly parse a date object or string supporting multiple common formats."""
    if d is None:
        raise ValueError("Date cannot be null or empty.")

    if isinstance(d, datetime.date):
        return d

    clean_str = str(d).strip()
    if not clean_str:
        raise ValueError("Date string cannot be blank.")

    # If it contains time (ISO format), take only the date part
    if "T" in clean_str:
        clean_str = clean_str.split("T")[0]
    elif " " in clean_str:
        clean_str = clean_str.split(" ")[0]

    # Try ISO format first (fast path: YYYY-MM-DD)
    try:
        return datetime.date.fromisoformat(clean_str)
    except ValueError:
        pass

    # Fallback to alternative common citizen input formats
    formats = [
        "%d-%m-%Y",  # 20-08-2026
        "%d/%m/%Y",  # 20/08/2026
        "%Y/%m/%d",  # 2026/08/20
        "%d.%m.%Y",  # 20.08.2026
        "%B %d, %Y", # August 20, 2026
        "%b %d, %Y", # Aug 20, 2026
    ]

    for fmt in formats:
        try:
            return datetime.datetime.strptime(clean_str, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Invalid date format: '{d}'. Please provide a valid date (e.g. YYYY-MM-DD or DD-MM-YYYY).")


def calculate_deadline(submitted_on: Union[str, datetime.date], allow_future: bool = False) -> dict:
    """Calculate the 30-day statutory response deadline under Section 7(1) of RTI Act 2005."""
    sub_date = _parse_date(submitted_on)
    
    if not allow_future and sub_date > datetime.date.today():
        # Soft safety check: warn or allow, but keep mathematically consistent
        pass

    response_due_date = sub_date + datetime.timedelta(days=RESPONSE_WINDOW_DAYS)
    overdue_from = response_due_date + datetime.timedelta(days=1)
    
    return {
        "submitted_on": sub_date.isoformat(),
        "response_due_date": response_due_date.isoformat(),
        "overdue_from": overdue_from.isoformat(),
    }


def is_overdue(response_due_date: Union[str, datetime.date], as_of: Union[str, datetime.date, None] = None) -> bool:
    """Check whether the statutory response deadline has elapsed."""
    due_date = _parse_date(response_due_date)
    if as_of is None:
        as_of_date = datetime.date.today()
    else:
        as_of_date = _parse_date(as_of)
        
    return as_of_date > due_date


def calculate_first_appeal_deadline(response_due_date: Union[str, datetime.date]) -> dict:
    """Calculate the statutory First Appeal filing period under Section 19(1) of RTI Act 2005."""
    due_date = _parse_date(response_due_date)
    appeal_eligible_from = due_date + datetime.timedelta(days=1)
    appeal_file_by = due_date + datetime.timedelta(days=FIRST_APPEAL_WINDOW_DAYS)
    
    return {
        "appeal_eligible_from": appeal_eligible_from.isoformat(),
        "appeal_file_by": appeal_file_by.isoformat(),
    }
