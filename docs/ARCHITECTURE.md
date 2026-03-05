# Architecture

## Purpose

This architecture separates infrastructure orchestration from agent reasoning.
Kestra handles outer workflow scheduling and execution, while Sherpa handles
state-machine-based research logic.

## Component Diagram

```text
+-------------------+       +-------------------------+
| User / Operator   | ----> | Kestra (Flow Runner)    |
| (CLI / API)       |       | ols.research namespace  |
+-------------------+       +-----------+-------------+
                                        |
                                        v
                             +----------+-----------+
                             | Sherpa Session Engine |
                             | state_machines/*.json |
                             +----+------------+-----+
                                  |            |
                                  |            +-------------------------+
                                  v                                      |
                    +-------------+-------------+            +-----------+-----------+
                    | LiteLLM Proxy (Router)    |            | Langfuse (Tracing +   |
                    | OpenAI-compatible endpoint |            | Prompt Mgmt + Metrics)|
                    +-------------+-------------+            +-----------+-----------+
                                  |
                                  v
                    +-------------+-------------+
                    | Model Providers            |
                    | API: OpenAI/Anthropic/... |
                    | Local: Ollama/Qwen/Mistral|
                    +-------------+-------------+
                                  |
                                  v
                    +-------------+-------------+
                    | LanceDB (Local Retrieval) |
                    | + corpus/data embeddings  |
                    +---------------------------+
```

## Data Flow

1. Kestra receives inputs and triggers `scripts/run_session.py`.
2. Sherpa state machine controls session steps from `INTAKE` to `FINALIZE`.
3. Retrieval and synthesis calls are routed through LiteLLM.
4. Session events, spans, prompts, and outcomes are traced to Langfuse.
5. Artifacts are written to `artifacts/` and then audited by review workflow.
6. Archive script snapshots outputs into `data/archives/`.

## Interface Boundaries

- **Kestra -> Session Runner:** CLI contract with typed inputs.
- **Session Runner -> Schema Pack:** Runtime loader of ontology/templates/schemas.
- **Sherpa -> LiteLLM:** OpenAI-compatible `base_url + api_key` interface.
- **Sherpa -> LanceDB:** Adapter contract (`upsert`, `query_topk`, `list_sources`).
- **Sherpa -> Langfuse:** Trace-per-run with span-per-state metadata.
- **Review Runner -> Artifacts:** Strict read-only analysis and report generation.

## Phase Notes

- [TODO][Phase B1] Replace state-machine draft format with verified Sherpa JSON format after course validation.
- [TODO][Phase B2] Implement production retrieval/web acquisition actions.
- [TODO][Phase B3] Add router fallback policies and latency/cost budgets.
