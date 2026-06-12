import type { EngagementContext, QueryResponse } from "./types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export async function askLedger(
  question: string,
  engagement: EngagementContext,
): Promise<QueryResponse> {
  const res = await fetch(`${API_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, engagement }),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Query failed (${res.status}). ${detail}`);
  }
  return res.json();
}

export interface Health {
  status: string;
  milestone: string;
  corpus_chunks: number;
  frameworks: string[];
  generation: string;
  answer_model: string;
}

export async function getHealth(): Promise<Health> {
  const res = await fetch(`${API_URL}/api/health`, { cache: "no-store" });
  if (!res.ok) throw new Error("health check failed");
  return res.json();
}
