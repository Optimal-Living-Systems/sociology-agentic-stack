# Kestra Flow Integration

This folder contains Kestra flows for orchestrating the OLS sociology stack.

## Files
- `flows/research_session.yaml`: End-to-end run (session -> review -> archive)
- `flows/corpus_ingest.yaml`: Corpus ingestion trigger scaffold
- `Dockerfile`: Custom Kestra image with `requirements.lock` preinstalled

## Prerequisites
- Kestra server running (Docker is acceptable)
- Kestra API reachable (default `http://localhost:8080`)
- Local repo path exists at `/home/joel/work/sociology-agentic-stack`
- API auth credentials available (default local dev: `admin@kestra.io` / `Kestra123`)

## Initialize auth (one-time per fresh Kestra DB)

```bash
curl -sS -X POST "http://localhost:8080/api/v1/main/basicAuth" \
  -H "Content-Type: application/json" \
  -d '{"uid":"ols-dev-bootstrap","username":"admin@kestra.io","password":"Kestra123"}'
```

## Install flows into Kestra

```bash
# Import research session flow
curl -sS -X POST "http://localhost:8080/api/v1/main/flows/import" \
  -u "admin@kestra.io:Kestra123" \
  -H "Content-Type: multipart/form-data" \
  -F "fileUpload=@kestra/flows/research_session.yaml"

# Import corpus ingest flow
curl -sS -X POST "http://localhost:8080/api/v1/main/flows/import" \
  -u "admin@kestra.io:Kestra123" \
  -H "Content-Type: multipart/form-data" \
  -F "fileUpload=@kestra/flows/corpus_ingest.yaml"
```

## Trigger a run from CLI

```bash
curl -sS -X POST "http://localhost:8080/api/v1/main/executions/ols.research/sociology-research-session" \
  -u "admin@kestra.io:Kestra123" \
  -H "Content-Type: multipart/form-data" \
  -F "query=How do neighborhood institutions affect youth civic participation?" \
  -F "taxonomy_seeds=civic_disengagement,social_capital" \
  -F "model_config=default" \
  -F "corpus_id=sociology" \
  -F "schema_pack_version=1.0.0"
```

## Notes
- Build/update the custom Kestra image when deps change: `make kestra-build`.
- `make kestra-install-deps` is kept as a compatibility alias to `make kestra-build`.
- The research session flow now triggers a real LiteLLM completion in `run_session.py` (non-dry mode).
- Ensure Ollama model bootstrap is done once: `./scripts/docker_compose.sh exec -T ollama ollama pull llama3.2:latest`.
- If Kestra runs on another host, update URLs and workspace path accordingly.
- Flows use the Kestra process task runner so commands execute inside the Kestra container with the mounted repo path.
