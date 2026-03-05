# Kestra Flow Integration

This folder contains Kestra flows for orchestrating the OLS sociology stack.

## Files
- `flows/research_session.yaml`: End-to-end run (session -> review -> archive)
- `flows/corpus_ingest.yaml`: Corpus ingestion trigger scaffold

## Prerequisites
- Kestra server running (Docker is acceptable)
- Kestra API reachable (default `http://localhost:8080`)
- Local repo path exists at `/home/joel/work/sociology-agentic-stack`

## Install flows into Kestra

```bash
# Import research session flow
curl -sS -X POST "http://localhost:8080/api/v1/flows/import" \
  -H "Content-Type: multipart/form-data" \
  -F "fileUpload=@kestra/flows/research_session.yaml"

# Import corpus ingest flow
curl -sS -X POST "http://localhost:8080/api/v1/flows/import" \
  -H "Content-Type: multipart/form-data" \
  -F "fileUpload=@kestra/flows/corpus_ingest.yaml"
```

## Trigger a run from CLI

```bash
curl -sS -X POST "http://localhost:8080/api/v1/executions/ols.research/sociology-research-session" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do neighborhood institutions affect youth civic participation?",
    "taxonomy_seeds": "civic_disengagement,social_capital",
    "model_config": "default",
    "corpus_id": "sociology",
    "schema_pack_version": "1.0.0"
  }'
```

## Notes
- These flows assume local virtualenv and scripts are already available.
- If Kestra runs on another host, update URLs and workspace path accordingly.
