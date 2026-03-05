# Project State

**Date:** 2026-03-05
**Time:** 02:25 EST

## Project Goal
Build the OLS Sociology Agentic Research Stack (Phase A1 bring-up after Phase 0).

## Phase Status
- Phase 0: Complete (scaffold, schemas, scripts, docs, Makefile).
- Phase A1: In progress (core bring-up complete; disk headroom + session group refresh still open).

## What Is Implemented
- Schema pack: `schemas/pack_manifest.yaml`, `schemas/ontology.yaml`, JSONSchemas under `schemas/artifact_schemas/`, templates under `schemas/templates/`.
- State machines: `state_machines/sociology_session.json`, `state_machines/review_session.json`.
- Kestra flows: `kestra/flows/research_session.yaml`, `kestra/flows/corpus_ingest.yaml`.
- LiteLLM router config: `integrations/litellm/config.yaml` and `integrations/config/router.yaml`.
- Langfuse adapter: `integrations/langfuse/tracing.py` with README.
- CLI scripts: `scripts/run_session.py`, `scripts/run_review.py`, `scripts/run_sherpa_workflow.py`, `scripts/sync_prompts_to_langfuse.py`, `scripts/validate_schema_pack.py`.
- Compose infra file: `compose.yaml` (Langfuse + dependencies + LiteLLM).
- Docker wrapper script: `scripts/docker_compose.sh` (falls back to `sg docker` and local no-creds Docker config when needed).
- Make targets: `make up`, `make down`, `make logs`, `make test`, plus existing targets.

## Verified Green
- Git history shows Phase 0 + A1 prep commits (see `git log --oneline`).
- Schema pack parsing passes via `scripts/validate_schema_pack.py`.
- Langfuse tracing is wired into `run_session.py` and `run_review.py`.
- Infra compose stack starts successfully via `make up`.
- Endpoint smoke checks:
  - `http://localhost:3000/api/public/health` returns `200` (Langfuse).
  - `http://localhost:4000/health` returns `200` with LiteLLM auth header.
  - LiteLLM mock completion returns `200` with response content `pong`.
- Docker daemon access verified in refreshed shell context via `newgrp docker` (`docker ps`, `docker info` both succeed).
- Sherpa workflow now validates `claims.jsonl`, `glossary.jsonl`, and `summary_metadata.json` against JSONSchemas before artifact writes.
- Tests added under `tests/test_sherpa_schema_validation.py`; `make test` passes (`4 passed`).

## Current Environment Facts
- OS: Ubuntu 24.04.4 LTS.
- Hardware: AMD 16-core CPU, 128GB RAM, RTX 3060 12GB.
- Docker context: `default` (unix:///var/run/docker.sock).
- Docker socket permissions: `/var/run/docker.sock` is owned by `root:docker`.
- Current shell groups still do not include `docker`; direct `docker ps` fails unless using refreshed login/session.
- In `newgrp docker` context, docker group is active and daemon access works.
- `scripts/docker_compose.sh` successfully runs docker commands via `sg docker` fallback.
- Disk free: `/` has ~51G free, `/home` has ~11G free (94% used).

## Known Blockers / Issues
- Docker CLI permission denied in current shell without `newgrp docker`/re-login (mitigated by wrapper script fallback).
- NVML (nvidia-smi) still fails (driver issue), deferred unless needed.
- Disk headroom on `/home` below 25–30GB target.
- Kestra endpoint is not reachable at `http://localhost:8080` (optional unless ingest flow is required now).

## Disk Cleanup Candidates (Not Executed)
- `/home/joel/.lmstudio` (~82G)
- `/home/joel/.docker` (~20G)
- `/home/joel/.local` (~15G)
- `/home/joel/llm` (~5.6G)
- `/home/joel/.cache` (~4.6G)

## Safe Cleanup Suggestions (No Action Taken Yet)
1. Remove unused Docker artifacts: `docker system df` then targeted `docker image prune` / `docker builder prune`.
2. Trim model caches not actively used (`.lmstudio`, `llm`, `.ollama`) after confirming active projects.
3. Clear package/tool caches (`~/.cache`, `~/.npm`) where safe.

## What “Phase A1 Done” Means
- Docker daemon accessible from shell without permission errors.
- Disk headroom >= 25–30GB on `/home` or documented safe cleanup path.
- Langfuse + LiteLLM reachable via compose or documented external services.
- Smoke tests pass (Langfuse reachable, LiteLLM basic completion, Kestra reachable if used).
- Sherpa runner validates outputs against JSONSchemas.
- `docs/STATE.md` reflects current status and git clean.

## Next Steps (Strict Order)
1. Refresh shell group membership (`newgrp docker` or re-login) so direct `docker` commands work without fallback.
2. Free `/home` space to reach at least 25–30GB headroom, then re-run `df -h /home`.
3. Decide whether to bring Kestra into compose or keep it as an external dependency and document that choice.
4. Run end-to-end workflow smoke with real provider keys (non-mock LiteLLM completion + Sherpa run).
5. Keep `docs/STATE.md` current after each material infra/runtime change.

## Safety Notes
- No destructive commands.
- Keep changes small and commit frequently.
- Verify with commands before assuming state.
