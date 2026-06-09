"""[1] Query understanding — classify intent, extract refs, normalise scope.

Deterministic, code-orchestrated (ARCHITECTURE.md §5). No LLM call here.
"""
from __future__ import annotations

import re

from app.models import EngagementContext, Intent

_STANDARD_REF = re.compile(
    r"\b(IFRS|IAS|ISA|AASB|ASC|FRS|AS|PCAOB)\s?-?\s?(\d{1,4})(?:[-.]?(\d{1,4}))?",
    re.IGNORECASE,
)

_RAP_HINTS = ("risk", "assertion", "procedure", "test", "audit response", "material misstatement")
_EQUIV_HINTS = ("equivalent", "us gaap", "uk gaap", "aasb", "asc ", "frs ", "carry over", "difference between")


def classify_intent(question: str) -> Intent:
    q = question.lower()
    if any(h in q for h in _EQUIV_HINTS):
        return "equivalence"
    if any(h in q for h in _RAP_HINTS):
        return "rap"
    if _STANDARD_REF.search(question):
        return "lookup"
    return "open"


def extract_standard_refs(question: str) -> list[str]:
    refs: list[str] = []
    for body, num, sub in _STANDARD_REF.findall(question):
        ref = f"{body.upper()} {num}" + (f".{sub}" if sub else "")
        if ref not in refs:
            refs.append(ref)
    return refs


def understand(question: str, engagement: EngagementContext) -> dict:
    return {
        "intent": classify_intent(question),
        "standard_refs": extract_standard_refs(question),
        "frameworks": [f.upper() for f in engagement.frameworks] or ["IFRS", "ISA"],
    }
