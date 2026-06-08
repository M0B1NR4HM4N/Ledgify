"""Load the seed corpus into memory (Phase 1 uses an in-memory index)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from app.config import CORPUS_PATH


@dataclass(frozen=True)
class Chunk:
    """A paragraph-level chunk — the atomic citable unit (ARCHITECTURE.md §2.1)."""

    id: str
    framework: str
    standard_id: str
    paragraph_id: str
    heading_path: str
    effective_date: str
    text: str

    @property
    def label(self) -> str:
        return f"{self.standard_id} ¶{self.paragraph_id}"


@lru_cache
def load_corpus() -> list[Chunk]:
    raw = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    return [Chunk(**row) for row in raw]
