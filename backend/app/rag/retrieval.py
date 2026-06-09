"""[2-3] Hybrid retrieval + fusion.

Standards questions mix exact terminology ("right-of-use asset", "ASC 842-40")
with conceptual intent, so neither lexical nor semantic search alone suffices
(ARCHITECTURE.md §4 / §13). Phase 1 ships a runnable in-memory hybrid retriever:

  * BM25 (rank_bm25)              -> exact-term recall
  * TF-IDF cosine (scikit-learn) -> stands in for dense embeddings until the
                                    pgvector index lands in a later milestone

The two ranked lists are merged with Reciprocal Rank Fusion (RRF). Swapping the
TF-IDF leg for real embeddings later does not change the fusion or downstream code.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import get_settings
from app.corpus.loader import Chunk, load_corpus

_TOKEN = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


@dataclass
class SearchResult:
    hits: list[tuple[Chunk, float]]   # (chunk, fused RRF score), ranked
    relevance: float                  # best absolute cosine in scope; refusal gate


class HybridIndex:
    """In-memory BM25 + TF-IDF index over the corpus."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        docs = [f"{c.heading_path} {c.label} {c.text}" for c in chunks]
        self._bm25 = BM25Okapi([_tokenize(d) for d in docs])
        self._tfidf = TfidfVectorizer(stop_words="english")
        self._matrix = self._tfidf.fit_transform(docs)

    def _bm25_ranking(self, query: str) -> list[int]:
        scores = self._bm25.get_scores(_tokenize(query))
        return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    def _dense_ranking(self, query: str) -> list[int]:
        qv = self._tfidf.transform([query])
        sims = cosine_similarity(qv, self._matrix)[0]
        return sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)

    def _cosine(self, query: str):
        qv = self._tfidf.transform([query])
        return cosine_similarity(qv, self._matrix)[0]

    def search(
        self,
        query: str,
        frameworks: list[str],
        top_k: int,
        rrf_k: int,
    ) -> "SearchResult":
        bm25 = self._bm25_ranking(query)
        dense = self._dense_ranking(query)
        cos = self._cosine(query)

        # Reciprocal Rank Fusion: score = sum 1 / (rrf_k + rank)
        fused: dict[int, float] = {}
        for ranking in (bm25, dense):
            for rank, idx in enumerate(ranking):
                fused[idx] = fused.get(idx, 0.0) + 1.0 / (rrf_k + rank)

        scope = {f.upper() for f in frameworks}
        in_scope = [i for i, c in enumerate(self.chunks) if not scope or c.framework.upper() in scope]
        # Absolute relevance gate (semantic, not rank-based): best cosine in scope.
        relevance = max((float(cos[i]) for i in in_scope), default=0.0)

        ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)
        out: list[tuple[Chunk, float]] = []
        for idx, score in ranked:
            chunk = self.chunks[idx]
            if scope and chunk.framework.upper() not in scope:
                continue
            out.append((chunk, score))
            if len(out) >= top_k:
                break
        return SearchResult(hits=out, relevance=relevance)


@lru_cache
def get_index() -> HybridIndex:
    return HybridIndex(load_corpus())


def retrieve(query: str, frameworks: list[str]) -> SearchResult:
    s = get_settings()
    return get_index().search(query, frameworks, s.top_k, s.rrf_k)
