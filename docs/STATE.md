# Project State

**Date:** 2026-03-05
**Time:** 11:00 EST

## Project Goal
Build the OLS Sociology Agentic Research Stack (Phase A1 bring-up after Phase 0).

## Phase Status
- Phase 0: Complete.
- Phase A1: Complete. Stack is end-to-end validated and practically usable.

## What Is Implemented
- Schema pack, ontology, JSONSchemas, and templates under `schemas/`.
- State machines under `state_machines/`.
- CLI scripts: `run_session.py`, `run_review.py`, `run_sherpa_workflow.py`, prompt sync, schema validation, smoke.
- Langfuse tracing integration in `run_session.py` and `run_review.py`.
- Compose infra stack in `compose.yaml`:
  - Langfuse + Postgres + ClickHouse + Redis + Minio
  - LiteLLM
  - Ollama (in-stack)
  - Kestra + dedicated Postgres
- Kestra service uses a custom image (`kestra/Dockerfile`) with `requirements.lock` preinstalled.
- `make kestra-build` builds the image; `make kestra-install-deps` is a compatibility alias.
- LiteLLM routes `synthesis` and `analysis` aliases to in-stack Ollama (`llama3.2:latest`).
- `run_session.py` performs a real LiteLLM completion call and records model output in `artifacts/summary.md`.
- `make kestra-wait` target added to reliably wait for Kestra readiness after cold start.
- `docs/RUNBOOK.md` updated with golden path (section 0) and improved troubleshooting (section 12).

## Verified Green (Phase A1 Final)
- All services healthy after `make up`: kestra, kestra-postgres, langfuse-web, langfuse-worker, litellm, ollama, postgres, clickhouse, redis, minio.
- `make kestra-health` → both endpoints reachable.
- `make kestra-import` → research_session + corpus_ingest imported successfully.
- `make ingest SOURCE_DIR=data/corpus` → execution CREATED (execution: `TrW2DV7E89nua5oPDKFXE`).
- `make kestra-run QUERY=... SEEDS=...` → execution SUCCESS in ~7s (execution: `1lc4gPlgfW1sMHwV1uacwa`).
- `make session QUERY=... SEEDS=...` → real model call, artifacts populated, `summary.md` contains `## Model Insight (LiteLLM)`.
- `make test` → 4 passed.

## Current Environment Facts
- OS: Ubuntu 24.04.4 LTS.
- Hardware: AMD 16-core CPU, 128GB RAM, RTX 3060 12GB.
- Docker context: `default` (`unix:///var/run/docker.sock`).
- In this shell, direct `docker` access requires refreshed group session; `scripts/docker_compose.sh` wrapper works.
- Kestra version in container: `1.3.0`.
- Local model: `llama3.2:latest` pulled (2.0 GB).

## Known Issues / Gaps
- Direct `docker` group access in current login shell needs a refreshed session (`sg docker` wrapper works).
- NVML (`nvidia-smi`) issue deferred — does not affect CPU inference.
- No git remote configured; push to GitHub pending.

## One-Time Bootstrap Checklist (Fresh Machine)
1. `cp .env.example .env` (edit if needed)
2. `make setup`
3. `make up`
4. `make kestra-wait`
5. `make kestra-init-auth`
6. `./scripts/docker_compose.sh exec -T ollama ollama pull llama3.2:latest`
7. `make kestra-import`

See `docs/RUNBOOK.md` section 0 for the full golden path.

## Safety Notes
- No destructive cleanup commands were run in this phase.
- Changes were incremental and verified with live commands.
