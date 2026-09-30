# V1 statutory text from GSMS-B structured dataset

Status: accepted

For speed to first useful results, v1 treats `GSMS-B/indian-legal-sections-bns-bnss-bsa-2023` (BNS rows only at query time) as the canonical statutory text for embedding, retrieval, and display. The MHA PDF remains an audit and reconciliation source, not a blocking ingestion dependency. Before marketing citations as fully authoritative, we run a section alignment check (number, title, optional text diff) against the PDF and fix or flag mismatches. IPC mapping rows cite the chosen mapping dataset plus the linked BNS section records, never model-invented links.

**Considered options**: PDF-first extraction (slower pipeline); merged dual-text records on day one (more engineering before any user sees results).
