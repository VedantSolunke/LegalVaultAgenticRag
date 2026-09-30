# Layered evidence verification

Status: accepted (layer two optional per ADR-0015)

Verification runs in two layers before a research response ships: (1) deterministic gates—every cited BNS section must be in retrieved evidence; IPC mapping claims must match ingested mapping rows; (2) an LLM faithfulness check on modes that produce free-form legal prose (fact-pattern analysis and section comparison), with regenerate or refuse if support is weak. Section lookup and IPC map responses lean on layer one.

Portfolio V1 requires layer one only; layer two may be added for fact-pattern analysis as an optional demo feature, not a full verification subsystem.
