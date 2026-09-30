# V1 application stack

Status: accepted

v1 ships as FastAPI (uv) with LangGraph orchestration in-process, Next.js frontend, Supabase Postgres with pgvector for section embeddings and app data, and Google Gemini (Flash-class) for generation. Embeddings use a free-tier Google embedding model (e.g. `text-embedding-004`) with the same API billing guardrails as the chat model. This is a deliberate small-deployment monolith: swapping orchestration or host later is possible but would touch most of the AI pipeline.
