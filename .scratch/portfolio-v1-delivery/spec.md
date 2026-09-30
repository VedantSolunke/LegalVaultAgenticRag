Status: ready-for-agent

# Portfolio V1 delivery

Align the running product with [ADR-0015](../../docs/adr/0015-portfolio-v1-scope.md) and [docs/portfolio-v1.md](../../docs/portfolio-v1.md): a recruiter-ready deployed demo, deterministic grounding for hero query modes, report-only offline eval in CI, and clear uncertainty for best-effort modes.

## Problem Statement

LegalVault’s architecture and documentation were originally framed like a small production legal product (staged eval gates, layered verification, invite-only access). The goal is now an **AI engineering portfolio**: a live URL, a readable repo, and a pipeline that demonstrates RAG, pgvector, LangGraph, and Gemini on the BNS corpus—without production-scale complexity blocking ship.

Gaps remain between that intent and day-to-day behavior: offline eval can fail when Supabase JWT verification is enabled locally; verification still applies LLM faithfulness to section comparison as well as fact-pattern analysis; CI does not yet run the eval suite; production ingest and deployment are not fully documented as a single “portfolio ship” path; secondary query modes can overclaim confidence relative to the glossary’s **best-effort query mode** definition.

## Solution

Deliver **Portfolio V1** as a cohesive milestone:

1. **Hero demos work reliably** on the real corpus: section lookup, IPC→BNS mapping, and at least one substantive fact-pattern example (with appropriate **confidence signal** and uncertainty when facts are thin).
2. **Evidence verification** matches ADR-0015: deterministic citation and section-number checks for all modes that cite the BNS; optional LLM faithfulness only for **fact-pattern analysis** (if enabled at all).
3. **Best-effort query modes** (legal concept, section comparison, general BNS information) compose answers that explicitly communicate limits—not reliable applicability analysis.
4. **Offline eval** runs in CI against the in-process research pipeline, prints pass-rate JSON, and does **not** fail the build on invite-gate thresholds; eval remains reliable even when developers have Supabase env vars in local `.env`.
5. **Deployment documentation** describes Vercel (web) + container API + Supabase (data/auth), including corpus ingest with live embeddings, env vars, and a short recruiter demo script (optional admin **debug trace** screenshot in README).
6. **Out of scope for this effort**: LangChain tool-calling refactor, enterprise retention/SLO work, widening corpus beyond ADR-0001, and making invite-gate thresholds CI blockers.

## User Stories

1. As a **recruiter**, I want to sign up with email on the public demo, so that I can try the product without asking the author for access.
2. As a **recruiter**, I want to ask for a BNS section by number and see statutory text with **citations**, so that I can judge grounding quality quickly.
3. As a **recruiter**, I want to ask what happened to an IPC section and see **IPC mapping** plus linked BNS **section records**, so that I understand structured + generative retrieval.
4. As a **recruiter**, I want to describe a short fact pattern and get a **research response** with explicit uncertainty when facts are incomplete, so that I do not mistake the assistant for legal advice or certainty.
5. As a **registered user**, I want a disclaimer visible in the chat experience, so that I understand this is **legal research assistant** software, not representation.
6. As a **registered user**, I want **chat sessions** with follow-up context within a short window, so that I can refine a question without starting over.
7. As a **registered user**, I want **citations** I can expand or scan, so that I can verify claims against the **BNS corpus**.
8. As a **registered user**, I want a **confidence signal** on responses, so that I know when the system is weakly tied to evidence.
9. As a **registered user** asking a **best-effort query mode** question, I want language that states limits and uncertainty, so that I am not led to believe the system performed reliable applicability analysis.
10. As a **registered user** asking about **out of corpus** material (e.g. BNSS), I want a clear refusal without fabricated citations, so that scope boundaries are trustworthy.
11. As the **project owner**, I want the live stack on Vercel + hosted API + Supabase, so that the README link works for hiring managers.
12. As the **project owner**, I want BNS **section records** ingested into pgvector with production embeddings, so that hybrid retrieval is real—not fixture-only.
13. As the **project owner**, I want IPC **mapping records** ingested for structured lookup, so that IPC→BNS demos use curated data per ADR-0004.
14. As the **project owner**, I want Gemini (or configured LLM provider) for composition on deployed API, so that answers are not stub text in production.
15. As the **project owner**, I want local development via Docker Compose Postgres and documented Supabase-or-dev-token auth, so that contributors can run the stack without production secrets.
16. As the **project owner**, I want `legalvault-eval` to run in CI and emit a JSON report, so that regressions in retrieval/citation validity are visible in every PR.
17. As the **project owner**, I want CI **not** to fail on invite-gate thresholds, so that portfolio velocity is not blocked by ADR-0013 operator gates.
18. As the **project owner**, I want to run `legalvault-eval --check-invite-gate` manually before demos, so that I can self-enforce quality when it matters.
19. As the **project owner**, I want the offline eval question set to cover hero modes (section lookup, IPC mapping, fact-pattern, out-of-corpus), so that the report card matches what I demo.
20. As the **project owner**, I want in-process eval to work regardless of local Supabase JWT configuration, so that `uv run legalvault-eval` is dependable on my laptop.
21. As an **admin user**, I want to view **debug trace** detail for a request, so that I can explain retrieval and verification in an interview.
22. As a **registered user**, I must not see **debug trace** UI by default, so that the product stays polished for external viewers.
23. As the **project owner**, I want substantive claims in hero modes to require **retrieved evidence** (ADR-0005), so that the portfolio story about grounding is honest.
24. As the **project owner**, I want verification to strip or refuse answers when cited sections are not in **retrieved evidence**, so that hallucinated section numbers do not ship.
25. As the **project owner**, I want section comparison to pass deterministic verification without mandatory LLM faithfulness, so that ADR-0015 layer-one behavior matches code.
26. As the **project owner**, I want fact-pattern verification to use deterministic checks always, with optional LLM faithfulness behind a clear switch or mode guard, so that complexity stays optional.
27. As a **CI system**, I want backend tests and eval to run without external Google API keys where stubs suffice, so that PR checks are fast and free.
28. As the **project owner**, I want README and portfolio docs to list deployment env vars and demo steps, so that I can onboard interviewers in one page.
29. As a **registered user**, I want session messages persisted with **redacted message** storage where implemented, so that obvious PII patterns are not stored verbatim (light mention; no new retention product).
30. As the **project owner**, I want the GitHub repo structure (backend graph, ingest CLIs, web chat) to remain explainable in a whiteboard interview, so that I am not ashamed of accidental over-engineering.

## Implementation Decisions

### Testing seam (proposed)

Use a **single external behavior seam** for acceptance of the research pipeline:

- **Primary:** the same entry point the API uses to produce a **research response** (structured payload with `query_mode`, `lead`, `body`, `citations`, `confidence`, `verification_outcome`)—whether reached via authenticated HTTP in tests or via a thin in-process wrapper used only by the eval CLI.

Prefer reusing the existing graph runner behind the API rather than adding parallel pipelines. Offline eval should not depend on Supabase JWT being disabled; it should either override auth in test app configuration or call the shared runner with fixture **section corpus** and mapping store (matching current fixture-based tests).

Confirm with the maintainer that this seam matches expectations before implementation.

### Research pipeline and verification

- Align `verify_evidence` with ADR-0015: deterministic **evidence verification** (citations and prose section numbers ⊆ **retrieved evidence**) for all modes that emit BNS citations.
- Restrict LLM faithfulness (`check_faithfulness`) to **fact-pattern analysis** only, gated so it can be disabled entirely for simpler deployments.
- **Section comparison** uses deterministic checks only; failures produce the existing refusal **research response** pattern or downgrade **confidence signal** per existing graph conventions—no new verification subsystem.
- Preserve existing LangGraph node sequence: classify → retrieve mappings → retrieve sections → compose → verify.

### Query modes and UX copy

- **Core demo modes:** section lookup, IPC→BNS mapping, fact-pattern analysis (including thin-facts behavior via existing `facts_are_thin` logic).
- **Best-effort query modes:** adjust composition prompts or post-compose copy so **legal concept lookup**, **section comparison**, and **general BNS information** responses include explicit uncertainty/limit language (glossary: **best-effort query mode**).
- Do not add new query modes; refine behavior and copy within the existing classifier.

### Offline evaluation

- Add a CI job step: run `legalvault-eval` without `--check-invite-gate`.
- Policy per ADR-0015: CI may fail on eval case failures (exit code 1) **or** may treat eval as report-only (always exit 0 except missing questions file)—**default recommendation:** fail CI when any eval case fails, but never on invite-gate alone; document the choice in eval-quality-gate doc.
- Fix `InProcessResearchClient` (or replace with direct runner invocation) so eval does not 401 when `LEGALVAULT_SUPABASE_URL` is set locally.
- Extend `backend/eval/questions.json` if needed with at least one **fact-pattern** case that expects citations when facts are sufficient (alongside existing thin-fact case).

### Deployment and configuration

- Document production checklist: Supabase SQL migrations for sessions/profiles/traces; `LEGALVAULT_CORPUS_BACKEND=postgres`; ingest BNS + IPC mapping with live embedding provider; API CORS for Vercel origin; web public Supabase keys and `NEXT_PUBLIC_SITE_URL`.
- Keep Docker Compose scoped to local Postgres; API container image already exists—document Railway/Fly-style deploy without mandating a specific vendor.
- Do not implement multi-region, autoscaling, or failover.

### Auth and access

- Public email signup remains the deployed default (ADR-0014); RLS on Supabase as today.
- Dev/test bearer tokens remain for local and in-process eval when JWT verification is off.
- **Admin user** debug traces unchanged; optional README screenshot.

### Persistence

- No schema changes required unless deploy uncovers gaps; reuse session/message/trace tables per ADR-0008.
- No new retention automation.

### Explicitly deferred

- LangChain retrieval **tool calling** in the graph.
- Invite-gate as merge/deploy blocker.
- Second-layer verification for section comparison.
- Case law or corpus expansion.

## Testing Decisions

**Principle:** Test observable **research response** behavior and HTTP status codes, not internal graph node order or private helpers—except where small pure functions (citation support, section number extraction) already have unit tests.

**Modules / surfaces**

- Existing `pytest` API tests (research, sessions, auth) with `test-user-token` headers—prior art in `backend/tests/test_research_*.py`, `test_auth.py`.
- Graph-level tests where they already assert mode, citations, and verification outcomes—extend for verification policy change (comparison vs fact-pattern).
- Eval runner: `test_eval_runner.py` and `test_eval_load_questions.py`; add coverage that in-process eval completes without Supabase when using fixture corpus seam.
- CI workflow: new step under `backend-tests` job after `pytest` (or combined) running `uv run legalvault-eval` with env that disables Supabase JWT for the test app if HTTP path is kept.

**Good tests**

- Given a fixture corpus query, response includes expected `query_mode`, minimum citations, and required section numbers.
- Given thin fact-pattern query, response respects max citation expectations and low confidence.
- Given out-of-corpus query, zero citations and appropriate mode.
- Verification: cited section not in retrieved set → refusal or stripped citations (behavior already partially covered—extend for comparison faithfulness removal).

**Bad tests**

- Asserting LangGraph node invocation order.
- Snapshotting full LLM prose from live Gemini in CI.

## Out of Scope

- LangChain tool-calling agent refactor.
- Production-scale observability, SLOs, rate limiting beyond basic API hosting defaults.
- Mandatory `--check-invite-gate` in CI or deploy pipelines.
- Full LLM-judged answer quality evaluation.
- HITL, multi-agent orchestration, or new vector databases.
- Mobile apps, billing, org/tenant features.
- Rewriting ADR history; only implement ADR-0015 alignment in code and ops docs.

## Further Notes

- Canonical product vocabulary: root `GLOSSARY.md` (**registered user**, **research response**, **retrieved evidence**, **best-effort query mode**).
- Portfolio narrative lives in `docs/portfolio-v1.md`; this spec is the implementation backlog for that doc.
- If CI eval flakiness appears with live LLM providers, keep CI on stub LLM with fixture corpus and document live eval as a manual pre-demo command against staging API (`--api-url`).
