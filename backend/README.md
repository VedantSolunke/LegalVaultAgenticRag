# LegalVault backend — BNS research API

## Run locally

```bash
cd backend
uv sync --extra dev
uv run legalvault-api
```

## Tests

Integration tests hit the HTTP API with fixture corpus and stub providers (no live Gemini):

```bash
cd backend
uv sync --extra dev
uv run pytest
```
