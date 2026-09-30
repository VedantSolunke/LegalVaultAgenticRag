# Staged evaluation before users

Status: accepted

Quality gating is two-stage. While the operator is the only user, automated eval runs against a fixed question set derived from the QA JSONL (questions only—never as retrieval corpus) plus hand-written cases; failures are reviewed and retrieval or prompts are fixed, without a mandatory pass-rate threshold. Before the first invite-only trusted user is enabled, the same eval must meet explicit thresholds (e.g. high citation validity on section lookup and IPC mapping; fact-pattern judged with a separate, documented bar). Manual smoke tests remain useful but do not replace the automated report card for widening access.
