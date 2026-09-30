# Portfolio V1 scope

Status: accepted

LegalVault is an AI engineering portfolio project, not a production-scale commercial product. V1 optimizes for a deployable demo recruiters can try, a readable GitHub repo, and credible use of Python, RAG, pgvector, LangChain/LangGraph, and Gemini—not multi-tenant SLOs, elaborate eval gates, or enterprise operations.

**Access:** Public email signup on the deployed instance (ADR-0014). Supabase Auth with basic RLS. Local dev uses documented bearer-token or Supabase env setup in the README.

**Hosting:** Next.js on Vercel; FastAPI + LangGraph on container hosting (e.g. Railway or Fly); Supabase for Postgres, pgvector, auth, and session data. Docker Compose is for local development only.

**Orchestration:** Ship the existing linear LangGraph pipeline first. Explicit LangChain tool calling is optional follow-up (one retrieval tool) and must not block deployment.

**Verification:** V1 relies on deterministic evidence checks—citations and section numbers in the answer must be supported by retrieved evidence (ADR-0005). A single optional LLM faithfulness check for fact-pattern analysis is allowed as a demo talking point; no layered verification subsystem (ADR-0011 layer two is not a V1 requirement).

**Evaluation:** Run `legalvault-eval` in CI and publish pass metrics. Invite-gate thresholds (ADR-0013) are not merge or deployment blockers; run `--check-invite-gate` manually before important demos or releases.

**Observability:** Admin debug traces (ADR-0009) are operator-only for development and interviews, not a end-user feature.

**Demo reliability:** Section lookup, IPC→BNS mapping, and at least one strong fact-pattern example are core demo paths. Legal concept lookup, section comparison, and general BNS information are secondary: responses must state uncertainty rather than imply reliable applicability analysis.
