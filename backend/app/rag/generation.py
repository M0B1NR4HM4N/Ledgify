"""[6] Generation — Claude Opus 4.8 with native document citations.

If no API key is configured, a deterministic grounded stub runs instead so the
whole pipeline is end-to-end runnable without credentials. The stub still only
"cites" retrieved chunks, mirroring the real anti-hallucination guarantee.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings
from app.corpus.loader import Chunk
from app.rag.context import SYSTEM_PROMPT, build_documents, build_user_text


@dataclass
class RawCitation:
    document_index: int
    cited_text: str


@dataclass
class Generation:
    answer: str
    citations: list[RawCitation]
    model: str
    used_stub: bool


def _generate_stub(question: str, chunks: list[Chunk]) -> Generation:
    """Grounded, citation-bounded fallback used when no API key is present."""
    top = chunks[:3]
    lines = [
        "Based on the retrieved standards (offline grounded mode — set "
        "LEDGER_ANTHROPIC_API_KEY for full Claude generation):",
        "",
    ]
    citations: list[RawCitation] = []
    for i, c in enumerate(top):
        lines.append(f"- Per {c.framework} {c.label}: {c.text}")
        citations.append(RawCitation(document_index=i, cited_text=c.text))
    lines.append("")
    lines.append(
        "These paragraphs are the governing language for your question; review the "
        "cited source text before relying on it."
    )
    return Generation("\n".join(lines), citations, model="offline-stub", used_stub=True)


def generate(question: str, frameworks: list[str], period: str | None, chunks: list[Chunk]) -> Generation:
    s = get_settings()
    if not s.anthropic_api_key:
        return _generate_stub(question, chunks)

    # Import lazily so the stub path needs no SDK installed.
    from anthropic import Anthropic

    client = Anthropic(api_key=s.anthropic_api_key)
    documents = build_documents(chunks)
    user_text = build_user_text(question, frameworks, period)

    kwargs: dict = {
        "model": s.answer_model,
        "max_tokens": s.max_tokens,
        "system": [
            {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}
        ],
        "messages": [
            {"role": "user", "content": [*documents, {"type": "text", "text": user_text}]}
        ],
    }
    if s.thinking_enabled:
        kwargs["thinking"] = {"type": "adaptive"}

    resp = client.messages.create(**kwargs)

    answer_parts: list[str] = []
    citations: list[RawCitation] = []
    for block in resp.content:
        if getattr(block, "type", None) != "text":
            continue
        answer_parts.append(block.text)
        for cit in getattr(block, "citations", None) or []:
            doc_idx = getattr(cit, "document_index", None)
            cited = getattr(cit, "cited_text", "") or ""
            if doc_idx is not None:
                citations.append(RawCitation(document_index=doc_idx, cited_text=cited))

    return Generation("".join(answer_parts).strip(), citations, model=s.answer_model, used_stub=False)
