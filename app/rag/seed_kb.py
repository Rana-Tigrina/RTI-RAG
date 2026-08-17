import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models import LegalChunk
from app.rag.retriever import get_retriever


def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    base_dir = Path(__file__).resolve().parent.parent.parent
    data_files = [
        base_dir / "kb" / "data" / "rti_act_2005.jsonl",
        base_dir / "kb" / "data" / "delhi_rti_rules.jsonl",
    ]

    total_seeded = 0
    try:
        for file_path in data_files:
            if not file_path.exists():
                print(f"File not found: {file_path}")
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    chunk_id = item["id"]

                    existing = db.query(LegalChunk).filter(LegalChunk.id == chunk_id).first()
                    if existing:
                        existing.jurisdiction = item["jurisdiction"]
                        existing.act = item["act"]
                        existing.section = item["section"]
                        existing.topic = item["topic"]
                        existing.title = item["title"]
                        existing.text = item["text"]
                        existing.source = item["source"]
                    else:
                        new_chunk = LegalChunk(
                            id=chunk_id,
                            jurisdiction=item["jurisdiction"],
                            act=item["act"],
                            section=item["section"],
                            topic=item["topic"],
                            title=item["title"],
                            text=item["text"],
                            source=item["source"],
                        )
                        db.add(new_chunk)
                    total_seeded += 1

        db.commit()
        print(f"Successfully seeded {total_seeded} legal chunks into knowledge base.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding legal chunks: {e}")
        raise
    finally:
        db.close()

    # Re-index the retriever
    retriever = get_retriever()
    retriever.reload()
    print("Legal retriever reloaded with seeded chunks.")


if __name__ == "__main__":
    seed_database()
