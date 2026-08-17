import datetime
from pathlib import Path
import sys

# Ensure root directory in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import engine, SessionLocal, Base
from app.rag.seed_kb import seed_database
from app.services import case_service


def seed_demo():
    Base.metadata.create_all(bind=engine)
    seed_database()
    db = SessionLocal()

    print("Seeding sample civic cases...")

    # Case 1: Fresh classification (Delhi - Garbage)
    case1, _ = case_service.create_case(
        db,
        user_text="Garbage has not been collected near the main residential park in Lajpat Nagar for over two weeks.",
        city="Delhi",
    )
    print(f"Created Case 1 (Fresh): {case1.id} [{case1.status}]")

    # Case 2: Draft generated (Bengaluru - Streetlight)
    case2, _ = case_service.create_case(
        db,
        user_text="Streetlights are completely non-functional along 100ft Road in Indiranagar creating safety hazards at night.",
        city="Bengaluru",
    )
    case_service.generate_and_save_draft(db, case2.id)
    case_service.approve_draft(db, case2.id)
    print(f"Created Case 2 (Approved Draft): {case2.id} [{case2.status}]")

    # Case 3: Submitted / Awaiting Response (Delhi - Water Supply / DJB)
    case3, _ = case_service.create_case(
        db,
        user_text="Severe water supply disruption and dirty tap water with foul smell received in Hauz Khas colony.",
        city="Delhi",
    )
    case_service.generate_and_save_draft(db, case3.id)
    case_service.approve_draft(db, case3.id)
    ten_days_ago = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
    case_service.submit_case(db, case3.id, submitted_on=ten_days_ago)
    print(f"Created Case 3 (Submitted/Awaiting): {case3.id} [{case3.status}]")

    # Case 4: Overdue Case (Pune - Road Potholes)
    case4, _ = case_service.create_case(
        db,
        user_text="Massive potholes and cave-in on primary connecting road near Shivaji Nagar causing repeated vehicular accidents.",
        city="Pune",
    )
    case_service.generate_and_save_draft(db, case4.id)
    case_service.approve_draft(db, case4.id)
    forty_days_ago = (datetime.date.today() - datetime.timedelta(days=40)).isoformat()
    case_service.submit_case(db, case4.id, submitted_on=forty_days_ago)
    # Generate first appeal
    case_service.generate_and_save_appeal(db, case4.id, as_of=datetime.date.today().isoformat())
    print(f"Created Case 4 (Overdue / First Appeal Ready): {case4.id} [{case4.status}]")

    db.close()
    print("Demo data successfully seeded!")


if __name__ == "__main__":
    seed_demo()
