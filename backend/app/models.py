"""Pydantic request/response schemas for the Query Service."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Intent = Literal["lookup", "equivalence", "rap", "open"]


class EngagementContext(BaseModel):
    """User-stated scope; narrows retrieval (ARCHITECTURE.md §3 Workflow)."""

    frameworks: list[str] = Field(default_factory=lambda: ["IFRS", "ISA"])
    jurisdiction: str | None = None
    period: str | None = None  # e.g. "FY2024"


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    engagement: EngagementContext = Field(default_factory=EngagementContext)


class Citation(BaseModel):
    """A resolved, verified citation pointing into a real corpus chunk."""

    chunk_id: str
    framework: str
    standard_id: str
    paragraph_id: str
    heading_path: str
    quoted_text: str
    verified: bool


class RetrievedChunk(BaseModel):
    chunk_id: str
    framework: str
    standard_id: str
    paragraph_id: str
    heading_path: str
    text: str
    score: float


class QueryResponse(BaseModel):
    query_id: str
    intent: Intent
    refused: bool
    answer: str
    citations: list[Citation]
    retrieved: list[RetrievedChunk]
    coverage: float          # 0..1 retrieval coverage signal
    confidence: Literal["low", "medium", "high"]
    frameworks_in_scope: list[str]
    not_advice: str = (
        "Research aid only — Ledger surfaces standards; it is not an audit opinion."
    )
