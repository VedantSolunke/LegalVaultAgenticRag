# Eval quality gate (ADR-0013)

LegalVault widens access in two stages. While the operator is the only user, eval failures are reviewed manually and there is **no mandatory pass-rate gate**. Before the first invite-only trusted user is enabled, the same offline eval must meet explicit thresholds.

## Question set

- Hand-written cases: `backend/eval/questions.json` (checked into the repo; safe to run in CI with the fixture corpus).
- Optional QA JSONL samples: pass `--jsonl /path/to/questions.jsonl` to `legalvault-eval`. Only the `question` / `query` field is used; answers and QA corpora are **never** ingested or embedded (see ADR-0003).

## Run the eval CLI

In-process (default; uses fixture corpus and stub providers):

```bash
cd backend
uv sync --extra dev
uv run legalvault-eval
```

Against a running API:

```bash
uv run legalvault-eval \
  --api-url http://localhost:8000 \
  --token test-user-token
```

Optional QA JSONL merge:

```bash
uv run legalvault-eval --jsonl /path/to/indian-legal-qa.jsonl
```

Fail the command when invite-gate thresholds are not met (for CI before inviting users):

```bash
uv run legalvault-eval --check-invite-gate
```

Exit codes: `0` all cases passed (and gate passed when requested), `1` case failures, `2` invite-gate failure with `--check-invite-gate`.

## Threshold configuration

File: `backend/eval/thresholds.json`

| Key | Default | Meaning |
|-----|---------|---------|
| `min_overall_pass_rate` | `0.9` | Minimum fraction of eval cases that must pass |
| `section_lookup_min_pass_rate` | `0.95` | Pass rate floor for `section_lookup` cases |
| `ipc_mapping_min_pass_rate` | `0.95` | Pass rate floor for `ipc_to_bns_mapping` cases |
| `fact_pattern_min_pass_rate` | `0.7` | Pass rate floor for `fact_pattern_analysis` cases |

Adjust these values as the corpus and prompts mature. The eval report JSON includes per-case metrics (`query_mode`, citation counts, cited section numbers) for debugging retrieval regressions.

## Metrics reported

Each case records:

- Expected vs actual `query_mode`
- Citation count vs min/max bounds
- Required BNS section numbers and IPC numbers present in citations
- Minimum confidence when specified

These are **retrieval/citation validity** checks, not LLM-judged answer quality. Fact-pattern cases use a separate, lower bar documented above.
