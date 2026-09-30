# Retrieval index: BNS sections only; IPC via structured lookup

Status: accepted

Semantic retrieval runs over BNS section records from the GSMS-B structured dataset. IPC→BNS resolution uses a structured store keyed by IPC section number (and related fields), not vector search over mapping text. The Indian-Legal-QA JSONL corpus is reserved for offline evaluation and benchmark questions—it is never embedded or retrieved as evidence, to avoid elevating third-party Q&A into authoritative answers.
