"use client";

import type { Confidence, QueryResponse } from "@/lib/types";
import { CitationCard } from "./CitationCard";

const CONFIDENCE_STYLE: Record<Confidence, string> = {
  high: "bg-accent/15 text-accent-foreground ring-accent/40",
  medium: "bg-secondary text-secondary-foreground ring-border",
  low: "bg-muted text-muted-foreground ring-border",
};

function MetaPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</span>
      <span className="font-serif text-lg leading-tight text-foreground">{value}</span>
    </div>
  );
}

export function AnswerPanel({ data }: { data: QueryResponse }) {
  if (data.refused) {
    return (
      <div className="animate-rise rounded-2xl border border-destructive/30 bg-card/80 p-6 shadow-sm backdrop-blur-sm">
        <div className="flex items-center gap-2 text-destructive">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" /></svg>
          <h3 className="font-serif text-xl">Outside the corpus</h3>
        </div>
        <p className="mt-3 text-[15px] leading-relaxed text-foreground/90">{data.answer}</p>
        <p className="mt-4 text-xs text-muted-foreground">
          Refuse over guess — the corpus boundary is a hard wall. No citation, no answer.
        </p>
      </div>
    );
  }

  return (
    <div className="animate-rise space-y-5">
      {/* Answer */}
      <div className="rounded-2xl border border-border bg-card/80 p-6 shadow-sm backdrop-blur-sm sm:p-7">
        <div className="mb-4 flex flex-wrap items-center gap-x-6 gap-y-3 border-b border-border/70 pb-4">
          <MetaPill label="Intent" value={data.intent} />
          <MetaPill label="Coverage" value={`${Math.round(data.coverage * 100)}%`} />
          <MetaPill label="Scope" value={data.frameworks_in_scope.join(" · ")} />
          <span
            className={`ml-auto rounded-full px-3 py-1 text-xs font-medium uppercase tracking-wide ring-1 ring-inset ${CONFIDENCE_STYLE[data.confidence]}`}
          >
            {data.confidence} confidence
          </span>
        </div>
        <div className="space-y-3 whitespace-pre-wrap text-[15.5px] leading-relaxed text-foreground/90">
          {data.answer}
        </div>
      </div>

      {/* Citations */}
      {data.citations.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 px-1 text-sm font-medium text-muted-foreground">
            <span className="font-serif text-base text-foreground">Citations</span>
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs">{data.citations.length}</span>
          </h3>
          <div className="space-y-2">
            {data.citations.map((c, i) => (
              <CitationCard key={`${c.chunk_id}-${i}`} citation={c} index={i} />
            ))}
          </div>
        </div>
      )}

      {/* Retrieval trace */}
      {data.retrieved.length > 0 && (
        <details className="group rounded-2xl border border-border bg-card/50 px-5 py-4">
          <summary className="flex cursor-pointer list-none items-center justify-between text-sm text-muted-foreground">
            <span className="font-serif text-base text-foreground">Retrieval trace</span>
            <span className="text-xs">{data.retrieved.length} chunks · hybrid BM25 + dense (RRF)</span>
          </summary>
          <ul className="mt-3 space-y-1.5">
            {data.retrieved.map((r) => (
              <li key={r.chunk_id} className="flex items-center gap-3 text-sm">
                <span className="w-28 shrink-0 font-mono text-xs text-muted-foreground">{r.standard_id} ¶{r.paragraph_id}</span>
                <span className="truncate text-foreground/80">{r.heading_path.split(" > ").slice(-1)[0]}</span>
                <span className="ml-auto shrink-0 font-mono text-xs text-accent-foreground/70">{r.score.toFixed(4)}</span>
              </li>
            ))}
          </ul>
        </details>
      )}

      <p className="px-1 text-xs text-muted-foreground">{data.not_advice}</p>
    </div>
  );
}
