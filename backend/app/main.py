"""FastAPI app — the Query Service entrypoint (ARCHITECTURE.md §4)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.corpus.loader import load_corpus
from app.models import QueryRequest, QueryResponse
from app.rag.pipeline import run_query

app = FastAPI(title="Ledger — Query Service", version="0.1.0 (M1)")

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(_settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    corpus = load_corpus()
    frameworks = sorted({c.framework for c in corpus})

    if _settings.provider == "gemini":
        live = bool(_settings.gemini_api_key)
        generation = "gemini" if live else "offline-stub"
        model = _settings.gemini_model
    else:
        live = bool(_settings.anthropic_api_key)
        generation = "claude" if live else "offline-stub"
        model = _settings.answer_model

    return {
        "status": "ok",
        "milestone": "M1 — Grounded Q&A (single framework)",
        "corpus_chunks": len(corpus),
        "frameworks": frameworks,
        "provider": _settings.provider,
        "generation": generation,
        "answer_model": model,
    }


@app.post("/api/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    return run_query(req)
