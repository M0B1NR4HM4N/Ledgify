"""Central configuration for the Ledger backend (Phase 1 / M1)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
CORPUS_PATH = BASE_DIR / "corpus" / "seed_corpus.json"
AUDIT_LOG_PATH = BASE_DIR.parent / "audit_log.jsonl"


class Settings(BaseSettings):
    """Runtime settings, overridable via environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="LEDGER_", extra="ignore")

    # --- Claude API (see ARCHITECTURE.md §6) ---
    anthropic_api_key: str | None = None
    answer_model: str = "claude-opus-4-8"          # correctness-sensitive main path
    lookup_model: str = "claude-sonnet-4-6"         # cost/speed fallback per-endpoint
    max_tokens: int = 16000
    thinking_enabled: bool = True

    # --- Retrieval (see ARCHITECTURE.md §5) ---
    top_k: int = 6                                  # chunks kept after fusion
    rrf_k: int = 60                                 # reciprocal-rank-fusion constant
    # Grounded-refusal pre-filter: a deliberately coarse semantic gate on the best
    # in-scope cosine relevance — it only blocks clearly-unrelated queries. The
    # AUTHORITATIVE refusal is the LLM grounded-refusal + citation verifier
    # (§3/§13): if generation yields no resolving citation, the answer is
    # suppressed. TF-IDF cannot finely separate borderline cases; real dense
    # embeddings (a later milestone) sharpen this pre-filter.
    relevance_floor: float = 0.20

    # --- Phase 1 framework scope (M1 = IFRS + ISA) ---
    default_frameworks: tuple[str, ...] = ("IFRS", "ISA")

    # --- Server ---
    cors_origins: tuple[str, ...] = ("http://localhost:3000", "http://127.0.0.1:3000")


@lru_cache
def get_settings() -> Settings:
    return Settings()
