export type Intent = "lookup" | "equivalence" | "rap" | "open";
export type Confidence = "low" | "medium" | "high";

export interface EngagementContext {
  frameworks: string[];
  jurisdiction?: string | null;
  period?: string | null;
}

export interface Citation {
  chunk_id: string;
  framework: string;
  standard_id: string;
  paragraph_id: string;
  heading_path: string;
  quoted_text: string;
  verified: boolean;
}

export interface RetrievedChunk {
  chunk_id: string;
  framework: string;
  standard_id: string;
  paragraph_id: string;
  heading_path: string;
  text: string;
  score: number;
}

export interface QueryResponse {
  query_id: string;
  intent: Intent;
  refused: boolean;
  answer: string;
  citations: Citation[];
  retrieved: RetrievedChunk[];
  coverage: number;
  confidence: Confidence;
  frameworks_in_scope: string[];
  not_advice: string;
}
