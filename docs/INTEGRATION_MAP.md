# Integration Map

This document defines interface contracts between stack components.

## 1) Kestra -> Session Runtime

- **Interface:** Shell command invocation (`python scripts/run_session.py ...`)
- **Inputs:** query, taxonomy_seeds, model_config, corpus_id, schema_pack_version
- **Output Contract:** Exit code `0/1`, artifacts written to `artifacts/`

## 2) Kestra -> Review Runtime

- **Interface:** Shell command invocation (`python scripts/run_review.py ...`)
- **Inputs:** artifacts directory, report directory
- **Output Contract:** Markdown + JSONL reports in `docs/review_reports/`

## 3) Session Runtime -> Schema Pack

- **Interface:** File-system loader (`schemas/pack_manifest.yaml`)
- **Inputs:** ontology file path, schema file list, template file list
- **Output Contract:** Strict validation pass before generation

## 4) Sherpa -> LiteLLM

- **Interface:** OpenAI-compatible HTTP API (`/v1/chat/completions`)
- **Inputs:** model alias, messages, generation parameters
- **Output Contract:** Provider-agnostic response payload for orchestration layer

## 5) Sherpa -> Retrieval Adapter

- **Interface:** Python adapter methods
- **Expected Methods:** `upsert_docs`, `query_topk`, `delete_corpus`, `list_sources`
- **Output Contract:** Structured source records with stable `source_id`

## 6) Sherpa -> Langfuse

- **Interface:** Langfuse SDK tracing
- **Trace Contract:** one trace per run, one span per state
- **Required Metadata:** run_id, agent_name, policy_name, state_name, corpus_id, git_commit_sha

## 7) Review Runtime -> Artifact Schemas

- **Interface:** JSONSchema validation
- **Inputs:** claims and glossary JSONL records
- **Output Contract:** findings with type/severity/artifact/record mapping

## 8) Archive Runtime -> Session Artifacts

- **Interface:** Filesystem snapshot + tar.gz compression
- **Inputs:** artifact directory
- **Output Contract:** timestamped archive directory + `archive_manifest.json`
