# User Manual: OLS Sociology Agentic Research Stack

## 1) What This Stack Is

The OLS Sociology Agentic Research Stack is a local-first research runtime that combines:

- Orchestration: Kestra
- Model gateway: LiteLLM (OpenAI-compatible API)
- Local model runtime: Ollama
- Observability: Langfuse
- Research runners: Python CLIs in `scripts/`
- Schema and template pack: `schemas/`

The current runtime is production-shaped but still partially scaffolded in research logic. It is fully usable for:

- Running reproducible session workflows from CLI and Kestra
- Routing model calls through LiteLLM
- Recording traces/spans in Langfuse
- Generating and auditing artifacts in `artifacts/`

## 2) Core Concepts

### Session run
A session run executes the state path:

`INTAKE -> RETRIEVE_LOCAL -> RETRIEVE_WEB -> SYNTHESIZE -> CRITIQUE -> FINALIZE`

The current implementation performs one real model completion during `SYNTHESIZE`, then writes deterministic scaffold artifacts.

### Artifacts
A successful run writes:

- `artifacts/summary.md`
- `artifacts/claims.jsonl`
- `artifacts/glossary.jsonl`
- `artifacts/critique.md`
- `artifacts/summary.metadata.json`

### Two operation modes

- Host CLI mode: run `make session`, `make review`, `python scripts/*.py` on the host.
- Kestra mode: run workflows via Kestra API/UI (`make kestra-run`, `make ingest`).

## 3) Prerequisites

- Ubuntu 24.04+ (or compatible Linux host)
- Python 3.12+
- Docker + Docker Compose
- Git
- Network access for provider APIs (if using OpenAI/Anthropic/Mistral)

## 4) Initial Setup

```bash
cd /home/joel/work/sociology-agentic-stack
cp .env.example .env
make setup
```

Then start infra:

```bash
make up
make kestra-wait
make kestra-init-auth
```

Pull local model once:

```bash
./scripts/docker_compose.sh exec -T ollama ollama pull llama3.2:latest
```

Import Kestra flows:

```bash
make kestra-import
```

## 5) Environment Configuration

Edit `.env` carefully. Most failures come from bad env values.

### Required keys/values

- `LITELLM_MASTER_KEY`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_ENCRYPTION_KEY` must be exactly 64 hex chars

Generate a valid encryption key:

```bash
openssl rand -hex 32
```

### Recommended local behavior

For this stack layout, prefer **not overriding** these unless you have a specific reason:

- `LANGFUSE_HOST`
- `OLLAMA_BASE_URL`

Reason:

- Host CLI defaults are correct for host execution (`localhost` where needed).
- Container defaults in `compose.yaml` are correct for in-network resolution (`langfuse-web`, `ollama`).
- Wrong overrides (especially `localhost` inside container context) can break LiteLLM/Kestra.

If you do set them explicitly, use values that match where the caller runs.

## 6) Daily Workflow (Golden Path)

### Start stack

```bash
make up
make kestra-wait
make kestra-health
```

### Run CLI session

```bash
make session QUERY="How does housing precarity influence civic participation?" \
  SEEDS="housing_precarity,civic_disengagement"
```

### Run review

```bash
make review
```

### Run Kestra session

```bash
make kestra-run QUERY="How does housing precarity influence civic participation?" \
  SEEDS="housing_precarity,civic_disengagement"
```

### Run Kestra ingest

```bash
make ingest SOURCE_DIR=data/corpus
```

### Run tests

```bash
make test
```

## 7) Make Targets You Will Use Most

### Infra

- `make up`
- `make down`
- `make logs SERVICE=<service>`

### Kestra

- `make kestra-wait`
- `make kestra-health`
- `make kestra-init-auth`
- `make kestra-import`
- `make kestra-run QUERY="..." SEEDS="..."`
- `make ingest SOURCE_DIR=data/corpus`
- `make kestra-logs`
- `make kestra-build` (rebuild custom Kestra image with baked Python deps)

### Session + review

- `make session QUERY="..." SEEDS="..."`
- `make dry-run QUERY="..." SEEDS="..."`
- `make review`
- `make sherpa-run QUERY="..." SEEDS="..."` (scaffold Sherpa workflow path)

### Validation/maintenance

- `make validate-schemas`
- `make sync-prompts`
- `make sync-prompts-apply`
- `make test`
- `make clean`

## 8) Langfuse Usage

### Access UI

- URL: `http://localhost:3000`

### Create keys

1. Log in to Langfuse UI
2. Create/open project
3. Generate API keys
4. Put keys in `.env`

### Verify health

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://localhost:3000/api/public/health
```

Expected: `200`

## 9) LiteLLM + Model Routing

### Endpoint

- `http://localhost:4000/v1`

### Quick test

```bash
curl -fsS http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"synthesis","messages":[{"role":"user","content":"Reply exactly: ok"}]}'
```

### Aliases

Defined in `integrations/litellm/config.yaml`, including:

- `synthesis`
- `analysis`
- `claude_synthesis`
- `mistral_synthesis`
- local aliases via Ollama

If an alias fails with model-not-found, update the upstream model ID in `integrations/litellm/config.yaml` and restart LiteLLM.

## 10) Kestra Usage

### Access

- UI/API: `http://localhost:8080`
- default local auth: `admin@kestra.io` / `Kestra123`

### Flow IDs

- `ols.research/sociology-research-session`
- `ols.research/corpus-ingest`

### Import after flow edits

```bash
make kestra-import
```

## 11) Files and Responsibilities

- `compose.yaml`: local infra topology
- `Makefile`: operator command surface
- `kestra/flows/*.yaml`: orchestration flows
- `scripts/run_session.py`: primary session runner (includes one real model call)
- `scripts/run_review.py`: read-only artifact audit
- `scripts/run_sherpa_workflow.py`: schema-validated Sherpa workflow scaffold
- `schemas/`: ontology, prompt templates, JSON schemas
- `integrations/litellm/config.yaml`: model aliases and provider mapping
- `integrations/langfuse/tracing.py`: tracing wrapper

## 12) Troubleshooting

### A) Langfuse health is 500

Usually invalid `LANGFUSE_ENCRYPTION_KEY` length/format.

Fix:

1. Set valid 64-char hex key in `.env`
2. `make up`

### B) LiteLLM 500 with `Cannot connect to host localhost:11434`

Cause: wrong `OLLAMA_BASE_URL` inside container context.

Fix options:

- Remove `OLLAMA_BASE_URL` from `.env` and rely on compose default
- Or set to `http://ollama:11434` for container-driven paths

Then restart:

```bash
make up
```

### C) Kestra auth failures (401)

```bash
make kestra-init-auth
make kestra-health
```

### D) Kestra not ready right after startup

```bash
make kestra-wait
```

### E) Docker permission issues

Use the wrapper-backed make targets. If needed, refresh docker group session (`newgrp docker` or relogin).

### F) Langfuse export returns 401 from runners

Re-check exact `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in `.env` for typos.

### G) Provider model errors (404/invalid model)

Model name in `integrations/litellm/config.yaml` is invalid for your account/provider version.
Update model IDs and restart LiteLLM.

## 13) Operational Checklists

### Pre-run checklist

- `make up` succeeds
- `make kestra-health` succeeds
- Langfuse health endpoint is `200`
- LiteLLM test call to `synthesis` returns `200`

### Post-run checklist

- `artifacts/summary.md` updated
- `artifacts/summary.metadata.json` includes expected query and model
- Kestra execution state is `SUCCESS` (if using Kestra path)
- `make test` still passes

## 14) Security and Secrets

- Never commit `.env`
- Never paste secrets into docs/issues
- Rotate API keys if accidentally exposed
- Keep `.env.example` placeholders only

## 15) Suggested Learning Path

1. Run golden path once from start to finish.
2. Read generated artifacts and map each to its producing script.
3. Trigger same run via Kestra and compare behavior.
4. Modify one model alias in LiteLLM config and validate effect.
5. Run `make review` and inspect findings output format.
6. Read `docs/ARCHITECTURE.md` and `docs/INTEGRATION_MAP.md` once the commands feel familiar.
