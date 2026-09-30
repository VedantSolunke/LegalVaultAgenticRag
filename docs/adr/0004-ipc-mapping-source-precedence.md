# IPC mapping source precedence

Status: accepted

IPC→BNS links are ingested from two Hugging Face datasets with explicit precedence: `jbp123/bns` is primary (comparative-table style); `nandhakumarg/IPC_and_BNS_transformation` fills gaps only when primary has no row for that IPC section. Every mapping record stores which source supplied it so citations and debug traces can show provenance. The model must not invent or adjust mapping links beyond these records.
