from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.rag.retriever import get_retriever
from app.schemas import LegalChunkResponse

router = APIRouter(prefix="/legal", tags=["legal"])


@router.get("/chunks", response_model=List[LegalChunkResponse])
def list_chunks(
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction: india, delhi"),
    topic: Optional[str] = Query(None, description="Filter by topic: request, deadline, transfer, appeal, fee, water, penalty"),
):
    retriever = get_retriever()
    results = retriever.chunks_list
    if jurisdiction:
        results = [c for c in results if c.get("jurisdiction", "").lower() == jurisdiction.lower()]
    if topic:
        results = [c for c in results if c.get("topic", "").lower() == topic.lower()]
    return results


@router.get("/chunks/{chunk_id}", response_model=LegalChunkResponse)
def get_chunk_by_id(chunk_id: str):
    retriever = get_retriever()
    chunk = retriever.get_by_id(chunk_id)
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Legal chunk '{chunk_id}' not found")
    return chunk


@router.get("/search", response_model=List[LegalChunkResponse])
def search_legal_knowledge_base(
    q: str = Query(..., min_length=1, description="BM25 search query text"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    top_k: int = Query(5, ge=1, le=20, description="Max number of results to return"),
):
    retriever = get_retriever()
    return retriever.search(query=q, jurisdiction=jurisdiction, topic=topic, top_k=top_k)
