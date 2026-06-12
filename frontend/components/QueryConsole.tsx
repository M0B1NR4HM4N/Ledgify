"use client";

import { useState } from "react";
import type { EngagementContext } from "@/lib/types";

const FRAMEWORKS = ["IFRS", "ISA"]; // M1 scope (single framework set)

const EXAMPLES = [
  "How do I account for a sale and leaseback under IFRS 16, and what should the auditor test?",
  "When is revenue recognised over time under IFRS 15?",
  "How is the recoverable amount measured for impairment under IAS 36?",
  "What audit procedures address accounting estimates?",
];

export function QueryConsole({
  onAsk,
  loading,
}: {
  onAsk: (question: string, engagement: EngagementContext) => void;
  loading: boolean;
}) {
  const [question, setQuestion] = useState("");
  const [frameworks, setFrameworks] = useState<string[]>([...FRAMEWORKS]);
  const [period, setPeriod] = useState("");

  function toggle(fw: string) {
    setFrameworks((prev) =>
      prev.includes(fw) ? prev.filter((f) => f !== fw) : [...prev, fw],
    );
  }

  function submit(q?: string) {
    const text = (q ?? question).trim();
    if (!text || loading) return;
    if (q) setQuestion(q);
    onAsk(text, {
      frameworks: frameworks.length ? frameworks : [...FRAMEWORKS],
      period: period.trim() || null,
    });
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-border bg-card/80 p-2 shadow-sm backdrop-blur-sm transition-shadow focus-within:border-accent/60 focus-within:shadow-md">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
          }}
          rows={3}
          placeholder="Ask about a standard — e.g. the auditor's response to a sale-and-leaseback…"
          className="w-full resize-none bg-transparent px-4 py-3 font-serif text-lg text-foreground placeholder:text-muted-foreground/70 focus:outline-none"
        />
        <div className="flex flex-wrap items-center gap-2 px-2 pb-1.5 pt-1">
          <span className="text-xs text-muted-foreground">Scope</span>
          {FRAMEWORKS.map((fw) => {
            const active = frameworks.includes(fw);
            return (
              <button
                key={fw}
                onClick={() => toggle(fw)}
                className={`rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset transition-colors ${
                  active
                    ? "bg-primary text-primary-foreground ring-transparent"
                    : "bg-transparent text-muted-foreground ring-border hover:text-foreground"
                }`}
              >
                {fw}
              </button>
            );
          })}
          <input
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            placeholder="period (e.g. FY2024)"
            className="w-40 rounded-full bg-input/60 px-3 py-1 text-xs text-foreground placeholder:text-muted-foreground/70 ring-1 ring-inset ring-border focus:outline-none focus:ring-accent/50"
          />
          <button
            onClick={() => submit()}
            disabled={loading || !question.trim()}
            className="ml-auto inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? (
              <>
                <svg className="animate-spin" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <path d="M21 12a9 9 0 1 1-6.22-8.56" />
                </svg>
                Retrieving
              </>
            ) : (
              <>
                Ask Ledger
                <span className="text-[11px] opacity-70">⌘↵</span>
              </>
            )}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap justify-center gap-2">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => submit(ex)}
            disabled={loading}
            className="rounded-full border border-border bg-parchment/50 px-3 py-1.5 text-left text-xs text-muted-foreground transition-colors hover:border-accent/50 hover:text-foreground disabled:opacity-50"
          >
            {ex.length > 58 ? ex.slice(0, 58) + "…" : ex}
          </button>
        ))}
      </div>
    </div>
  );
}
