# Ledger — Phase 1 (M1: Grounded Q&A)

A retrieval-augmented assistant for auditors and accountants. This is the first
milestone from [`ARCHITECTURE.md`](./ARCHITECTURE.md) — **M1: Grounded Q&A,
single framework set (IFRS + ISA)**:

- Paragraph-level corpus + **hybrid retrieval** (BM25 + dense, fused with RRF)
- **Native Claude citations** bounded to retrieved standards, with a post-generation **citation verifier**
- **Grounded refusal** — no corpus support ⇒ explicit "not covered", never a fabricated cite
- **Append-only audit log** — every Q → context → answer → citations tuple is reproducible
- **ElevenLabs-style web app** in the warm paper/walnut/gold brand palette (light + dark)

> Later milestones (cross-framework equivalence, RAP builder, working-paper export,
> engagement memory) are intentionally out of scope here — see §12 of the architecture.

```
Ledgify/
├── ARCHITECTURE.md          # the design contract
├── backend/                 # FastAPI Query Service (the RAG workflow)
│   └── app/
│       ├── main.py              # /api/query, /api/health
│       ├── corpus/              # seed IFRS + ISA paragraph chunks
│       └── rag/                 # understand → retrieve → assemble → generate → verify
└── frontend/                # Next.js 15 + Tailwind v4 (OKLCH brand tokens)
```

## Run the backend (Python only — runs with no API key)

```bash
cd backend
./run.sh            # creates .venv, installs deps, starts uvicorn on :8000
```

Without `LEDGER_ANTHROPIC_API_KEY` it runs a **grounded offline stub** (still
citation-bounded to retrieved chunks) so the whole pipeline works end-to-end. Set
the key in `backend/.env` to switch on real Claude Opus 4.8 generation with native
document citations and full LLM grounded-refusal.

Health check: <http://localhost:8000/api/health>

## Run the frontend (needs Node.js)

```bash
brew install node              # not yet installed on this machine
cd frontend
cp .env.local.example .env.local
npm install
npm run dev                    # http://localhost:3000
```

## What "grounded refusal" means here

Refusal is layered (architecture §3/§13):

1. **Coarse pre-filter** — a low cosine-relevance floor blocks clearly-unrelated
   questions ("how do I bake bread") before any LLM call.
2. **Authoritative gate** — with an API key, Claude answers only from the attached
   standards; if it produces no resolving citation, the answer is suppressed.

> Note: the dense leg of retrieval is a TF-IDF stand-in for now, so borderline
> refusal calibration is limited without an API key. Real pgvector embeddings
> (a later milestone) and Claude's judgment sharpen it. This is called out in
> `backend/app/config.py`.

## Brand palette

Cream `#F8F5ED` · Ink brown `#291F18` · Walnut `#402E20` · Gold `#C7A04E` ·
Parchment `#EFE6D3` — defined as OKLCH tokens in `frontend/app/globals.css`
(full light + dark token sets).
