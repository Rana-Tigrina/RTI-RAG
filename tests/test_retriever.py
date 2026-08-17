from app.rag.retriever import get_retriever
from app.rag.seed_kb import seed_database


def test_get_delhi_fee_chunk():
    seed_database()
    retriever = get_retriever()
    chunk = retriever.get_by_id("delhi-r5-fee")
    assert chunk is not None
    assert chunk["section"] == "Fee Rules"
    assert chunk["jurisdiction"] == "delhi"


def test_search_appeal_sections():
    seed_database()
    retriever = get_retriever()
    results = retriever.search("first appeal delayed RTI", topic="appeal")
    assert any(result["id"] == "rti-s19-1" for result in results)


def test_search_transfer_section():
    seed_database()
    retriever = get_retriever()
    results = retriever.search("transfer to other public authority", topic="transfer")
    assert any(result["id"] == "rti-s6-3" for result in results)
