#!/usr/bin/env python3
"""Civic RTI & First Appeal Drafter — Command Line Interface.

Run interactive or scripted civic RTI operations locally without a browser.
"""

import sys
import argparse
import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import SessionLocal, Base, engine
from app.rag.seed_kb import seed_database
from app.rag.retriever import get_retriever
from app.services import case_service


def init_app():
    Base.metadata.create_all(bind=engine)
    seed_database()


def cmd_create(args):
    db = SessionLocal()
    try:
        case, questions = case_service.create_case(db, user_text=args.text, city=args.city)
        print("\n" + "=" * 60)
        print(f"🏛️  CIVIC CASE CREATED: {case.id}")
        print("=" * 60)
        print(f"Status:         {case.status}")
        print(f"Category:       {case.issue_type}")
        print(f"Department:     {case.department}")
        print(f"Municipal Body: {case.municipal_body}")
        print(f"Fee Amount:     ₹{case.fee_amount}")
        if questions:
            print("\n⚠️  Clarifying questions for best legal impact:")
            for q in questions:
                print(f"  - {q}")
        print("=" * 60)
    finally:
        db.close()


def cmd_draft(args):
    db = SessionLocal()
    try:
        case, draft_res = case_service.generate_and_save_draft(db, args.case_id, submitted_on=args.submitted_on)
        print("\n" + "=" * 60)
        print(f"📄  RTI APPLICATION DRAFT FOR CASE: {case.id}")
        print("=" * 60)
        print(draft_res["draft_markdown"])
        print("\n" + "=" * 60)
        print(f"Application Fee: ₹{draft_res['fee']['amount']} ({draft_res['fee']['currency']})")
        print(f"Fee Notes:       {draft_res['fee']['notes']}")
        print(f"Citations:       {len(draft_res['legal_citations'])} attached")
        print("=" * 60)
        if args.output:
            out_p = Path(args.output)
            out_p.write_text(draft_res["draft_markdown"], encoding="utf-8")
            print(f"✅ Saved draft to: {out_p.resolve()}")
    finally:
        db.close()


def cmd_submit(args):
    db = SessionLocal()
    try:
        sub_date = args.date or datetime.date.today().isoformat()
        case = case_service.submit_case(db, args.case_id, submitted_on=sub_date)
        print("\n" + "=" * 60)
        print(f"📬  CASE MARKED SUBMITTED: {case.id}")
        print("=" * 60)
        print(f"Submission Date:       {case.submission_date}")
        print(f"Statutory Due Date:    {case.response_due_date} (30 days)")
        print(f"Overdue Non-Compliance: {case.overdue_from}")
        print(f"First Appeal Period:   Until {case.appeal_file_by}")
        print("=" * 60)
    finally:
        db.close()


def cmd_appeal(args):
    db = SessionLocal()
    try:
        as_of = args.as_of or datetime.date.today().isoformat()
        case, appeal_res = case_service.generate_and_save_appeal(db, args.case_id, as_of=as_of)
        print("\n" + "=" * 60)
        print(f"⚖️  FIRST APPEAL DRAFT FOR CASE: {case.id}")
        print("=" * 60)
        print(f"Days Overdue: {appeal_res['days_overdue']} days")
        print("=" * 60)
        print(appeal_res["appeal_markdown"])
        print("\n" + "=" * 60)
        if args.output:
            out_p = Path(args.output)
            out_p.write_text(appeal_res["appeal_markdown"], encoding="utf-8")
            print(f"✅ Saved appeal to: {out_p.resolve()}")
    except ValueError as e:
        print(f"\n❌ Error: {e}")
    finally:
        db.close()


def cmd_list(args):
    db = SessionLocal()
    try:
        cases = case_service.list_cases(db, status=args.status, city=args.city)
        print("\n" + "=" * 80)
        print(f"{'CASE ID':<38} | {'CITY':<12} | {'STATUS':<20} | {'DUE DATE':<10}")
        print("=" * 80)
        for c in cases:
            print(f"{c['id']:<38} | {str(c['city'] or 'National'):<12} | {c['status']:<20} | {str(c.get('response_due_date') or '-'):<10}")
        print("=" * 80)
        print(f"Total: {len(cases)} case(s)")
    finally:
        db.close()


def cmd_search_legal(args):
    init_app()
    retriever = get_retriever()
    results = retriever.search(args.query, topic=args.topic, top_k=args.top_k)
    print("\n" + "=" * 80)
    print(f"🔍 BM25 LEGAL KNOWLEDGE SEARCH: '{args.query}' (Found {len(results)} chunks)")
    print("=" * 80)
    for r in results:
        print(f"\n📜 [{r['id']}] {r['act']} — {r['section']}: {r['title']}")
        print(f"   Jurisdiction: {r['jurisdiction']} | Topic: {r['topic']}")
        print(f"   {r['text']}")
    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Civic RTI & First Appeal Drafter CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Create and classify a civic grievance case")
    p_create.add_argument("--text", "-t", required=True, help="Description of civic issue")
    p_create.add_argument("--city", "-c", default=None, help="City name (e.g. Delhi, Bengaluru)")
    p_create.set_defaults(func=cmd_create)

    # draft
    p_draft = subparsers.add_parser("draft", help="Generate RTI application draft")
    p_draft.add_argument("case_id", help="Case UUID")
    p_draft.add_argument("--submitted-on", default=None, help="Submission date if already filed")
    p_draft.add_argument("--output", "-o", default=None, help="Output markdown file path")
    p_draft.set_defaults(func=cmd_draft)

    # submit
    p_submit = subparsers.add_parser("submit", help="Record submission and calculate deadlines")
    p_submit.add_argument("case_id", help="Case UUID")
    p_submit.add_argument("--date", "-d", default=None, help="Submission date (YYYY-MM-DD)")
    p_submit.set_defaults(func=cmd_submit)

    # appeal
    p_appeal = subparsers.add_parser("appeal", help="Generate First Appeal draft if overdue")
    p_appeal.add_argument("case_id", help="Case UUID")
    p_appeal.add_argument("--as-of", default=None, help="Evaluation date (YYYY-MM-DD)")
    p_appeal.add_argument("--output", "-o", default=None, help="Output markdown file path")
    p_appeal.set_defaults(func=cmd_appeal)

    # list
    p_list = subparsers.add_parser("list", help="List all tracked civic cases")
    p_list.add_argument("--status", default=None, help="Filter by status")
    p_list.add_argument("--city", default=None, help="Filter by city")
    p_list.set_defaults(func=cmd_list)

    # search-legal
    p_search = subparsers.add_parser("search-legal", help="Search legal knowledge base via BM25")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--topic", default=None, help="Filter by topic")
    p_search.add_argument("--top-k", type=int, default=5, help="Number of results")
    p_search.set_defaults(func=cmd_search_legal)

    args = parser.parse_args()
    init_app()
    args.func(args)


if __name__ == "__main__":
    main()
