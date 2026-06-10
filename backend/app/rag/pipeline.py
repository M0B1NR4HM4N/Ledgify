"""The code-orchestrated RAG loop (ARCHITECTURE.md §5).

[1] understand -> [2-3] retrieve+fuse -> [5] assemble -> [6] generate
-> [7] verify citations -> [8] assemble response + audit-log write.

Steps are deterministic control flow; only [6] is an LLM call. This is a
workflow, not an open-ended agent, which keeps answers auditable.
"""
from __future__ import annotations

import uuid

from app.audit_log import write_entry
from app.config import get_settings
from app.models import QueryRequest, QueryResponse, RetrievedChunk
from app.rag.generation import generate
from app.rag.query_understanding import understand
from app.rag.retrieval import retrieve
from app.rag.verification import verify_citations


def _confidence(coverage: float, relevance: float, verified: int) -> str:
    if verified == 0 or coverage < 0.34:
        return "low"
    if coverage >= 0.67 and verified >= 2:
        return "high"
    return "medium"


def run_query(req: QueryRequest) -> QueryResponse:
    s = get_settings()
    query_id = str(uuid.uuid4())
    plan = understand(req.question, req.engagement)
    frameworks = plan["frameworks"]

    # [2-3] hybrid retrieval + fusion
    result = retrieve(req.question, frameworks)
    hits = result.hits
    retrieved = [
        RetrievedChunk(
            chunk_id=c.id,
            framework=c.framework,
            standard_id=c.standard_id,
            paragraph_id=c.paragraph_id,
            heading_path=c.heading_path,
            text=c.text,
            score=round(score, 5),
        )
        for c, score in hits
    ]

    # Grounded refusal: corpus boundary is a hard wall (ARCHITECTURE.md §13).
    if not hits or result.relevance < s.relevance_floor:
        write_entry(query_id, req.question, [c.id for c, _ in hits], "", [], "refusal")
        return QueryResponse(
            query_id=query_id,
            intent=plan["intent"],
            refused=True,
            answer=(
                "The curated corpus does not cover this question for the selected "
                "frameworks, so Ledger will not answer. Rephrase, widen the framework "
                "scope, or consult the standard directly rather than rely on a guess."
            ),
            citations=[],
            retrieved=retrieved,
            coverage=0.0,
            confidence="low",
            frameworks_in_scope=frameworks,
        )

    chunks = [c for c, _ in hits]

    # [6] generation with native citations (or grounded stub)
    gen = generate(req.question, frameworks, req.engagement.period, chunks)

    # [7] citation verification
    citations = verify_citations(gen.citations, chunks)

    # Authoritative grounded refusal: a real-model answer with no resolving
    # citation means the retrieved standards did not actually cover the question.
    # Suppress it rather than surface an uncited claim (ARCHITECTURE.md §3/§13).
    # (The offline stub always cites, so this gate is exercised with an API key.)
    if not gen.used_stub and not citations:
        write_entry(query_id, req.question, [c.id for c in chunks], "", [], gen.model)
        return QueryResponse(
            query_id=query_id,
            intent=plan["intent"],
            refused=True,
            answer=(
                "The retrieved standards do not substantively cover this question, so "
                "Ledger will not answer rather than cite paragraphs that don't apply. "
                "Rephrase or consult the standard directly."
            ),
            citations=[],
            retrieved=retrieved,
            coverage=0.0,
            confidence="low",
            frameworks_in_scope=frameworks,
        )

    # [8] coverage / confidence signals
    cited_ids = {c.chunk_id for c in citations}
    coverage = round(len(cited_ids) / len(chunks), 3) if chunks else 0.0
    verified = sum(1 for c in citations if c.verified)
    confidence = _confidence(coverage, result.relevance, verified)

    write_entry(
        query_id,
        req.question,
        [c.id for c in chunks],
        gen.answer,
        [c.chunk_id for c in citations],
        gen.model,
    )

    return QueryResponse(
        query_id=query_id,
        intent=plan["intent"],
        refused=False,
        answer=gen.answer,
        citations=citations,
        retrieved=retrieved,
        coverage=coverage,
        confidence=confidence,
        frameworks_in_scope=frameworks,
    )
