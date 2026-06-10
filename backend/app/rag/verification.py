"""[7] Citation verification — the secondary anti-hallucination backstop.

Every citation must resolve to a real retrieved chunk AND its quoted text must
match the source within tolerance (ARCHITECTURE.md §3 / §10). Citations that do
not resolve are dropped and flagged unverified.
"""
from __future__ import annotations

import re

from app.corpus.loader import Chunk
from app.models import Citation
from app.rag.generation import RawCitation

_WS = re.compile(r"\s+")


def _normalise(text: str) -> str:
    return _WS.sub(" ", text).strip().lower()


def _matches(quoted: str, source: str) -> bool:
    q, s = _normalise(quoted), _normalise(source)
    if not q:
        return False
    return q in s or s in q


def verify_citations(raw: list[RawCitation], chunks: list[Chunk]) -> list[Citation]:
    out: list[Citation] = []
    seen: set[tuple[str, str]] = set()
    for rc in raw:
        if rc.document_index < 0 or rc.document_index >= len(chunks):
            continue  # cannot resolve -> suppress
        chunk = chunks[rc.document_index]
        quoted = rc.cited_text.strip() or chunk.text
        verified = _matches(quoted, chunk.text)
        key = (chunk.id, _normalise(quoted)[:80])
        if key in seen:
            continue
        seen.add(key)
        out.append(
            Citation(
                chunk_id=chunk.id,
                framework=chunk.framework,
                standard_id=chunk.standard_id,
                paragraph_id=chunk.paragraph_id,
                heading_path=chunk.heading_path,
                quoted_text=quoted,
                verified=verified,
            )
        )
    return out
