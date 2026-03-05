# Acceptance Tests

Use this checklist as pass/fail gates by phase.

## Phase 0: Foundations

- [ ] Host validation report exists at `docs/HOST_VALIDATION.md` with real command outputs
- [ ] Required directory tree exists (integrations/schemas/state_machines/kestra/scripts/docs/etc.)
- [ ] `.env.example` contains all required variables with placeholders only
- [ ] All YAML/JSON files parse successfully
- [ ] `make help` works and lists expected targets
- [ ] `make validate-schemas` returns success

## Phase A1: Core Runtime Bring-Up

- [ ] Sherpa import passes (`import sherpa_ai`)
- [ ] Langfuse SDK import passes (`import langfuse`)
- [ ] LiteLLM import passes (`import litellm`)
- [ ] LanceDB import passes (`import lancedb`)
- [ ] `make smoke` completes without error

## Phase A2: Workflow Execution

- [ ] `INTAKE -> RETRIEVE_LOCAL -> RETRIEVE_WEB -> SYNTHESIZE -> CRITIQUE -> FINALIZE` path executes
- [ ] Artifacts generated: `summary.md`, `claims.jsonl`, `glossary.jsonl`, `critique.md`
- [ ] Claims and glossary records validate against JSON schemas
- [ ] Summary metadata includes run ID, schema version, model, timestamp

## Phase A3: Observability + Prompt Lifecycle

- [ ] Langfuse is reachable locally
- [ ] 1 trace per session run is recorded
- [ ] 1 span per workflow state is recorded
- [ ] Required metadata keys are present on spans
- [ ] Local templates are synchronized to Langfuse prompt management

## Phase A4: Retrieval + Model Routing

- [ ] LanceDB retrieval works for local corpus queries
- [ ] LiteLLM endpoint supports OpenAI-compatible calls
- [ ] At least one API model route works (OpenAI/Anthropic/Mistral)
- [ ] At least one local model route works (Qwen/Mistral via Ollama)
- [ ] Routing config can be changed without code edits

## Phase A5: Review Layer

- [ ] Review runs in strict review-only mode (no auto-fix)
- [ ] Citation integrity task identifies unsupported or uncited claims
- [ ] Schema/duplication task detects schema violations and duplicates
- [ ] Reports are written to `docs/review_reports/`

## Phase A6: Hardening + Public Release

- [ ] Reproducible setup from fresh machine via `docs/RUNBOOK.md`
- [ ] No secrets committed in git history
- [ ] ADR set complete and current
- [ ] Security baseline documented and enforced
- [ ] CI placeholders replaced with real checks [TODO][Phase C1]
