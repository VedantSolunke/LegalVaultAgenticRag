export type SectionCitation = {
  section_number: number;
  title: string;
  excerpt: string;
  act: string;
  ipc_section_number: number | null;
  mapping_source: string | null;
};

export type ResearchResponse = {
  query_mode: string;
  lead: string;
  body: string;
  citations: SectionCitation[];
  confidence: string;
  disclaimer: string;
  trace_id?: string | null;
};

export type RequestTrace = {
  query_mode: string;
  retrieval_query: string;
  retrieval_snapshot: Record<string, unknown>[];
  verification_outcome: string;
  latency_ms: number;
  confidence: string;
};

export type MeResponse = {
  user_id: string;
  is_admin: boolean;
};

export type ChatSession = {
  id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
};

export type SessionMessage = {
  id: string;
  session_id: string;
  role: string;
  body: string;
  created_at: string;
  research: ResearchResponse | null;
};
