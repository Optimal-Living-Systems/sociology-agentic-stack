# Project State

**Date:** 2026-03-05
**Time:** 02:02 EST

## Project Goal
Build the OLS Sociology Agentic Research Stack (Phase A1 bring-up after Phase 0).

## Phase Status
- Phase 0: Complete (scaffold, schemas, scripts, docs, Makefile).
- Phase A1: In progress (infra verification and bring-up pending).

## What Is Implemented
- Schema pack: `schemas/pack_manifest.yaml`, `schemas/ontology.yaml`, JSONSchemas under `schemas/artifact_schemas/`, templates under `schemas/templates/`.
- State machines: `state_machines/sociology_session.json`, `state_machines/review_session.json`.
- Kestra flows: `kestra/flows/research_session.yaml`, `kestra/flows/corpus_ingest.yaml`.
- LiteLLM router config: `integrations/litellm/config.yaml` and `integrations/config/router.yaml`.
- Langfuse adapter: `integrations/langfuse/tracing.py` with README.
- CLI scripts: `scripts/run_session.py`, `scripts/run_review.py`, `scripts/run_sherpa_workflow.py`, `scripts/sync_prompts_to_langfuse.py`, `scripts/validate_schema_pack.py`.
- Make targets: `make sherpa-run`, `make sync-prompts-apply`, plus base targets.

## Verified Green
- Git history shows Phase 0 + A1 prep commits (see `git log --oneline`).
- Schema pack parsing passes via `scripts/validate_schema_pack.py`.
- Langfuse tracing is wired into `run_session.py` and `run_review.py`.

## Current Environment Facts
- OS: Ubuntu 24.04.4 LTS.
- Hardware: AMD 16-core CPU, 128GB RAM, RTX 3060 12GB.
- Docker context: `default` (unix:///var/run/docker.sock).
- Docker socket permissions: `/var/run/docker.sock` is owned by `root:docker`.
- Current user `joel` is in the `docker` group, but `docker ps` returns permission denied in this session.
- Disk free: `/` has ~57G free, `/home` has ~11G free (94% used).

## Known Blockers / Issues
- Docker CLI permission denied to `/var/run/docker.sock`. User is in `docker` group but session not refreshed.
- NVML (nvidia-smi) still fails (driver issue), deferred unless needed.
- Disk headroom on `/home` below 25–30GB target.
- Infra services not yet brought up in this repo (no compose file committed here).
- Schema validation not yet enforced inside `scripts/run_sherpa_workflow.py` outputs.

## What “Phase A1 Done” Means
- Docker daemon accessible from shell without permission errors.
- Disk headroom >= 25–30GB on `/home` or documented safe cleanup path.
- Langfuse + LiteLLM reachable via compose or documented external services.
- Smoke tests pass (Langfuse reachable, LiteLLM basic completion, Kestra reachable if used).
- Sherpa runner validates outputs against JSONSchemas.
- `docs/STATE.md` reflects current status and git clean.

## Next Steps (Strict Order)
1. Fix Docker socket access: refresh group membership (`newgrp docker` or re-login). Verify `docker ps`.
2. Record Docker verification in this file and commit if status changes.
3. Disk readiness: run `df -h /` and `df -h /home`; if `/home` < 25–30GB free, propose safe cleanup.
4. Add compose file(s) for Langfuse + LiteLLM (and Kestra if needed) or document external services.
5. Add Make targets: `make up`, `make down`, `make logs` if compose is added.
6. Bring up infra and verify endpoints (Langfuse UI, LiteLLM /v1).
7. Update `docs/STATE.md` with infra status and commit.
8. Enforce JSONSchema validation in `scripts/run_sherpa_workflow.py` before writing artifacts.
9. Add tests in `tests/` for schema validation pass/fail.
10. Add `make test` target and run it.

## Safety Notes
- No destructive commands.
- Keep changes small and commit frequently.
- Verify with commands before assuming state.
