"use client";

import { useState } from "react";
import type { Citation } from "@/lib/types";

export function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-parchment/60 transition-colors hover:border-accent/40">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left"
      >
        <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-primary text-[11px] font-semibold text-primary-foreground">
          {index + 1}
        </span>
        <span className="flex min-w-0 flex-1 flex-col">
          <span className="truncate font-serif text-base leading-tight text-foreground">
            {citation.standard_id} <span className="text-muted-foreground">¶{citation.paragraph_id}</span>
          </span>
          <span className="truncate text-xs text-muted-foreground">{citation.heading_path}</span>
        </span>
        <span className="flex shrink-0 items-center gap-2">
          {citation.verified ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-accent/15 px-2 py-0.5 text-[11px] font-medium text-accent-foreground ring-1 ring-inset ring-accent/40">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5" /></svg>
              verified
            </span>
          ) : (
            <span className="rounded-full bg-destructive/10 px-2 py-0.5 text-[11px] font-medium text-destructive ring-1 ring-inset ring-destructive/30">
              unverified
            </span>
          )}
          <svg
            className={`text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`}
            width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          >
            <path d="m6 9 6 6 6-6" />
          </svg>
        </span>
      </button>
      {open && (
        <div className="border-t border-border/70 px-4 py-3">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {citation.framework} · source text
          </p>
          <blockquote className="mt-2 border-l-2 border-accent pl-3 font-serif text-[15px] leading-relaxed text-foreground/90">
            “{citation.quoted_text}”
          </blockquote>
        </div>
      )}
    </div>
  );
}
