"""Append-only audit log.

Every Q -> retrieved-context -> answer -> citations tuple is logged so an answer
is reproducible from its inputs (ARCHITECTURE.md §9). Phase 1 uses an append-only
JSONL file; a later milestone moves this to the immutable Postgres table.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from app.config import AUDIT_LOG_PATH


def prompt_hash(question: str, chunk_ids: list[str], model: str) -> str:
    h = hashlib.sha256()
    h.update(question.encode("utf-8"))
    h.update("|".join(chunk_ids).encode("utf-8"))
    h.update(model.encode("utf-8"))
    return h.hexdigest()


def write_entry(
    query_id: str,
    question: str,
    retrieved_chunk_ids: list[str],
    answer: str,
    citation_ids: list[str],
    model: str,
) -> None:
    entry = {
        "query_id": query_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "retrieved_chunk_ids": retrieved_chunk_ids,
        "citation_ids": citation_ids,
        "model": model,
        "prompt_hash": prompt_hash(question, retrieved_chunk_ids, model),
        "answer_len": len(answer),
    }
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
