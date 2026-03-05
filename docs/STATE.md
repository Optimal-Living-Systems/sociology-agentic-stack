# Project State

**Date:** 2026-03-05
**Time:** 03:41 EST

## Project Goal
Build the OLS Sociology Agentic Research Stack (Phase A1 bring-up after Phase 0).

## Phase Status
- Phase 0: Complete.
- Phase A1: In progress, with Kestra now integrated and validated in-stack.

## What Is Implemented
- Schema pack, ontology, JSONSchemas, and templates under `schemas/`.
- State machines under `state_machines/`.
- CLI scripts: `run_session.py`, `run_review.py`, `run_sherpa_workflow.py`, prompt sync, schema validation, smoke.
- Sherpa workflow schema validation now enforced before artifact writes.
- Langfuse tracing integration in `run_session.py` and `run_review.py`.
- Compose infra stack in `compose.yaml`:
  - Langfuse + Postgres + ClickHouse + Redis + Minio
  - LiteLLM
  - Kestra + dedicated Postgres
- Docker wrapper script `scripts/docker_compose.sh` with `sg docker` and no-creds fallback support.
- Make targets for infra + Kestra operations:
  - `make up/down/logs/test`
  - `make kestra-init-auth`
  - `make kestra-install-deps`
  - `make kestra-health`
  - `make kestra-import`
  - `make kestra-run`
  - `make ingest`
- Kestra flows updated to use process runner + `python3`:
  - `kestra/flows/research_session.yaml`
  - `kestra/flows/corpus_ingest.yaml`

## Verified Green (This Session)
- Disk readiness:
  - `/` free: ~47G
  - `/home` free: ~76G
- Docker stack is running; Kestra is healthy.
- Kestra config endpoint reports `isBasicAuthInitialized: true`.
- Kestra API pathing corrected to `/api/v1/main/*` for flow import/execution.
- End-to-end Kestra target sequence succeeds:
  - `make kestra-init-auth`
  - `make kestra-health`
  - `make kestra-install-deps`
  - `make kestra-import`
  - `make ingest SOURCE_DIR=data/corpus`
  - `make kestra-run QUERY=... SEEDS=...`
- Latest verification executions completed `SUCCESS`:
  - `363OcefWdA3ZSHLOAvaL8s` (corpus-ingest)
  - `2uT12D5dVYomm8VqBDCBzV` (sociology-research-session)
- Python test suite passes: `make test` -> `4 passed`.
- Langfuse health endpoint returns `200`.

## Current Environment Facts
- OS: Ubuntu 24.04.4 LTS.
- Hardware: AMD 16-core CPU, 128GB RAM, RTX 3060 12GB.
- Docker context: `default` (`unix:///var/run/docker.sock`).
- In this shell, direct `docker` access still fails without refreshed group session; `sg docker`/wrapper works.
- Kestra version in container: `1.3.0`.

## Known Issues / Remaining Work
- LiteLLM is reachable, but provider routes are not currently usable without real upstream credentials/connectivity:
  - `synthesis/analysis` need valid `OPENAI_API_KEY`.
  - local Ollama routes are currently unreachable from container (`host.docker.internal` resolution/connectivity issue in this environment).
- `make kestra-install-deps` installs into the running Kestra container; it must be re-run if Kestra container is recreated.
  - Recommended follow-up: build a custom Kestra image with Python deps baked in (or startup bootstrap script).
- NVML (`nvidia-smi`) issue remains deferred.

## What “Phase A1 Done” Means
- Docker access in active login shell is clean (no `sg docker` fallback needed).
- Langfuse + LiteLLM + Kestra are up and reachable.
- Kestra flows import and execute successfully (now true).
- LiteLLM real completion test passes using configured provider keys or local model backend.
- Sherpa schema validation and tests remain green.
- `docs/STATE.md` reflects final state and worktree is clean after commit.

## Next Steps (Strict Order)
1. Commit current Kestra integration milestone.
2. Decide and implement durable Kestra Python dependency strategy (custom image preferred).
3. Configure real provider key(s) and/or fix Ollama host reachability for LiteLLM.
4. Run non-dry real session path via CLI and via Kestra, then capture outputs in docs.
5. Update `docs/STATE.md` again after those runtime validations.

## Safety Notes
- No destructive cleanup commands were run in this phase.
- Changes were incremental and verified with live commands.
