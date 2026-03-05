# Project State

**Date:** 2026-03-05
**Time:** 10:49 EST

## Project Goal
Build the OLS Sociology Agentic Research Stack (Phase A1 bring-up after Phase 0).

## Phase Status
- Phase 0: Complete.
- Phase A1: In progress, with durable Kestra runtime deps and real local LiteLLM completions validated.

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
- Kestra service now uses a custom image (`kestra/Dockerfile`) with `requirements.lock` preinstalled.
- `make kestra-build` target added; `make kestra-install-deps` retained as compatibility alias.
- `run_session.py` now performs a real LiteLLM completion call in non-dry mode and records the model output in `artifacts/summary.md`.
- Kestra flows remain on process runner + `python3`:
  - `kestra/flows/research_session.yaml`
  - `kestra/flows/corpus_ingest.yaml`

## Verified Green (This Session)
- Custom Kestra image built and running:
  - Service image: `sociology-agentic-stack/kestra:v1.3.0-py`
  - In-container imports verified: `sherpa_ai`, `langfuse`, `instructor`, `lancedb`
- Kestra API/auth/flow operations verified after recreate:
  - `make kestra-health`
  - `make kestra-import`
- Ollama reachability from LiteLLM container verified:
  - `OLLAMA_BASE_URL=http://ollama:11434`
  - `/api/tags` returns `200`
- Real LiteLLM completion checks succeeded:
  - `model=synthesis` returned non-empty content
  - `model=analysis` returned non-empty content
- Non-dry CLI path with real model call succeeded:
  - `python scripts/run_session.py --query ... --taxonomy-seeds ...`
  - Artifacts contain populated `## Model Insight (LiteLLM)` block
  - `artifacts/summary.metadata.json` shows `"model_used": "synthesis"`
- Non-dry Kestra path with real model call succeeded:
  - Triggered execution: `wmErqrj05WwdugeiV1fdb`
  - Final state: `SUCCESS`
  - `artifacts/summary.md` updated with Kestra query + model-generated insight
- Python tests still pass: `make test` -> `4 passed`

## Current Environment Facts
- OS: Ubuntu 24.04.4 LTS.
- Hardware: AMD 16-core CPU, 128GB RAM, RTX 3060 12GB.
- Docker context: `default` (`unix:///var/run/docker.sock`).
- In this shell, direct `docker` access still fails without refreshed group session; `scripts/docker_compose.sh` wrapper works.
- Kestra version in container: `1.3.0`.

## Known Issues / Remaining Work
- Direct `docker` group access in current login shell still needs a refreshed session (`sg docker` wrapper remains necessary).
- NVML (`nvidia-smi`) issue remains deferred.

## Next Steps (Strict Order)
1. Commit durable Kestra image milestone (`phase-a1/*`).
2. Commit LiteLLM+Ollama real completion milestone (`phase-a1/*`).
3. If desired, tune model aliases/prompts for tighter deterministic formatting from local models.
4. Continue toward Phase A1 done criteria and final cleanup commit.

## Safety Notes
- No destructive cleanup commands were run in this phase.
- Changes were incremental and verified with live commands.
