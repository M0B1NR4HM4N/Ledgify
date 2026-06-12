"use client";

import { useEffect, useState } from "react";
import { askLedger, getHealth, type Health } from "@/lib/api";
import type { EngagementContext, QueryResponse } from "@/lib/types";
import { QueryConsole } from "@/components/QueryConsole";
import { AnswerPanel } from "@/components/AnswerPanel";

export default function Home() {
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  async function handleAsk(question: string, engagement: EngagementContext) {
    setLoading(true);
    setError(null);
    try {
      setResult(await askLedger(question, engagement));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative mx-auto flex min-h-screen max-w-3xl flex-col px-5 sm:px-6">
      {/* Logo — pinned to the top-left corner */}
      <div className="fixed left-5 top-5 z-50 flex items-center gap-2.5 sm:left-6 sm:top-6">
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-primary-foreground">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
        </span>
        <span className="font-serif text-2xl tracking-tight text-foreground">Ledger</span>
      </div>

      {/* Hero — centered */}
      <section className="flex flex-col items-center pb-8 pt-24 text-center sm:pt-28">
        <span className="mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-card/50 px-3 py-1 text-[11px] text-muted-foreground">
          <span className="rounded-full bg-secondary px-1.5 py-0.5 font-medium text-secondary-foreground">M1</span>
          Grounded Q&A
          {health && (
            <>
              <span className="text-border">·</span>
              <span className={`h-1.5 w-1.5 rounded-full ${health.generation !== "offline-stub" ? "bg-accent" : "bg-muted-foreground"}`} />
              {health.generation === "offline-stub" ? "offline stub" : health.answer_model}
            </>
          )}
        </span>
        <h1 className="font-serif text-[2.7rem] leading-[1.05] tracking-tight text-foreground sm:text-6xl">
          Answers, with the
          <br />
          <span className="text-accent">standard cited.</span>
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-[15px] leading-relaxed text-muted-foreground">
          A retrieval-augmented assistant for auditors and accountants. Every claim is
          grounded in IFRS &amp; ISA down to the paragraph — and if the corpus doesn&apos;t
          cover it, Ledger says so rather than inventing a citation.
        </p>
      </section>

      {/* Console */}
      <QueryConsole onAsk={handleAsk} loading={loading} />

      {/* Results */}
      <main className="flex-1 py-8">
        {error && (
          <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-5 text-sm text-destructive">
            <p className="font-medium">Couldn&apos;t reach the Query Service.</p>
            <p className="mt-1 text-destructive/80">{error}</p>
            <p className="mt-2 text-xs text-muted-foreground">
              Is the backend running on <code className="font-mono">:8000</code>? Start it with{" "}
              <code className="font-mono">cd backend &amp;&amp; ./run.sh</code>.
            </p>
          </div>
        )}
        {result && !error && <AnswerPanel data={result} />}
        {!result && !error && !loading && (
          <div className="rounded-2xl border border-dashed border-border bg-card/30 p-10 text-center">
            <p className="font-serif text-lg text-foreground/80">Ask a question to begin</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {health
                ? `${health.corpus_chunks} paragraphs indexed · ${health.frameworks.join(", ")}`
                : "Connecting to the corpus…"}
            </p>
          </div>
        )}
      </main>

      <footer className="border-t border-border/60 py-6 text-center text-xs text-muted-foreground">
        Research aid — surfaces standards, not an audit opinion. Citations are verified
        against source text before display.
      </footer>
    </div>
  );
}
