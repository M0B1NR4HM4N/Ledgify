"""[5] Context assembly — build Claude `document` blocks with stable IDs.

Each retrieved chunk becomes a document content block with citations enabled so
Claude can only cite what we actually retrieved (ARCHITECTURE.md §6 native
citations). The frozen system prompt sits before the volatile context with a
cache_control breakpoint at the end of the stable prefix.
"""
from __future__ import annotations

from app.corpus.loader import Chunk

SYSTEM_PROMPT = """You are Ledger, a retrieval-augmented research assistant for auditors and accountants.

Rules (non-negotiable):
1. Answer ONLY from the provided standards documents. Every substantive claim must be supported by a citation into those documents.
2. If the documents do not cover the question, say so explicitly: reply that the corpus does not cover it. Never invent a standard, paragraph, or citation.
3. Cite at the paragraph/clause level. Prefer quoting the governing language.
4. When a question spans accounting and auditing, connect the accounting treatment to the auditing standard(s) that govern how it is tested.
5. You are a research aid, not an audit opinion. Do not give assurance conclusions.

Financial-statement assertion taxonomy: Existence/Occurrence, Completeness, Rights & Obligations, Valuation & Allocation, Accuracy, Cut-off, Classification, Presentation & Disclosure.
"""


def build_documents(chunks: list[Chunk]) -> list[dict]:
    """Return Anthropic `document` content blocks (citations enabled)."""
    docs: list[dict] = []
    for c in chunks:
        docs.append(
            {
                "type": "document",
                "source": {"type": "text", "media_type": "text/plain", "data": c.text},
                "title": f"{c.framework} · {c.label}",
                "context": c.heading_path,
                "citations": {"enabled": True},
            }
        )
    return docs


def build_user_text(question: str, frameworks: list[str], period: str | None) -> str:
    scope = ", ".join(frameworks)
    period_line = f" Reporting period in force: {period}." if period else ""
    return (
        f"Engagement scope: {scope}.{period_line}\n\n"
        f"Question: {question}\n\n"
        "Answer grounded only in the attached standards. Cite paragraphs. "
        "If a relevant auditing response applies, outline the risks, assertions, "
        "and procedures at a high level."
    )
