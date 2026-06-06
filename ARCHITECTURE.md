# Ledger — Architecture

**A retrieval-augmented (RAG) assistant for auditors and accountants.**
Ledger answers accounting and auditing questions by citing the relevant standards across **IFRS, AASB, US GAAP, and UK GAAP**, mapping each accounting standard to its **matching auditing standard(s)** (ISA / ASA / PCAOB / FRC ISA (UK)), and laying out the **risks, assertions, and procedures** an engagement team should consider.

> Status: design document. This describes the target architecture and the feature set; it is the contract the implementation builds against.

---

## 1. What Ledger does

A user (auditor, preparer, reviewer, student) asks a question in natural language. Ledger:

1. **Retrieves** the relevant passages from a curated, versioned corpus of standards.
2. **Generates** an answer grounded *only* in those passages, with **inline citations** down to the paragraph/clause level.
3. **Cross-references** the matching auditing standard for any accounting topic (and vice versa).
4. **Structures the audit response** — for the topic in question it surfaces the **risks of material misstatement**, the affected **financial-statement assertions**, and the **audit procedures** (tests of control / substantive / analytical) that address them.
5. **Refuses to answer beyond the corpus** — if the standards don't cover it, Ledger says so rather than inventing a citation.

### Example interaction

> **Q:** "How do I account for a sale-and-leaseback under IFRS, and what should the auditor test?"

> **A (shape):**
> - **Accounting treatment** — IFRS 16 *Leases*, paras 99–103 (transfer-of-asset test under IFRS 15) → cited.
> - **Equivalent standards** — AASB 16 (paras 99–103, verbatim adoption); ASC 842-40 (US GAAP — *different* model, failed-sale guidance); FRS 102 §20 (UK GAAP — finance vs operating lease, materially different).
> - **Risks** — overstated gain on disposal; off-balance-sheet financing; incorrect right-of-use asset measurement.
> - **Assertions** — Occurrence, Accuracy, Cut-off (gain); Rights & Obligations, Valuation (ROU asset).
> - **Procedures** — ISA 540 (estimates) for the ROU measurement; recompute the retained-interest gain; inspect the contract for the IFRS 15 control-transfer criteria; ISA 330 substantive response.
> - **Divergence flag** — "US GAAP outcome differs materially; do not assume IFRS treatment carries over."

---

## 2. Domain model

The product's value is the **knowledge graph linking standards to each other and to the audit response**. Retrieval feeds the LLM; the graph is what makes the answer *useful to an auditor*.

### 2.1 Corpus (the standards themselves)

| Framework | Body | Examples |
|---|---|---|
| **IFRS** | IASB | IFRS 15, IFRS 16, IAS 36, IAS 37 … |
| **AASB** | AASB (Australia) | AASB 15, AASB 16 — largely IFRS-aligned |
| **US GAAP** | FASB | ASC 606, ASC 842, ASC 350 … |
| **UK GAAP** | FRC | FRS 102, FRS 105 |
| **Auditing — international** | IAASB | ISA 315, ISA 330, ISA 540, ISA 500 … |
| **Auditing — Australia** | AUASB | ASA 315, ASA 330 … (ISA-aligned) |
| **Auditing — US** | PCAOB | AS 2301, AS 2110, AS 1105 … |
| **Auditing — UK** | FRC | ISA (UK) 315, ISA (UK) 330 … |

Each standard is decomposed into **paragraph-level chunks** (the atomic citable unit). A chunk carries: `framework`, `standard_id`, `paragraph_id`, `effective_date`, `supersedes`, `text`, `heading_path`, and `embedding`.

### 2.2 Linkage graph (the differentiator)

Three relationship types are authored/curated (not inferred at query time):

1. **Equivalence edges** — `IFRS 16 ¶99 ≈ AASB 16 ¶99` (verbatim) / `≈ ASC 842-40` (analogous, divergent) / `≈ FRS 102 §20` (partial). Each edge is tagged `verbatim | analogous | divergent | no_equivalent` so Ledger can warn when frameworks differ.
2. **Accounting→Auditing edges** — a topic in IFRS 16 maps to the auditing standards that govern how it's tested (ISA 540 for estimates, ISA 315 for risk ID, etc.).
3. **Risk/Assertion/Procedure (RAP) edges** — each topic links to curated `Risk`, `Assertion`, and `Procedure` nodes.

```
                         ┌──────────────┐
            equivalence  │  Standard    │  equivalence
        ┌───────────────▶│  Paragraph   │◀───────────────┐
        │                │  (chunk)     │                │
   AASB 16 ¶99           └──────┬───────┘          ASC 842-40
                                │ governs / tested-by
                                ▼
                         ┌──────────────┐
                         │ Audit Topic  │
                         └──┬────┬───┬──┘
                  addresses │    │   │ requires
              ┌─────────────┘    │   └─────────────┐
              ▼                  ▼                  ▼
         ┌─────────┐       ┌───────────┐      ┌────────────┐
         │  Risk   │──────▶│ Assertion │◀─────│ Procedure  │
         │ (RMM)   │ maps  │ (E/O/C/V/ │ tests│ (ToC/Subst │
         └─────────┘  to   │  P/A/CO)  │      │  /Analyt)  │
                           └───────────┘      └────────────┘
```

**Assertions** use the standard FS-assertion taxonomy: Existence/Occurrence, Completeness, Rights & Obligations, Valuation & Allocation, Accuracy, Cut-off, Classification, Presentation & Disclosure.

---

## 3. Feature set

### Core
- **Cross-framework citation** — every claim is backed by a paragraph-level citation; the UI renders the quoted source text on hover/expand.
- **Standard equivalence lookup** — "show me the US GAAP equivalent of IFRS 16" with a divergence flag.
- **Risk / Assertion / Procedure builder** — generates a structured audit-response table for a topic, exportable to a working paper.
- **Divergence warnings** — when an equivalence edge is `divergent`/`no_equivalent`, Ledger explicitly warns rather than implying carry-over.
- **Effective-date / version awareness** — answers respect the standard version in force for a stated reporting period ("as at FY2024").
- **Grounded refusal** — no corpus support → explicit "not covered" instead of a hallucinated citation.

### Workflow
- **Engagement context** — user states framework (e.g. IFRS + ISA), jurisdiction, and period; Ledger scopes retrieval accordingly.
- **Working-paper export** — RAP tables export to DOCX/XLSX (audit-file-ready).
- **Saved queries / memos** — citeable, reusable research memos.
- **Conversation memory** — multi-turn follow-ups retain engagement context.

### Trust & governance
- **Citation verifier** — a post-generation check that every citation resolves to a real chunk and the quoted text matches (anti-hallucination gate).
- **Audit log** — every Q→retrieved-context→answer→citations tuple is logged immutably for review/QA.
- **Confidence & coverage** — answers show retrieval coverage and flag low-confidence regions.
- **"Not advice" framing** — Ledger is a research aid; it surfaces standards, it does not sign opinions.

---

## 4. System architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Clients:  Web app  ·  IDE/Excel add-in  ·  REST API                 │
└───────────────────────────────┬─────────────────────────────────────┘
                                 │ HTTPS / JSON
                       ┌─────────▼──────────┐
                       │   API Gateway      │  auth, rate-limit, tenancy
                       └─────────┬──────────┘
                                 │
              ┌──────────────────┼──────────────────────┐
              ▼                  ▼                       ▼
     ┌────────────────┐ ┌─────────────────┐    ┌──────────────────┐
     │ Query Service  │ │ Ingestion Svc   │    │ Export Service   │
     │ (RAG orchestr.)│ │ (corpus build)  │    │ (DOCX/XLSX)      │
     └───┬────────┬───┘ └────────┬────────┘    └──────────────────┘
         │        │              │
         │        │              ▼
         │        │      ┌────────────────────────────────────────┐
         │        │      │ Corpus pipeline: parse → chunk →        │
         │        │      │ embed → link (RAP/equivalence) → index  │
         │        │      └────────────────────────────────────────┘
         │        │
         ▼        ▼
  ┌──────────┐ ┌─────────────────┐   ┌──────────────┐   ┌──────────────┐
  │ Vector   │ │ Knowledge graph │   │ Claude API   │   │ Postgres     │
  │ store    │ │ (equivalence +  │   │ (Opus 4.8 +  │   │ (metadata,   │
  │ (hybrid: │ │  RAP edges)     │   │  citations,  │   │  audit log,  │
  │ dense+   │ │                 │   │  structured  │   │  tenancy)    │
  │ BM25)    │ │                 │   │  outputs)    │   │              │
  └──────────┘ └─────────────────┘   └──────────────┘   └──────────────┘
```

### Component responsibilities

- **Query Service** — orchestrates the RAG loop: retrieve → rerank → assemble context → call Claude → verify citations → enrich with graph edges → return.
- **Ingestion Service** — turns source documents (standards PDFs/XML) into chunks, embeds them, and runs the linking pipeline. Versioned and idempotent.
- **Vector store** — hybrid retrieval (dense embeddings + BM25 lexical), since standards questions are full of exact terms ("right-of-use asset", "ASC 842-40") that lexical search nails and semantic search alone misses.
- **Knowledge graph** — stores equivalence and RAP edges; queried to enrich a retrieved chunk with its cross-framework equivalents and audit response.
- **Claude API** — generation, structured extraction, and grounded citation (details in §6).
- **Postgres** — tenancy, users, engagement context, saved memos, and the immutable audit log.

---

## 5. RAG pipeline (request lifecycle)

```
User question + engagement context (framework, jurisdiction, period)
        │
        ▼
[1] Query understanding ── classify intent (lookup / equivalence / RAP / open),
        │                   extract standard refs, normalise framework scope
        ▼
[2] Hybrid retrieval ───── dense + BM25 over the corpus, filtered by
        │                   framework scope + effective-date(period)
        ▼
[3] Rerank ─────────────── cross-encoder (or Claude-as-reranker for hard cases),
        │                   keep top-k paragraph chunks
        ▼
[4] Graph enrichment ───── for each retrieved chunk, pull equivalence edges
        │                   (other frameworks) + RAP edges (risks/assertions/procs)
        ▼
[5] Context assembly ───── build the prompt: system (frozen) + retrieved chunks
        │                   with stable IDs + graph context. Prompt-cache the
        │                   frozen system + standards preamble.
        ▼
[6] Generation ─────────── Claude Opus 4.8, native citations ON, adaptive thinking,
        │                   structured output for the RAP table
        ▼
[7] Citation verification  every citation resolves to a real chunk AND quoted
        │                   text matches source within tolerance; drop/flag if not
        ▼
[8] Response assembly ──── answer + citations + equivalence table + RAP table +
                            divergence warnings + coverage/confidence + audit-log write
```

Steps 1–5 are **code-orchestrated** (deterministic control flow). Only step 6 is the LLM call. This is a **workflow**, not an open-ended agent — we control the loop, which keeps answers auditable and reproducible.

---

## 6. Claude API integration

Ledger is LLM-shaped (RAG + grounded extraction). It uses the **Anthropic API** via the official SDK.

### Model & parameters
- **Model:** `claude-opus-4-8` (Claude Opus 4.8) — strongest grounding/citation fidelity and instruction-following, which matters when the cost of a fabricated citation is high. 1M context window lets us pack many full paragraphs of context.
  - For high-volume, latency-sensitive endpoints (e.g. autocomplete-style standard lookup), `claude-sonnet-4-6` is the cost/speed fallback. Model choice is per-endpoint, never silently downgraded.
- **Thinking:** adaptive — `thinking: {type: "adaptive"}`. Let the model reason harder on cross-framework divergence questions and lightly on simple lookups.
- **Effort:** `high` for the main answer path (correctness-sensitive); `medium`/`low` for lookup and reranking subcalls.
- **Streaming:** on for the answer endpoint (long, structured outputs) using `.get_final_message()` / `.finalMessage()` to avoid HTTP timeouts.
- **`max_tokens`:** ~16000 non-streaming, ~64000 streaming.

### Native citations (core feature)
Use the API's **document citations** feature: pass retrieved standards as `document` content blocks with `citations: {enabled: true}`. Claude returns citation spans that point back into the provided documents, so the model can only cite what we actually retrieved — citations are bounded by the corpus by construction. This is the primary anti-hallucination mechanism; the §5 step-7 verifier is the secondary backstop.

### Structured outputs
The RAP table and equivalence table are generated with **structured outputs** (`output_config.format` with a JSON schema) so the audit response is machine-parseable and export-ready — no fragile prose parsing. Schema covers: `risks[]`, `assertions[]`, `procedures[]` (each with `type: ToC|substantive|analytical` and the governing auditing standard), and `equivalences[]` (each with `framework`, `standard_ref`, `relation: verbatim|analogous|divergent|no_equivalent`).

### Prompt caching
The frozen system prompt (role, citation rules, assertion taxonomy, refusal policy) and any large stable preamble sit **before** the volatile retrieved context, with a `cache_control` breakpoint at the end of the stable prefix. Per-request retrieved chunks and the user question go *after* the breakpoint. No timestamps/UUIDs in the prefix. Verify via `usage.cache_read_input_tokens`.

### Multi-turn
Stateless API — the Query Service replays conversation history each turn, preserving engagement context. For long research sessions, enable **compaction** (`compact-2026-01-12`) and append full `response.content` each turn.

### Token counting
Use `client.messages.count_tokens` (never `tiktoken`) for cost estimation and context-budget checks before assembling oversized prompts.

---

## 7. Ingestion & corpus pipeline

```
Source (PDF / XML / authoritative text)
   │
   ├─ Parse ──────── layout-aware extraction; preserve heading hierarchy
   ├─ Chunk ──────── paragraph-level, the atomic citable unit; keep paragraph_id
   ├─ Embed ──────── dense vectors for semantic recall
   ├─ Link ───────── author/curate equivalence + accounting→auditing + RAP edges
   │                 (human-reviewed; this is the proprietary value)
   ├─ Version ─────── stamp effective_date / supersedes; never destructive
   └─ Index ──────── write to vector store + BM25 + knowledge graph
```

- **Licensing:** standards texts are copyrighted (IFRS Foundation, FASB, FRC, IAASB). Ledger must hold the appropriate license/subscription to ingest full text. Where full text can't be licensed, fall back to summaries + citation pointers (cite-and-link rather than reproduce).
- **Versioning is non-destructive** — superseded paragraphs are retained so "as at FY2022" questions retrieve the version then in force.
- **Curation tooling** — an internal console for SMEs (qualified auditors) to author and review equivalence/RAP edges. Edge quality is the moat; it is reviewed, not LLM-trusted.

---

## 8. Data model (selected tables)

```
standards(id, framework, standard_id, title, body, effective_date, supersedes_id)
chunks(id, standard_pk, paragraph_id, heading_path, text, embedding, effective_date)
equivalence_edges(from_chunk, to_chunk, relation, note, reviewed_by)
audit_topics(id, label, description)
topic_chunk(topic_id, chunk_id)            -- which standards govern a topic
risks(id, topic_id, description, rmm_level)
assertions(id, code, label)                -- E/O, C, R&O, V&A, A, CO, CL, P&D
procedures(id, topic_id, type, description, governing_audit_standard_chunk)
risk_assertion(risk_id, assertion_id)
procedure_assertion(procedure_id, assertion_id)
engagements(id, tenant_id, framework_scope, jurisdiction, period)
queries(id, engagement_id, question, retrieved_chunk_ids, answer, citations, created_at)
audit_log(id, query_id, prompt_hash, model, usage, immutable_ts)   -- append-only
```

---

## 9. Security, compliance & trust

- **Tenancy isolation** — per-tenant data partitioning; engagement data never crosses tenants.
- **Immutable audit log** — every answer is reproducible from its logged inputs (retrieved chunks + prompt hash + model + version). Critical for professional QA and peer review.
- **PII / client-data handling** — user-supplied engagement facts may contain client confidential data; encrypt at rest/in transit, support data-residency (esp. AASB/UK tenants), and never send client data to the LLM beyond what the user explicitly includes.
- **Grounded-refusal policy** — enforced in the system prompt *and* by the citation verifier. A claim with no resolvable citation is suppressed.
- **"Research aid, not assurance"** — explicit product framing; outputs are decision support for a qualified professional, not an audit opinion.
- **Model data retention** — configure Anthropic data-retention appropriately for professional-confidentiality obligations.

---

## 10. Evaluation

The accuracy bar is high — wrong standards guidance is worse than no answer.

- **Citation faithfulness** — % of citations that resolve and whose quoted text matches source (target: ~100%; the verifier enforces it).
- **Retrieval recall@k** — does the gold paragraph appear in the retrieved set? Measured against an SME-labelled question set.
- **Equivalence accuracy** — divergence calls (verbatim/analogous/divergent) judged against SME ground truth.
- **RAP completeness** — do generated risks/assertions/procedures match the SME-authored reference for the topic?
- **Refusal calibration** — out-of-corpus questions correctly refused, not hallucinated.
- **Adversarial set** — questions designed to elicit cross-framework carry-over errors (the most dangerous failure mode).

Eval runs use the Batches API (50% cost) for the labelled suite; results gate releases.

---

## 11. Tech stack (proposed)

| Layer | Choice | Why |
|---|---|---|
| LLM | Claude Opus 4.8 (Anthropic SDK) | citations, structured outputs, grounding |
| Backend | Python (FastAPI) | first-class Anthropic SDK, data tooling |
| Vector store | pgvector or a dedicated vector DB | hybrid dense+lexical |
| Lexical | Postgres FTS / OpenSearch BM25 | exact-term recall for standard refs |
| Graph | Postgres (relational edges) or a graph DB | equivalence + RAP edges |
| Metadata/audit | Postgres | tenancy, immutable log |
| Reranker | cross-encoder or Claude-as-reranker | precision on hard queries |
| Export | python-docx / openpyxl | working-paper output |
| Frontend | Web app + Excel/Office add-in | meets auditors where they work |

---

## 12. Roadmap

1. **M1 — Grounded Q&A (single framework).** IFRS + ISA. Corpus ingestion, hybrid retrieval, native citations, refusal, audit log. Proves citation fidelity.
2. **M2 — Cross-framework equivalence.** Add AASB, US GAAP, UK GAAP + equivalence graph + divergence warnings.
3. **M3 — Risk/Assertion/Procedure builder.** RAP graph + structured-output tables + working-paper export.
4. **M4 — Engagement context & memory.** Period/version awareness, multi-turn, saved memos.
5. **M5 — Office add-in & QA console.** Excel/Word integration; SME curation tooling at scale.

---

## 13. Key design decisions (and why)

- **Workflow, not agent.** Deterministic retrieve→generate→verify loop. Auditing demands reproducibility; an open-ended agent trajectory is harder to audit.
- **Curated linkage graph, not inferred-at-query-time.** Equivalence and RAP edges are SME-reviewed assets, not LLM guesses. This is the product's defensibility and its correctness guarantee.
- **Hybrid retrieval.** Standards questions mix exact terminology with conceptual intent — neither dense nor lexical alone suffices.
- **Native citations + verifier.** Two independent anti-hallucination layers, because a fabricated standard reference is a catastrophic failure in this domain.
- **Refuse over guess.** The corpus boundary is a hard wall.
