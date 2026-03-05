# Architectural Decision Records (ADRs)

## ADR-001: Use Kestra for Outer Orchestration

- **Status:** Accepted
- **Decision:** Kestra manages trigger/schedule/archive orchestration; Sherpa manages in-session reasoning.
- **Rationale:** Separates infra concerns from agent policy logic; aligns with existing OLS infrastructure.
- **Consequences:** Requires stable CLI contracts between Kestra tasks and local scripts.

## ADR-002: Use Sherpa-Based Review Agent (Review-Only)

- **Status:** Accepted
- **Decision:** Review workflows are implemented as agentic audits but constrained to read-only outputs.
- **Rationale:** Reuses shared ontology/schema context while preserving safety.
- **Consequences:** Review pipeline must never execute write-back or auto-fix operations on artifacts.

## ADR-003: LanceDB as Default Local Vector Store

- **Status:** Accepted
- **Decision:** LanceDB is default local retrieval backend.
- **Rationale:** Embedded local operation, performant analytics format, clean Python integration path.
- **Consequences:** Maintain adapter boundary for fallback swap to Chroma if required.

## ADR-004: Instructor for Structured Generation Contracts

- **Status:** Accepted
- **Decision:** Use structured generation tooling (Instructor) to enforce JSON outputs against schemas.
- **Rationale:** Reduces malformed records and improves deterministic parsing in downstream checks.
- **Consequences:** Must maintain version compatibility with chosen model providers and SDK layers.

## ADR-005: LiteLLM as Unified Router Layer

- **Status:** Accepted
- **Decision:** Route all model calls through a single OpenAI-compatible endpoint.
- **Rationale:** Unifies API + local model invocation and decouples workflows from provider SDK drift.
- **Consequences:** Requires strong environment and key management discipline.

## ADR-006: Dual Prompt Governance (Git + Langfuse)

- **Status:** Accepted
- **Decision:** Prompts live in source-controlled templates and are synchronized to Langfuse prompt management.
- **Rationale:** Enables reproducibility in git and operational observability/versioning in Langfuse.
- **Consequences:** Sync tooling must track versions and avoid accidental overwrites.

## ADR-007: DVC for Artifact/Corpus Versioning

- **Status:** Accepted
- **Decision:** Use DVC for larger artifact and corpus data lineage.
- **Rationale:** Keeps git history lightweight while preserving reproducibility and provenance.
- **Consequences:** Team needs documented remote storage setup and DVC workflow training.
