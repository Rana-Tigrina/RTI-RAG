import math
import re
import unicodedata
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import LegalChunk

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    class BM25Okapi:  # type: ignore
        """Pure Python fallback implementation of BM25Okapi algorithm."""
        def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75, epsilon: float = 0.25):
            self.corpus_size = len(corpus)
            self.avgdl = sum(len(doc) for doc in corpus) / self.corpus_size if self.corpus_size > 0 else 1.0
            self.corpus = corpus
            self.k1 = k1
            self.b = b
            self.epsilon = epsilon
            self.doc_len = [len(doc) for doc in corpus]
            self.doc_freqs: List[Dict[str, int]] = []
            self.nd: Dict[str, int] = {}
            for doc in corpus:
                frequencies: Dict[str, int] = {}
                for word in doc:
                    frequencies[word] = frequencies.get(word, 0) + 1
                self.doc_freqs.append(frequencies)
                for word in frequencies:
                    self.nd[word] = self.nd.get(word, 0) + 1
            self.idf: Dict[str, float] = {}
            self._calc_idf()

        def _calc_idf(self):
            idf_sum = 0
            negative_idfs = []
            for word, freq in self.nd.items():
                idf = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)
                self.idf[word] = idf
                idf_sum += idf
                if idf < 0:
                    negative_idfs.append(word)
            average_idf = idf_sum / len(self.idf) if self.idf else 0.0
            eps = self.epsilon * average_idf
            for word in negative_idfs:
                self.idf[word] = eps

        def get_scores(self, query: List[str]) -> List[float]:
            if self.corpus_size == 0:
                return []
            scores = [0.0] * self.corpus_size
            for q in query:
                q_freq = self.nd.get(q, 0)
                if q_freq == 0:
                    continue
                q_idf = self.idf.get(q, 0.0)
                for idx, doc_freq in enumerate(self.doc_freqs):
                    freq = doc_freq.get(q, 0)
                    if freq == 0:
                        continue
                    numerator = freq * (self.k1 + 1)
                    avg_len = self.avgdl if self.avgdl > 0 else 1.0
                    denominator = freq + self.k1 * (1 - self.b + self.b * (self.doc_len[idx] / avg_len))
                    if denominator > 0:
                        scores[idx] += q_idf * (numerator / denominator)
            return scores


def _tokenize(text: str) -> list[str]:
    """Tokenize and normalize text removing punctuation and Unicode anomalies."""
    if not text:
        return []
    # Normalize Unicode (NFKD)
    normalized = unicodedata.normalize("NFKD", str(text))
    # Extract lowercased alphanumeric tokens
    return [w.lower() for w in re.findall(r"\w+", normalized) if w]


class LegalRetriever:
    def __init__(self, db_session_factory=SessionLocal):
        self.db_session_factory = db_session_factory
        self.chunks_by_id: Dict[str, Dict[str, Any]] = {}
        self.chunks_list: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None
        self.reload()

    def reload(self):
        db: Session = self.db_session_factory()
        try:
            db_chunks = db.query(LegalChunk).all()
            self.chunks_list = [
                {
                    "id": c.id,
                    "jurisdiction": c.jurisdiction,
                    "act": c.act,
                    "section": c.section,
                    "topic": c.topic,
                    "title": c.title,
                    "text": c.text,
                    "source": c.source,
                    "updated_at": c.updated_at,
                }
                for c in db_chunks
            ]
            self.chunks_by_id = {c["id"]: c for c in self.chunks_list}

            if self.chunks_list:
                corpus = [
                    _tokenize(f"{c['title']} {c['text']} {c['topic']} {c['section']} {c['act']}")
                    for c in self.chunks_list
                ]
                self.bm25 = BM25Okapi(corpus)
            else:
                self.bm25 = None
        finally:
            db.close()

    def get_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        if not chunk_id:
            return None
        if chunk_id in self.chunks_by_id:
            return self.chunks_by_id[chunk_id]
        
        # If not found in memory cache, try fresh DB lookup
        db: Session = self.db_session_factory()
        try:
            c = db.query(LegalChunk).filter(LegalChunk.id == chunk_id).first()
            if c:
                chunk_dict = {
                    "id": c.id,
                    "jurisdiction": c.jurisdiction,
                    "act": c.act,
                    "section": c.section,
                    "topic": c.topic,
                    "title": c.title,
                    "text": c.text,
                    "source": c.source,
                    "updated_at": c.updated_at,
                }
                self.chunks_by_id[c.id] = chunk_dict
                return chunk_dict
            return None
        finally:
            db.close()

    def search(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        topic: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        if not self.chunks_list:
            self.reload()

        if not self.chunks_list or not self.bm25:
            return []

        # Filter candidates based on jurisdiction and topic
        candidate_indices = []
        for idx, c in enumerate(self.chunks_list):
            if jurisdiction and c.get("jurisdiction", "").lower() != jurisdiction.lower().strip():
                continue
            if topic and c.get("topic", "").lower() != topic.lower().strip():
                continue
            candidate_indices.append(idx)

        if not candidate_indices:
            return []

        tokenized_query = _tokenize(query)
        if not tokenized_query:
            return [self.chunks_list[i] for i in candidate_indices[:top_k]]

        doc_scores = self.bm25.get_scores(tokenized_query)
        
        # Rank filtered candidates by their BM25 score
        scored_candidates = [(idx, doc_scores[idx]) for idx in candidate_indices]
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        return [self.chunks_list[idx] for idx, _ in scored_candidates[:top_k]]


_retriever_instance: Optional[LegalRetriever] = None


def get_retriever() -> LegalRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = LegalRetriever()
    return _retriever_instance
