# PII redaction before persist

Status: accepted

Before user messages are written to Supabase (and before trace payloads are stored long-term), the pipeline applies lightweight pattern-based redaction for obvious PII such as phone numbers and email addresses. The live turn may still use the original text for retrieval quality within the session; stored history and traces use the redacted form. This is not a guarantee of anonymity—users are still told the product is not for substituting professional advice.
