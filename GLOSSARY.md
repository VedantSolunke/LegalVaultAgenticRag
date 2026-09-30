# LegalVault Agentic RAG

Domain language for the Indian legal research assistant: BNS-focused, source-grounded, agent-orchestrated retrieval—not legal advice.

## Corpus scope

**BNS corpus**:
The in-scope body of Bharatiya Nyaya Sanhita, 2023 material the system may cite and explain in substantive answers.

_Avoid_: Knowledge base, legal database (when meaning only BNS)

**Out of corpus**:
Any legal material outside the current product scope (e.g. BNSS, BSA, case law, non-Indian law). Queries that need it get an explicit refusal, not a best-effort answer.

_Avoid_: Out of scope (too generic)

**IPC mapping**:
A curated link between an Indian Penal Code, 1860 section and one or more BNS sections, stored as data—not inferred by the model.

_Avoid_: IPC conversion, legacy mapping (without “IPC”)

## Statutory units

**Section**:
One numbered unit of the BNS (including its title and subsections) identified by section number and act.

_Avoid_: Provision (use only when quoting generic legal English, not as the primary UI label)

**Citation**:
A pointer from an answer claim to a specific corpus record (section text or IPC mapping row) the user can verify.

_Avoid_: Reference, source link (when meaning statutory citation)

## Query handling

**Query mode**:
The classified intent of a user message: section lookup, legal concept lookup, fact-pattern analysis, IPC-to-BNS mapping, comparison, or general BNS information within corpus.

_Avoid_: Intent type, query class

**Fact-pattern analysis**:
A query where the user describes circumstances in natural language and asks which BNS sections may be relevant, with uncertainty when facts are incomplete.

_Avoid_: Situation-to-law (informal)

**Best-effort query mode**:
Legal concept lookup, section comparison, or general BNS information within corpus—supported when retrieval helps, but the research response must state limits and uncertainty rather than imply reliable applicability analysis.

_Avoid_: Secondary mode (informal)

## Product boundaries

**Legal research assistant**:
Software that retrieves and explains authoritative corpus material with traceable reasoning; it does not provide legal advice, representation, or autonomous legal action.

_Avoid_: Legal chatbot, legal AI lawyer

**Research response**:
The user-facing answer: short plain-language lead, professional detail (citations, conditions, exceptions), and explicit uncertainty where facts are insufficient.

_Avoid_: Chat reply, completion

## Retrieval and evidence

**Section record**:
One indexed BNS section from the structured corpus (identifier, number, title, chapter, statutory text) used as the unit of vector search and citation.

_Avoid_: Chunk, document (when meaning a BNS section)

**Mapping record**:
One row linking an IPC section to one or more BNS section records, tagged with which curated dataset supplied the link.

_Avoid_: Mapping entry, transform row

**Retrieved evidence**:
The set of section records (and mapping records when relevant) passed into answer generation after search and ranking; substantive claims must be supported by this set.

_Avoid_: Context, RAG context

**Evidence verification**:
The check that blocks or revises a draft research response when citations or stated BNS section numbers are not supported by retrieved evidence.

_Avoid_: Guardrail pass, fact check (generic)

## Sessions and observability

**Chat session**:
A short-lived conversation window (roughly five to ten turns) used for follow-up questions; not a long-term legal matter file.

_Avoid_: Thread, conversation (when meaning persisted legal workspace)

**Debug trace**:
The full request trail (query mode, rewrites, retrieval hits, verification, model steps) visible only to operators or admin users, not the default lawyer view.

_Avoid_: Logs, LangSmith trace (product names)

**Confidence signal**:
User-visible indication of how strongly the system ties its answer to retrieved evidence and complete facts (e.g. high / medium / low, or explicit “insufficient facts”).

_Avoid_: Score, probability

## Access and privacy

**Registered user**:
A person with a Supabase account who can use the deployed chat demo (email signup on the portfolio instance).

_Avoid_: Beta user, tester (ambiguous)

**Admin user**:
A registered user whose profile is marked to view debug traces and operator detail; default users see citations and confidence only.

_Avoid_: Superuser, root

**Redacted message**:
The copy of user text stored and traced after automated removal of obvious PII patterns; used for persistence and logs while session follow-ups still work on the live request path.

_Avoid_: Anonymized query (implies stronger guarantees than v1 provides)

**Eval question set**:
Offline test questions (including samples from the QA JSONL) used to score retrieval and citations; never embedded or retrieved during live answers.

_Avoid_: Test corpus, golden dataset (when confused with production index)
